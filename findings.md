# findings.md — estate-wide audit, 2026-10-14

Living findings doc for the awrawr-pc estate. Every claim verified against
observable state (ss/curl/git/du) on 2026-10-14 unless marked UNVERIFIED.
Repairs landed this session are marked [FIXED]; open items marked [OPEN].

## 1. Fleet health (pitchfork, 91 daemons)

- Distribution: 57 running / 23 available / 16 stopped / **1 errored** [OPEN]
- `estate/awrawr-mcp` "errored" is a **stale-definition bug**: port :25198
  responds HTTP 401 (live, auth-gated). Pitchfork state field lies. [OPEN]
- `bidder-finch` stopped vs `bidder-forge` running: two bidder chains on
  different gateways; no action taken (additive-only doctrine).

## 2. Gatehouse / MCP mesh

- gatehouse = the **mcpproxy-go gateway binary** (rebrand), listening on
  :25127, running under pitchfork `estate/gatehouse`. [FIXED: understood]
- Bizarre-by-naming, not by behavior [OPEN — rename debt]:
  - binary lives in `ranch/range/bin/` as THREE files: `gatehouse`,
    `gatehouse.bak-20261011T104142Z`, `gatehouse-v0.51.0` (version soup;
    unclear which the serve script would pick if re-run — it execs the
    unversioned one)
  - port SSOT calls it `MCPPROXY_GO_PORT=25127` (old brand), config+data live
    in `ranch/barn/gatehouse/`, a data dir sits in `ranch/gatehouse-staging/`
    (config.db + index.bleve + logs)
  - `ranch/mcpproxy-go` repo is the source; `daemons.gatehouse` bootstrap
    logic (mcp_config.json from .dist, secrets injected from ~/.secrets) is
    load-bearing: direct-run crash-loops without it
- **This agent harness has no MCP servers attached** — the estate's mesh
  (awrawr-mcp :25198, gatehouse :25127, mcpproxy :25109, keypool) is not
  wired into agent sessions; all MCP work goes through bash probes. [OPEN]
- MCP server census in ranch: mcpproxy-go, rsync-mcp, mcp-prompt-injection-
  detector, wezterm-agent-mcp, kitty-mcp-server, fleet-bus-mcp, hatch-mcp,
  huggingface-mcp-server, mcp-gateway, pd-mcp-standalone, tmux-mcp,
  websearch-mcp (+ assorted one-off .py shims: smoke_mcp, mcpproxy-max-yolo,
  mcpproxy-max-yolo-v2 — scratch duplicates). [OPEN: v1/v2 shims unlabeled]

## 3. Port SSOT drift (`estate/config/ports.env`)

- `GHAS_API_PORT=25112` and `GHAS_MCP_PORT=25113` — both DEAD (connection
  refused, 000). AGENTS.md already flags :25113; the SSOT still carries them.
  [OPEN — scrub or mark dead]
- Sampled rest (herd 25100 dual-alias, awrawr-mcp 25198, gatehouse 25127):
  consistent with live listeners.

## 4. Tau (engine) — the deep findings

- Runtime/config fusion: `~/.tau → estate/config/tau` = **28 GiB inside the
  control-plane repo** (sessions 22G, agent/cache 3.6G, plugins 1.8G,
  natives 176M, logs 240M, reports 112M). Secrets (auth.json, flock.key,
  kimi-device-id) gitignored but physically co-located — one `git clean -xd`
  in estate destroys all credentials + runtime state. [OPEN — highest-risk item]
- **Root defect found: uncapped bash tool logs.** Sessions hold per-call
  logs like `59.bash.log` = 4.3 GiB; three Oct-2026 sessions = 15.2 GiB;
  jsonl transcripts are only 0.2 GiB of 1508 files. No size cap, no rotation.
  [OPEN — root cause of the six "fix tau" campaigns]
- Six+ one-shot repair scripts litter $HOME root
  (tau_fix_maximal_v{2..6}.sh, tau_maximal_rewrite.sh, tau-doctor*,
  fix_tau_*.sh, tau-repair.py, 2 report tars). None fixed the retention
  root cause. [OPEN — sweep to archive/fix-campaigns-20261014/]
- Family sprawl: 4 repos in 3 homes (ranch/tau, ranch/tau-extensions,
  ranch/tau-marketplace, estate/tau-skills); tau-extensions still has
  `omp-*` dirs; version identity still `+sovereign.tau.*`. [OPEN]
- Self-documented live bugs (docs/MISSING-FEATURES.md, 2026-10-08): B1 no
  hedged-stream.ts, B2 no HotfixRegistry, B3 no estate/integrations/,
  B4/B5 missing @ranch/tack → **gen:compat unrunnable**. [OPEN]
- tau repo has dirty build artifacts: embedded-addon.js modified,
  embedded-addons.linux-x64.tar.gz deleted (mid-flight natives rebuild).
  [OPEN — commit or restore]

## 5. Namespace debt (sovereign → estate, announced in 6af2094)

- rename-roundup dry-run (full report: ~/roundup-sovereign-report-20261014.txt):
  **265 path renames + 1445 content rewrites** still pending in estate.
  Hotspots: skills/sovereign-{chat,hatch-toolkit}, packages/sovereign-{scripts,
  utils,skills}, packages/caddy-sovereign-auth, stack/services/sovereign-
  exporter.py, pitchfork.d/sovereign-exporter.toml, tools/sovereign-chat,
  .github/workflows/sovereign-ci.yml, sovereign-scripts/, sovereign-skills/.
  [OPEN — content-only subset is safe; path renames need per-daemon care]
- Residue beyond estate: kimi-code-sovereign (src/local), gayxxx-sovereign
  (ranch), roundup result keys `sov__*`, ranch/pitchfork.d flicker→forge done
  but flicker-agent→forge-agent only partial in docs.

## 6. Shims/aliases audit [mostly FIXED]

- [FIXED] .bashrc.local: dead GITHUB_TOKEN (401) → vault sourcing (~/.secrets
  copy live, 200). .bash_profile clean.
- [FIXED] safe-rg log path → ~/.local/state/safe-rg.log (was ENOENT).
- [FIXED] direnv + pass installed; oxfmt/oxlint installed (bun run check
  unblocked).
- [FIXED] tok rewritten: multi-arg bug, ignored -e, dirs/totals/--top/--json/
  --cost; committed to tau repo (c3cbcdcaf).
- [FIXED] secretsmith: global-flags-after-subcommand, --label selectors,
  free-text search; README to readme-maximal; committed (c227ea2).
- [FIXED] pattern-forge de-conflict: BUILD DAEMON owns `forge` (pitchfork
  estate/forge :25148/:25240, renamed from flicker 2026-10-13); verification
  CLI keeps `pattern-forge`; shim documented. Canonical pattern-forge symlink
  re-pointed from var/workspaces snapshot to live skill dir.
- [FIXED] ranch 061bd32: landed prior session's uncommitted dots-client
  404 fix + 18 files of doc drift; estate-chat rename committed (cb8b657).
- [OPEN] `~/hatch` and `~/fledge` both → `~/kite/kite` (dual identity);
  `~/.omp` and `~/.tau` both → estate/config/tau.
- [OPEN] cover shim: intentional 27-byte no-op; origin undocumented.
- [OPEN] 13 orphan repos in src/local/ (kimi-*, squawk-relay-5f9a2c,
  free-claude-code, whatsapp-mcp…) — several with no remote.

## 7. Monorepo options (see conversation for full versions)

- A: config/runtime split + log-cap root fix + family absorption (recommended)
- B: tau as product monorepo (post-A, at next release)
- C: policy layer — layout-check manifest daemon + quarterly triage (complements)

## 8. In flight at time of writing

- roundup herd sweep (bgp_13d0fedc5001MWwOtHw3MOPHOw) →
  ranch/roundup/results/herd-20261014/ — first full-herd ranking since
  2026-10-02 (last one covered only 4 exaone quantizations; Oct 3 realworld
  sweep silently produced 0-byte results + empty weights).

## 9. Docs-estate audit (2026-10-15, subagent-verified)

- **AGENTS.md mutual-legacy contradiction [FIXED]**: /home/toxic/AGENTS.md and
  estate/AGENTS.md were byte-identical while each claimed the other was the
  "legacy variant". Estate copy now correctly declares itself a mirror of the
  authoritative /home/toxic/AGENTS.md.
- **Mesh truth**: `ranch/mesh/README.md` is the live-verified routing doc
  (cuttinggate :25200 canonical, estate-router :25104 LIVE, herd :25100,
  flock :25193 retired, keypool :25109, gatehouse :25127 fronts MCP).
  Estate-level docs contradict it: CONTROL_PLANE.md + MASTER_PLAN.md still
  cite "sovereign-router :25104 stopped"/"mcpproxy :25109 as MCP federation
  gateway" (wrong service), MASTER_PLAN.md:8 "herd DOWN" vs mesh README's
  live check. [OPEN — rewrite CONTROL_PLANE.md/MASTER_PLAN.md against mesh
  README]
- **Dead-path docs**: plans/master/REORG-PLAN.md (assumes ~/sovereign exists),
  pitchfork-modularization/sandbox/pitchfork.toml.orig (hardcodes dead
  projects/range/ranch), CONVENTIONS.md:66-67 (skills-hub as skills home,
  ~/workspace/skills symlink target missing), mbx.md + daemons.md +
  estate-map.md + environment-variables.md + port-ssot.md (all cite mbx-cache
  :25148 — no such daemon, port not listening; forge owns :25148 now).
  [OPEN — mark archived or fix]
- **Ranch structure**: 87 tracked git submodules + 6 ignored nested repos
  (vansrouter, tau, boundless, sigma, omp-semantic-policy, barn/woodpecker)
  + ~200 plain dirs. Duplications: paper-poller (ranch submodule vs
  deep-paper-reader leg), pi-skills (estate root checkout), sovereign-skills
  (submodule) vs estate/skills canonical. [OPEN — see monorepo options]

## 10. Kilo MCP wiring [FIXED]

- `~/.config/kilo/kilo.json` created: `mcp.gatehouse` → remote streamable-HTTP
  at http://127.0.0.1:25127/mcp (server confirmed: mcpproxy-go v0.1.0,
  initialize round-trip 200 with Mcp-Session-Id), Authorization via
  ${MCPPROXY_API_KEY} env interpolation — no secret literal in config.
- `~/.bashrc.local` now exports MCPPROXY_API_KEY from the vault (64-char key
  verified present in fresh login shell; `bash -lc true` healthy).

## 11. Forge decision (2026-10-15, Chris)

- **GitHub stays primary** — Copilot subscription + provenance/contribution
  history are assets; account is too good to lose.
- **Forgejo self-hosted joins as secondary mirror/redundancy** (free tier,
  one Go binary + sqlite, pitchfork daemon beside gatehouse/forge build
  daemon). Private repos mirrored to Forgejo; public repos dual-push
  (`git remote set-url --add --push` fan-out).
- Cleanup ladder still applies first: tarball-monster slimming
  (local-work-archive 3.5TB, three.ws 2.2TB, agent-dashboard 2.0TB,
  sovereign-projects 1.8TB, estate 1.5TB, OmniRoute 1.4TB), backup/tmp repo
  kills, 60 dual-truth name reconciliations — slim before mirroring.
- Pilot: secretsmith → Forgejo first, then fleet-wide multi-remote sweep.

## 12. RustDesk

(2026-10-15) Self-hosted RustDesk relay stack added to the estate service layer.

- **Installed:** rustdesk-server 1.1.16, official GitHub release binaries at
  `ranch/rustdesk-server/amd64/` (hbbs, hbbr, rustdesk-utils). Not in Arch repos;
  AUR would have compiled from source — release binary chosen instead.
- **Ports** (SSOT in `config/ports.env`, RUSTDESK_* keys; verified free with `ss -ltnu`):
  hbbs `-p 25221` → 25220 (nat-type test tcp), 25221 (tcp + udp hole punch),
  25223 (websocket); hbbr `-p 25222` → 25222 (relay tcp), 25224 (websocket relay).
  Block 25220-25224 chosen after 25151/25152 (oracle-core/toolcall) and the
  nativelink/forensics/windmill clusters were ruled out.
- **Pitchfork:** `daemons.rustdesk-hbbs` and `daemons.rustdesk-hbbr` in
  `pitchfork.toml`, `auto = ["start"]`, `retry = true`. No HTTP health endpoint
  exists in rustdesk-server — supervised via `ready_cmd` TCP `ss` checks only.
  hbbs advertises the relay with `-r 100.72.199.93:25222` (tailscale IP).
- **Keys:** id_ed25519 keypair generated in `ranch/rustdesk-server/` on first run;
  private + public key gitignored, never committed.
- **Mise tasks:** `mise run rustdesk-logs` (tail both daemons' pitchfork logs),
  `mise run rustdesk-clients` (print the client connection block).
- **Client config** (RustDesk → Settings → Network → ID/Relay Server):
  ID server `100.72.199.93:25221`, Relay `100.72.199.93:25222`,
  Key `VLtWm5nG+d9TYWxB1C1uLELf2cFYMtbT75fASh9DT2M=`.
  UDP 25221 must stay open on the tailnet for hole punching.

## 13. Network & Tailscale

Audited 2026-10-15 (full evidence: `findings/prior-audits/network-audit-20261015.txt`).

| # | Item | Verdict | Evidence / fix |
|---|---|---|---|
| 1 | Interfaces/routes | PASS | enp12s0 10.0.0.218/24 (LAN), tailscale0 100.72.199.93, tsd 100.108.135.48 (2nd tailscale: github-mcp-host), docker bridges 172.17-21 |
| 2 | MagicDNS | PASS (already on) | tailnet-wide, suffix `tailc9ac71.ts.net`; accept-dns enabled; systemd-resolved active + stub resolv.conf symlink |
| 3 | Subnet router (10.0.0.0/24) | PASS (advertised) | `tailscale set --advertise-routes=10.0.0.0/24`; **approval pending in admin console** (PrimaryRoutes: None) |
| 4 | Tailscale SSH | PASS (already on) | `RunSSH: true` in prefs; no reconfiguration needed |
| 5 | Direct vs DERP | PASS | almalinux-server: direct `172.96.160.178:41641` ~41-44ms ( DERP warmup 141ms); doorbell direct (LAN) <1ms |
| 6 | tailscaled boot | PASS | `systemctl is-enabled tailscaled` = enabled, active |
| 7 | Host firewall | PASS (installed+enabled) | Was: only docker/tailscale chains, INPUT policy ACCEPT. Now: `inet awrawr_filter` baseline in `config/nftables.conf` → `/etc/nftables.conf`, `nft -c` validated, nftables.service enabled. Deliberately NO `flush ruleset` (protects docker/ts tables). Verified SSH survived (session from 10.0.0.77) |
| 8 | RustDesk 25220-25224 | PASS (tailnet-only) | hbbs/hbbr bind * but firewall: full accept from `tailscale0`/`tsd`; LAN+public dropped |
| 9 | Loopback exposure of 25xxx | PARTIAL | Many services bound 0.0.0.0/* (25102/25103/25105/25110/25117/25118/25148/25144/25201/25212/25219/25240, kafka 9093/37725/25144, dockerd 43000, effusion-web). **Firewall now blocks all non-loopback access** except LAN allowlist (3000/3001/8503/25100-25107/25203). Bind fixes per-service left to owners (see below) |
| 10 | valkey 25203 on 0.0.0.0 | FIXED | pitchfork.toml `[daemons.redis]` run line: `--bind 0.0.0.0` → `--bind 127.0.0.1`, restarted, ss confirms 127.0.0.1:25203 |
| 11 | ip_forward persistence | PASS (installed) | Was set live but not persisted under an explicit tailscale file. New: `config/sysctl.d/99-tailscale-forward.conf` → symlink `/etc/sysctl.d/99-tailscale-forward.conf` (ip_forward=1 v4+v6) |
| 12 | DNS consistency | PASS | systemd-resolved stub (127.0.0.53) + tailscale accept-dns; dnsmasq 10.0.0.218:53 serves LAN (allowed from LAN only) |

### Needs Chris (admin console)
- **Approve subnet route** 10.0.0.0/24 for `estate` (100.72.199.93) at https://login.tailscale.com/admin/networks — advertised, not yet approved.

### Client-facing facts
- Tailscale IP `100.72.199.93`, MagicDNS `estate.tailc9ac71.ts.net`; funnel on `https://estate.tailc9ac71.ts.net`.
- Subnet route 10.0.0.0/24 (once approved) reaches LAN incl. 10.0.0.218 services.
- Tailscale SSH enabled; RustDesk via 100.72.199.93:25220-25224 (tailnet only).

### Bind-fix backlog (documented, not forced — pitchfork-owned)
For each 0.0.0.0-bound service, prefer `--bind 127.0.0.1` (or interface-specific) in its pitchfork run line, like the valkey fix. Ports still bound wide: 25102/25103/25105/25110/25201/25219 (bun), 25117 (hindsight-api), 25118 (next-server), 25148/25240 (flicker-server), 25212 (systemd user mgr), 43000 (effusion-web docker publish — change to `127.0.0.1:43000->80`), kafka 9093/37725/25144, syncthing 22000, dnsmasq 53 (LAN DNS — intentional), tailscaled 55911 (tailscale-owned).

## 14. freeinference concurrency recon (2026-10-15, ferret-methodology)

Probe matrix: 9 lanes, concurrent pairs racing; script + results in
`findings/prior-audits/freeinference-concurrency-recon.sh`. Verdicts:

| Lane | Result |
|---|---|
| same model x2 concurrent | one 200, one **429 concurrency_limit_exceeded (limit: 1)** |
| two DIFFERENT models concurrent | one 200, one **429** — limit is GLOBAL per key, not per model |
| UA curl/OpenAI/tau concurrent | UAs treated identically — pure arrival-order serialization |
| Claude shape `/v1/messages` | **SUPPORTED** (200) — but routed to `qwen3.6-35b` while requesting `glm-5.3-flash`: the anthropic-shaped endpoint **silently remaps the model field** |
| OpenAI shape `/chat/completions` | works (loses arrival race only) |

Conclusions: (1) freeinference enforces ONE concurrent request per key,
provider-side — Kilo Code imposes no such limit (both subagents spawned).
(2) Whichever request arrives second eats the 429; serialization gate, not
per-model quota. (3) Fleet rule: parallel lanes override off freeinference
(kilo/Nemotron proven); freeinference jobs serialize or resume after 429.
(4) Do not trust `model` on `/v1/messages` — verify `model` in the response
payload (live example returned qwen3.6-35b for a glm request).
