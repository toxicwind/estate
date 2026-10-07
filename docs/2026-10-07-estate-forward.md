# Estate forward plan — 2026-10-07

**Workflow:** no PRs. Commit and push straight to `main` on each repo (force when rewriting history is intentional).  
**Constraint:** never edit only the live path; never touch `/home/toxic` from the Grok Bot VM — host scripts run on `toxic@awrawr-pc`.

This consolidates Spark’s Funnel + hardcore-cleanup brief with the Grok Bot hybrid layout + **arroyo** bot-plane decision.

---

## 0. What’s true vs Spark fiction

| Keep from Spark | Reject / correct |
|---|---|
| Funnel root cause: CLI parsed `on` as target → tailnet-only | Wrong ports in Spark READMEs (`herd :25104`, flock as sole cloud door) |
| Archive-then-purge scratch / tack | Aggressive `.gitmodules` wipe to one github/gitignore entry |
| Roost sole provider authority; delete `ranch/tack/` | Four-pillar “toxicwind/herd” as separate GitHub face (herd lives in ranch) |
| Abolish rotting submodules; prefer independent checkouts + sync | Spark README omission of gatehouse, doorbell, cuttinggate, squawk, **arroyo** |
| `ops/sync.sh` idea | Buggy script (`{REPOS[@]}`, `"CHANGES"` string, commits ranch README into estate) |

**Canonical mental model (Grok + corrected Spark):**

| Plane | Repo / path | Role |
|---|---|---|
| Ops / master | `toxicwind/estate` → `~/estate` | pitchfork, config, bin, stack, ports |
| Projects / monorepo | `toxicwind/ranch` → `~/estate/ranch` | animals as directories |
| Control cell | `toxicwind/hatch` (private) | Ember; light only |
| Bot plane | `ranch/arroyo/` | overlord · coyote · discord (+ MCP shim) |
| Public MCP | `ranch/doorbell` + satellite `toxicwind/doorbell` curl mirror | `:25202`, aliases `/doorbell-mcp` `/gemini-mcp` |
| Agent (own cadence) | `toxicwind/tau` | nested or `~/tau` — one SSOT |
| Fleet / oracle | ranch + `toxicwind/squawk` for oracle | as today |
| Host name | **yote** / awrawr-pc | machine ≠ bot product |

Satellites only for: curl-install (`doorbell`), private cell (`hatch`), independent release (`tau`, maybe `squawk`). Everything else → ranch dirs or archive.

---

## 1. Immediate: Funnel (unblocks Gemini bridge)

Doorbell healthy on `:25202` is necessary but not sufficient — Funnel must be on.

```bash
# Diagnose
tailscale serve status
tailscale funnel status

# Fix (correct form — do NOT pass a bare "on" as HTTPS target)
# Prefer existing host script if present:
#   bash ranch/doorbell/scripts/funnel-on.sh   # or estate copy @ SHA 942ba604…
# Manual pattern (adjust path to live serve config):
tailscale serve --bg https+insecure://127.0.0.1:25202
tailscale funnel 443 on

# Prove
tailscale serve status   # expect (Funnel on), not (tailnet only)
curl -sS -o /dev/null -w '%{http_code}\n' https://github-mcp-host.tailc9ac71.ts.net/doorbell-mcp
curl -sS -o /dev/null -w '%{http_code}\n' https://github-mcp-host.tailc9ac71.ts.net/gemini-mcp
```

Then gatehouse upstream patch (`patch-upstreams.sh` @ `0ac68ff5…`) to real ranch/tools paths — no bad symlinks. Port `:25204` stays awrawr-ws-exec.

---

## 2. Hardcore cleanup — zero data loss (fixed protocol)

**Order is law:** ARCHIVE (SHA256 + non-empty) → PURGE → REPAIR → DOCS → COMMIT `main`.

### 2.1 Archive gate

```bash
ARCHIVE_DIR="$HOME/.tau/archives"
TS=$(date +%Y%m%d-%H%M%S)
TAR="$ARCHIVE_DIR/estate-rescue-${TS}.tar.gz"
# Archive relative to $HOME so restores are portable:
#   estate/var/scratch  estate/README.md  estate/.gitmodules
#   estate/ranch/tack  estate/ranch/README.md  estate/ranch/.gitmodules (if any)
# sha256sum "$TAR" | tee "$ARCHIVE_DIR/manifest-${TS}.txt"
# Abort if ! -s "$TAR"
```

Do **not** `tar` absolute paths without `-C` (Spark’s script did). Prefer `tar -C "$HOME" -czf …`.

### 2.2 Purge (only after gate)

- `ranch/tack/` — superseded by `@ranch/roost` (`mesh/catalog`)
- `estate/var/scratch/tmp-rescue-*` and other zombie checkouts
- `.tmp-clone-*` under tau plugins cache
- Empty `doorbell-v5` leftovers; dead gist / SP yote stubs (inventory already done)

### 2.3 Repair gitmodules

- Strip **dead** entries (`projects/shell/ii`, `tau/vendors`, …)
- Do **not** blindly replace entire `.gitmodules` with a single github/gitignore submodule unless audit shows that’s the only live one
- Prefer: no new submodules; research one-offs as plain dirs or archived repos

### 2.4 Deploy docs (plane map — not Spark flock-centric fiction)

**estate/README.md** — one page:

- Two boxes (hatch / yote host)
- pitchfork + port SSOT (`config/ports.env`)
- Link ranch for code; hatch private; doorbell public URL
- Deep links: ranch · tau · hatch · doorbell · squawk

**ranch/README.md** — animals by plane:

- Inference: herd · flock · cuttinggate · roost · keypool  
- MCP: gatehouse · doorbell · switchboard · lasso  
- Fleet: squawk · campfire · corral  
- **Bot: arroyo** (overlord · coyote · discord)  
- Agent: tau via chute  
- Kill / rewrite `ESTATE-PROJECTS.md` (sovereign-projects fiction)

**estate/ops/sync.sh** — status across `~/estate`, `~/estate/ranch`, `~/tau` (and herd path if separate). Fix array expansion; no auto-commit of wrong trees.

### 2.5 Commit

```text
estate main: chore: archive rescue scratch, sanitize gitmodules, README plane map, ops/sync.sh
ranch  main: docs: plane map; chore: remove tack (archived)
```

Push `main` (force only if history rewrite was part of the op and Chris confirmed that push).

---

## 3. arroyo landing (bot plane)

```
ranch/arroyo/
  overlord/   # GramJS MTProto — puppertrix / BotFather control
  coyote/     # Bun bot path (ex product name "yote")
  discord/
  mcp/        # thin shim → gatehouse :25127
```

- Host machine stays **yote**; product rename only  
- Env: introduce `ARROYO_*`, keep `YOTE_*` aliases until cutover  
- Archive standalone `toxicwind/yote` after in-tree SSOT proven on `:25102`  
- Make-work path: Overlord session (`YOTE_TELEGRAM_API_ID/HASH/SESSION`) DMs BotFather; Bun path uses bot token separately  

---

## 4. Phased execution (autonomous default)

| Phase | On host | Push |
|---|---|---|
| **A** Funnel + prove public `/doorbell-mcp` + `/gemini-mcp` | yes | n/a |
| **B** Archive → purge tack/scratch → sanitize gitmodules → sync.sh | yes | estate + ranch `main` |
| **C** README plane maps + kill ESTATE-PROJECTS fiction | yes | `main` |
| **D** `ranch/arroyo/` skeleton + MOVE from current yote paths | yes | ranch `main` |
| **E** gatehouse upstreams + shell prove | yes | as needed |
| **F** Overlord live prove (BotFather mint/rotate) | yes | when green |

Default autonomy: A→C without waiting; pause before destructive purge if archive size looks wrong; pause before force-push; pause before Overlord actions that mint tokens.

---

## 5. Invariants (October 2026 forward)

1. Project code → **ranch**; host ops → **estate**; cell → **hatch**.  
2. One provider authority: **roost**. No `tack` resurrection.  
3. No submodule lock-in for live animals.  
4. No relative `file:../../../…` package links — Bun workspace names or `$HOME` paths.  
5. Public Funnel for doorbell when Gemini/xAI need ingress; MagicDNS ≠ public.  
6. Never edit only live doorbell path; xai/ and spark/ workspaces stay unsymlinked.  
7. Ship on **main**, no PR theater.

---

## 6. Open questions (few)

See chat widget — answers unlock Phase B/D defaults.
