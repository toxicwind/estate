# 2026-10-27 Anomalies — fleet restoration session

All items verified with live probes / real traffic this session. Charter:
every anomaly gets a capability-contract test before its fix is trusted —
each fix below shipped with one.

---

## 1. Namespace drift (the meta-anomaly)

**Symptom:** hindsight failed 80+ starts with "lib-ports.sh: No such file or
directory"; daemon scripts resolved `./stack/...` against a directory that
did not contain them; pitchfork.toml edits "did not take".

**Root cause:** TWO copies of the control plane — the estate CLONE
(`/home/toxic/estate`, tracked SSOT) and the pens NAMESPACE
(`/home/toxic/pens/estate`, what the supervisor loads per
`~/.config/pitchfork/config.toml`). The supervisor loads the namespace;
daemons run with `dir` inside the namespace; the clone's git tracked
`pitchfork.toml` + `config/` — three places one truth had to live.

**Fix:** `bin/sync-estate-ns.sh` + `bin/sync-stack.sh` (mirror semantics,
deletes stale artifacts) + a post-commit hook in the clone that runs them.
The clone stays the SSOT; the pen becomes a mechanical mirror.

**Contract test:** `sync-estate-ns.sh` then `diff` — the pen must equal the
clone for every synced path.

---

## 2. Supervisor state.toml resurrection

**Symptom:** daemons removed from pitchfork.toml (hashline, olympus, herd,
beellama-fast) kept being supervised — restarts respawned them; status
showed `errored` for daemons no config defined.

**Root cause:** `~/.local/state/pitchfork/state.toml` is the supervisor's
PERSISTED registry. On reload it merges state over config, and retired
daemons stay in state.toml forever. Editing pitchfork.toml alone is
therefore NOT sufficient.

**Fix:** stop pitchfork → delete the retired daemons' blocks (including the
dotted `.status`/`.env` sub-tables) from state.toml → start pitchfork.
Verified: retired daemons gone from status; 112 daemons tracked = 112 in
config.

**Contract test:** `pitchfork status | grep <retired>` must be empty after
retire + state-clean + restart.

---

## 3. Effect 4.0.6 runtime traps (kappa)

**Symptom:** `kappa serve` died with `Unexpected HttpServer address tag:
InetAddressV4` (and, in drizzle paths, `(void 0) is not a function`).

**Root cause:** (a) the resolved TCP address tag in 4.0.6 is
`InetAddressV4`/`InetAddressV6` — kappa checked `_tag === "TcpAddress"`;
(b) `Schema.TaggedError` became a generic factory needing the identifier
argument — `Schema.TaggedError()("X", …)` passes undefined into
`Error(undefined)` → `(void 0) is not a function` (drizzle's
cache-effect.js; the existing patch covered only errors.js).

**Fix:** kappa-code 1e61eaf702 (tag check + regenerated drizzle patch
covering cache-effect.{js,cjs}). Verified: `kappa serve` binds :25159,
auth wall live (401 without basic auth, 404 with).

**Contract test:** `kappa serve --hostname 127.0.0.1 --port 25159` (after
stopping the daemon) must print `kappa server listening on …`.

---

## 4. secretsmith env --app drops label-prefixed secrets

**Symptom:** `secretsmith env --app kappa` emitted only HODOS_API_KEY;
KAPPA_SERVER_PASSWORD (which had NO `service` attribute) was filtered out —
the kappa server booted UNSECURED.

**Root cause:** the filter was `attributes.service === a.app` (exact).
An app owns a secret when the service attr names it OR the label/key
belongs to it (case-insensitive prefix).

**Fix:** secretsmith.ts `cmdEnv` — match service attr OR
label/key-prefix. Verified: `--app kappa` emits HODOS_API_KEY +
KAPPA_SERVER_PASSWORD; kappa serve logs no "unsecured" warning and the
auth wall answers 401/404 correctly.

**Also found the same session:** `defaultCollection()` did
`String((await service()).ReadAlias(...))` — ReadAlias is an ASYNC dbus
call, so String(promise) → `Invalid object path: [object Promise]`, which
broke EVERY `secretsmith set`.

**Contract test:** `secretsmith env --app kappa` lists both keys;
`secretsmith set/get --show` round-trips a value.

---

## 5. Router UA pass-through (Cloudflare 1010)

**Symptom:** rhodochrosite answered bare `502 bad_gateway` on EVERY
`/v1/chat/completions`; direct provider probes with a library-default UA
returned 403 `error code: 1010`.

**Root cause:** the router forwarded only CONTENT_TYPE + ACCEPT upstream,
so reqwest sent its library-default UA; Cloudflare-fronted providers
(freeinference, groq) block it.

**Fix:** forward the caller's User-Agent; default to a desktop UA when
absent (proxy.rs `upstream_request`). Verified: estate/auto answers 200
through the router; direct freeinference calls 200 with the browser UA
(403 without).

**Contract test:** any alias through :25193 must return 200 (or a real
upstream error, never the UA-block 403).

---

## 6. Per-model credit/auth strikes (402 is per-model)

**Symptom:** ~25% of `estate/auto` requests burned a failover hop on
openrouter's "Insufficient credits" 402; the oracle's judge panel stretched
3.3s judge calls into 78s panels.

**Root cause:** 402/401/403 are PER-MODEL failures (one exhausted key, one
unlisted model) but the router treated only conn/429/5xx as failures — the
dead (provider, model) pair kept its weight share and was retried first
every time. Additionally the oracle's retry window was 22.5s per attempt.

**Fix:** (a) router `record_model_strikes` quarantines (provider, model)
after 3 strikes with 15-min decay (`model_selectable` gates selection);
(b) the oracle fails over auth-class failures in 8s. Verified live:
estate/auto 200 in 0.26–1.5s where it previously 402'd; oracle verdict
8.2s with all slots attempts=1 (was 78.5s with attempts=1/2/3).

**Contract test:** strike a lane (force a 402), then request that model —
the router must skip the struck pair without a failover delay.

---

## 7. Supervised state resurrect + peer snapshot fork (see also #2)

**Symptom:** `git status` in ranch showed phantom modifications for 277
squawk files frozen at v0.8.1 while the squawk peer repo was at v0.10.2;
the estate clone and pens namespace disagreed about pitchfork.toml.

**Root cause:** ranch's index tracked a PARTIAL SNAPSHOT of a peer's files.
Two owners = two truths. Peers are standalone clones; the parent must track
nothing under their roots (and must ignore their runtime WAL state —
rustdesk's sqlite3-shm/-wal guaranteed phantom dirt).

**Fix:** removed the snapshot from ranch's index; gitignored peer roots +
runtime state. Verified: ranch status clean; the peer repo is the only
owner of its files.

**Contract test:** in the parent, `git status --porcelain <peer>/` must be
empty while the peer's own `git status` is authoritative.

---

## 8. Daemon scripts depending on unset cwd / unexported env

**Symptom:** browserless died before bind (MODULE_NOT_FOUND from
`process.cwd()/node_modules/...`); rhodochrosite ran with zero provider
keys ("NotConnected" on every provider).

**Root cause:** (a) browserless' meta route resolves playwright-core via
process.cwd() — the daemon's cwd was the namespace dir, not the app dir;
(b) rhodochrosite's serve.sh sourced the keyring dump without `set -a`, so
keys were shell variables and did not survive `exec`.

**Fix:** run.sh `cd`s into the app dir; serve.sh wraps the source in
`set -a`/`set +a`. Verified: browserless binds :25130 and the management
route answers 200; the router serves estate/auto 200.

**Contract test:** `tr '\0' '\n' < /proc/<pid>/environ | grep -c <key>` on
the RUNNING process must show the keys; the service must bind its port.

---

## 9. New capability surfaces (not anomalies — additions)

- **estate-probe**: direct-DNS (raw UDP to 8.8.8.8 — a hijacked resolv.conf
  cannot hide), 32-query dork matrix, magic-byte sniffing (12 live tests).
- **fleet-tui**: dark-mode dashboard (fleet health, 16 probed lanes,
  funnel, 0-star provenance, MCP count).
- **fleet-audit-mcp**: the same surfaces as 6 MCP tools, federated through
  thresher (fleet-audit:lane_probe callable from any client).
- **bp.py → tau-shell `budget_chars`**: character-budget output with a
  reserved error pool (879 tau-shell tests pass; live 4000-line log test).
- **sse-passthrough** (thresher contrib): stdio↔HTTP MCP bridge with
  dynamic chaining.
