# 2026-11-02 — Session maximal board (all threads, no drops)

Consolidation of every open thread this session. Artifacts referenced by path.

## ✅ Done this session (verified)

| Thread | Outcome | Evidence |
|---|---|---|
| **CoreELEC playback** | Drew Carey S5E16 playing (resolver-confirmed) | `playByShow` result |
| **nuvio ipk rebuild+deploy** | ipk 11.4MB built 12:40, installed+launched on LG TV | `ares-install` Success |
| **genre-map analysis** | single-portal id-keyed map proven wrong for 60 providers; live probe 23745/24231 match | (architect fixed) |
| **lg-eval v3** | exception surfacing + `__L__` luna helper + unicode byte-exact; SDK contract | `lg-fleet` `fb37273` pushed |
| **audit-correlator product** | NEW geode product: semantic audit-log behavior correlation (bge-m3); 9/9 tests; 69 misfits on real CF data | `toxicwind/audit-correlator` pushed |
| **CF audit log opened** | 18-month walk: 1300 events; attacker = noo056272@gmail.com = ACCOUNT OWNER (undeletable) | `p0-cf-account-owned-by-attacker.md` |
| **Hijack timeline** | Oct 30 hijack (12 events) + Nov 2 16:23-16:28 evidence destruction (token_roll/revoke) | `cf-hijack-evidence/` |
| **ghas transport fix** | fresh-session lane proven ×3; gateway dispatch verified live | (session evidence) |
| **session-audit fresh run** | kleio-deep-20261102: dataframe + findings + bands | `/tmp/kleio-deep-20261102/` |
| **Surfacemanager ground truth** | NO PiP service on webOS 5; LSM ACG-private; doc read from webosose source | `docs/lg-eval.agents.md` |

## 🔴 Open threads (with next action each)

### P0 hijack response (human-gated on registrar)
1. **Migrate 8 zones off attacker-owned CF account** — registrar NS re-point (NameCheap) to a clean account. DNS snapshot: `cf-hijack-evidence/cf-zone-dns-snapshot.json`. Runbook: `fix-hijack.ts --check` per zone once new token exists.
2. **Restore moment.mildlyawesome.com** — GitHub Pages content live (200); vanity host returns after zone recovery.
3. **Rotate every credential in the attacker's reach** — tunnel token (still valid, ours), all keyring CF entries (dead), any CF-scoped secrets.

### tau/kappa product fixes (approved maximal)
4. **coercion.ts TDD** — real freeinference + deepseek live-probe tests; expand from the existing `coercion-dots-list.test.ts` contract. Files: `tau/packages/ai/src/dialect/coercion.ts`, `tau/packages/ai/test/`.
5. **tau/kappa todo tool regressions** — verify the todo modifications live in BOTH TUIs (dual-TUI contract); fix at root, no special-casing.
6. **MCP endpoint audit** — add missing lanes to tau (`~/.tau/agent/mcp.json`) + kappa (`~/.kappa/kappa.jsonc`); 81 thresher upstreams exist, both TUIs should carry the full useful set.
7. **secretsmith CLI/UX rewrite** — `--help` currently prints bare usage (no subcommand help, no `--show` doc, no examples). Rewrite `printUsage()` → per-subcommand help, and add a `client_secret` hunt lane (chromium-logins/gcloud-credentials.db adapter) as a first-class command.

### Board/tooling consolidation
8. **Board consolidation** — this document IS the consolidation. Copy to `pens/estate/docs/sessions/2026-11-02-maximal-board.md` + link from KB.
9. **AGENTS.md anomaly rows** — append #105+ rows: CF-account-owned-by-attacker, evidence-destruction pattern, cfat_ account-token verify trap, session-JSONL credential graveyard.
10. **Commit+push sweep** — geode/audit-correlator (done: `6352d1f`), lg-fleet (done: `fb37273`), estate docs, kryptos (secretsmith rewrite), tau (coercion TDD).

## Lessons captured (do not regress)

1. `cfat_` prefix = Account-Owned Token — `/user/tokens/verify` returns 1000 BY DESIGN; test `/zones` instead.
2. Ownership ≠ membership: `Cannot delete the account owner` is the definitive tell.
3. Audit logs go back 18 months (not 30 days) — walk `since`/`before` windows.
4. Session JSONL is a credential graveyard — regex-sweep for `cfat_`/`ghp_` before assuming keys are dead.
5. Actor-class derivation beats keyword matching for audit correlation (bge-m3).
6. webOS PiP: no service exists on firmware; LSM is ACG-private; the app lane is the only luna lane.
