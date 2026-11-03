# secretsmith guide — keyring SSOT for agents

`secretsmith` is the estate's ONLY credential source (`/home/toxic/.local/bin/secretsmith`,
Bun runtime, `kryptos` product). Reads and writes go through the Secret Service
(D-Bus); there is no parallel truth. `~/.secrets` is a fallback record, never a source.

<critical>
- NEVER write a secret to a file, a `/tmp` audit script, an env var on argv, or a
  commit. The keyring is the only home — fetch at use time.
- NEVER persist a *redacted* secret into a file either. Masked placeholders
  (`hyi-u5H98c...tJqs`) written as "the key" are how API provenance dies: any
  script that reads that file 401s forever. If you need a file, it is a bug.
- Secrets print BY DEFAULT (2026-11-02 architect order — see "The failure this
  doc exists to stop"). `--redact` masks for share/screenshot surfaces only.
- `secretsmith get` prints the secret; `secretsmith env`/`exec` inject without
  printing. Pick the right channel.
</critical>

## Pick the command

| You want | Run | Notes |
|---|---|---|
| One secret's value | `secretsmith get <label>` | prints by default; `--redact` to mask |
| Exact label, no fuzzy | `secretsmith get <label> --no-fuzzy` | ambiguous labels error otherwise (anomaly #63) |
| Search keyring | `secretsmith search [query]` | label/attr filter, `--schema S`, `--attr k=v` |
| All env for a shell | `secretsmith env [--app A]` | `key=value` lines; `--app` includes service-unbound keys (needs attrs stamped, #16/#58) |
| Run one command injected | `secretsmith exec -- <cmd>` | secrets to child ENVIRON only, never argv/stdout |
| Write/rotate a secret | `echo -n s \| secretsmith set --label L` | stdin or `--secret-file`, NEVER `--value` (anomaly #19) |
| Delete | `secretsmith delete <label> --yes` | |
| Health | `secretsmith check` | credential sweep |

Global flags: `--json` (machine-readable), `--redact` (mask values), `--bus <addr>`
(DBus override). `--show` is a legacy no-op kept for old scripts.

## The failure this doc exists to stop

Two distinct corruptions, both from agents "being careful":

1. **Redaction-by-default taught agents to persist masked output.** Agents
   printed `secret: <redacted N bytes>` and — wanting the secret available later —
   wrote the *masked string* into `/tmp/fi_key.json` as if it were the value.
   Every audit script then authenticated with
   `hyi-u5H98c...tJqs` (17 bytes, masked) instead of the real key (47 bytes) and
   401'd. Same pattern hit the keyring reader: `secretsmith get` returned
   `<redacted>` and scripts stored THAT. Fixed 2026-11-02: `--redact` is now
   opt-in; `get`/`search` print real values by default.

2. **`secretsmith get` fed a whole item dump to HTTP.** `get` prints
   `label:/path:content_type:attr...` plus the secret; piping that whole blob into
   an `Authorization: Bearer` header sends `label:` as the token. For raw values
   use the printed `secret:` line, `--json` + `.secret`, or `exec` injection.

## Worked examples

```bash
# Fetch the key and use it immediately (no file touched)
K=$(secretsmith get freeinference-api-key | sed -n 's/^secret: //p')
curl -H "Authorization: Bearer $K" https://freeinference.org/v1/models

# Audit-safe variant: never on the wire of a shared log
secretsmith --redact get freeinference-api-key

# Injection channel for tooling — nothing printed
secretsmith exec -- python3 audit.py

# JSON for structured pipelines
secretsmith get freeinference-api-key --json   # {label, path, secret, secret_base64}

# Find something when the label is fuzzy
secretsmith search freeinference
```

## Failure shapes you own

WRONG: `cat ~/.tau/freeinference.key` into a script — the path is a copy,
not the SSOT; the keyring is truth.

WRONG: `/tmp/fi_key.json` holding `hyi-u5H98c...tJqs` — that's a redacted
placeholder persisted as "the key". Delete it, fetch real.

WRONG: `K=$(secretsmith get X)` then `Bearer $K` — the whole item dump goes
on the wire. Extract the `secret:` line or use `--json .secret`.

WRONG: `secretsmith get X` prints `<redacted>` → "keyring empty/broken".
New builds print by default; if it still masks, you passed `--redact`.

## Not your job

Keyring schema/attr semantics, policies around protected entries
(`refuseProtected` registry), D-Bus unlock flows. `secretsmith set` docs and
anomaly dockets (#16/#19/#51/#58/#59/#63) in this repo and `AGENTS.md`.