# Classification rules

Every rule in `bin/tmp-classify.py`, its rationale, and its blind spots.
Rules are checked in this order; first match wins. **Secrets are checked
before everything else** so a secret-shaped file can never be misclassified
as disposable.

## 1. Type-based rules (before names)

| Rule | Class | Rationale |
|---|---|---|
| unix socket | IN_USE | live IPC endpoint; deleting breaks the peer |
| fifo | IN_USE | live pipe; same |
| name in {`.ICE-unix`, `.X11-unix`, `.XIM-unix`, `.font-unix`, `tmux-0`} | IN_USE | desktop/session runtime state |
| directory | UNKNOWN | never auto-delete a tree; inspect contents |
| non-regular special file | UNKNOWN | device nodes etc. — human call |
| size 0 | DISPOSABLE | empty file; nothing to lose |

## 2. Name rules (first match wins)

### Secrets — checked first

| Pattern | Reason |
|---|---|
| `\.(tok\|pem\|key\|p12\|pfx\|jks\|kdbx)$` | token/keystore material |
| `(^|[/_.~-])(id_rsa\|id_ed25519\|id_ecdsa)(\.\|$)`, `netrc`, `secret\|credential\|passwd\|shadow`, `\.env(\.\|$)`, `.secrets.bak-*` | credential-shaped names |

### In-use

| Pattern | Reason |
|---|---|
| `^tmux-` | tmux server socket dir |

### Transfer fragments (DISPOSABLE)

| Pattern | Reason |
|---|---|
| `\.b64$`, `\.b64chunks$`, `\.chunk\.[a-z0-9]+$`, `(^|-)chunk-[a-z0-9]+$`, `\.part$` | base64/chunked payloads shuttled between boxes |
| `\.hm$` | empty hash-lock markers from herd tooling |

Blind spot: a `.b64` that is someone's *archived* payload, not a fragment.
The chunk-reassembly check (§4) mitigates; when in doubt, decode a head.

### Caches (DISPOSABLE)

`node-compile-cache`, `__pycache__`, `^bunx-`, `^hsperfdata_` — regenerable
build/runtime caches.

### Locks / pids (DISPOSABLE)

`\.(pid|lock|lck)$`, `(^|/)fslock$`. Blind spot: a pid file for a *live*
daemon. Mitigate with `fuser` before deleting, and never delete pid files
under a service dir you don't own.

### Tool dumps (DISPOSABLE — regenerable)

`jarvis-tool-output-*`, `-baseline.(json|yaml|yml)`, `mat-debug-*.log`,
fleet/log scrapes (`fleet.(txt|log)`, `leads.txt`).

## 3. Content rules (first 64 KB of regular files)

| Pattern | Class | Reason |
|---|---|---|
| credential-shaped assignment (`api_key=...`, `bearer ...`, `client_secret=...` with 20+ char values) | SECRET | keys embedded in dumps/backups |
| `-----BEGIN ... PRIVATE KEY-----` | SECRET | key material |
| `printf '%s' '<200+ b64 chars>' … base64 -d` | DISPOSABLE | chunked base64 transfer job script |
| `/tmp/xfer.b64` referenced | DISPOSABLE | xfer transfer job script |
| >97% base64 alphabet over a 100+ char body | DISPOSABLE | transfer fragment without the extension |
| >70% of lines look like `<number> <name>` | DISPOSABLE | regenerable inventory dump |
| >30% of lines look like `[seq] author @ date` scrapes | DISPOSABLE | regenerable channel/log scrape |
| name ends `.py`/`.sh` + name hints `xfer\|mr-patch\|chunk` + body mentions `base64`/`xfer` | DISPOSABLE | one-off transfer job script |
| shebang or `.(py|sh|go|rs|ts|js|toml|yaml|yml|md)` | MEANINGFUL | script/doc/config/source — needs a repo home |
| body starts with `{` or `[` | MEANINGFUL | structured data — check provenance before integrating |

Blind spots: content rules only read the first 64 KB; a secret buried
deeper is missed (name rules still catch most). Minified JS bundles can trip
the base64 rule — check the extension first (`.js` → MEANINGFUL by name).

## 4. Chunk reassembly

`find_reassembled()`: groups candidate chunk files by common prefix,
concatenates, base64-decodes, and compares the md5 against every other file
in the root. On a byte-identical match the report annotates the chunks with
`reassembles byte-identical to <original>` — those chunks are safe to delete
with full confidence. Proven in the field: `ch1+ch2+ch3` decoded
byte-identical to `daemon-audit.py`.

## 5. Deletion guards

- Dry run is the default; deletion is opt-in (`--delete-disposable`).
- SECRET / IN_USE / UNKNOWN are never deleted by the tool.
- `--min-age-min` (default 30): never delete anything younger. Protects
  files created by still-running jobs.
- Directories are never deleted except when explicitly classified
  DISPOSABLE by a name rule (e.g. `fslock`); UNKNOWN dirs are always kept.
- Exit code 2 when secrets were found, so pipelines can gate on it.