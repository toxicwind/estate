# 2026-10-31 kappa TUI freeze / Termius typing / trio route / estate path session (tau)

All items verified with live probes / real traffic this session.
Charter: every anomaly gets a capability-contract test before its fix is trusted.

## 79. Kappa TUI frozen shell — stdin never subscribed to fd 0
- **Symptom**: SSH kappa TUI rendered but typing had zero effect; kernel truth: strace showed `epoll_ctl ADD fd=0: 0` across full boots; 0 read(0) from the TUI main process; keystrokes sat in the tty buffer.
- **Root cause**: Bun's Node-compat `process.stdin` stream intermittently never starts its tty pump; the OpentUI renderer's `stdin.on("data")` attach produced no kernel subscription. Two prior "fixes" (c1671fd438, a861a09277) only called `stream.resume()` — no kernel effect. Deployed binary also predated them.
- **Fix**: `packages/tui/src/kappacode/input/tty-input.ts` — fake renderer stdin + pump feeding `renderer.stdinListener` (Bun.stdin.stream() native path with fd-pump fallback on lock), wired in `app.tsx` with teardown; binary rebuilt 0.0.0-main-202610310837, atomic-deployed. Commit `eab600a6ec` (kappa-code).
- **Contract test**: pty boot harness — type "zzverifyzz", assert echo ≤ 50 ms. Deployed binary verified: boot 9.2 s, echo 50 ms, no startup modals. tty-input.test.ts 11/11 green.

## 80. "Commands Unavailable: Expected JSON value at [6][template]" startup modal
- **Symptom**: every boot showed the Commands Unavailable modal; `/command` list 400'd via schema rejection `at [6]["template"]`.
- **Root cause**: `Info.template` is `Promise<string> | string` (lazy MCP-prompt commands); the HTTP JSON response encoded a Promise → not a JSON value → schema rejection.
- **Fix**: materialize templates at the list/get boundary via `Effect.option(Effect.promise(...))` with `_tag` narrowing to "" on failure. `eab600a6ec`.
- **Contract test**: deployed binary boot shows no "Commands Unavailable" (verify-deploy harness, `Commands Unavailable visible: False`).

## 81. Code Indexing Error — openai-compatible bge-m3 dimension undetermined
- **Symptom**: "Failed to initialize: Cannot determine vector dimension for model \"bge-m3\" with provider \"openai-compatible\""; indexing dead.
- **Root cause**: kappa-indexing model registry has an EMPTY `"openai-compatible": {}` profile map; config omitted `dimension`; error demanded explicit dimension. Secondary: qdrant JS client 1.17.0 vs server 1.19.1 version gate ("Client version 1.17.0 is incompatible").
- **Fix**: config `dimension: 1024` (SSOT olympus commit `d14734c`); qdrant client bumped 1.19.0 (`eab600a6ec`). freeinference live-probed: serves `BAAI/bge-m3` 1024 dims.
- **Contract test**: pty boot shows no indexing error (verify-deploy `Config Warning visible: False`).

## 82. Trio ROUTE channel default-route noise
- **Symptom**: `searchRoutes` classified any conditional line containing the needle as a "route" (else-if catch-all at 0.7) — guard clauses polluted ROUTE hits.
- **Root cause**: default fallback branch `else if (/(?:elif|if|case|match)\s+/)` in src/audit.ts.
- **Fix**: removed fallback; ROUTE = dispatch predicates + route declarations only. `dda139e` (trio).
- **Contract test**: new test/route.test.ts — dispatch predicates hit, guard clauses/conditionals never.

## 83. Trio MCP integration tests dead (HTTP vs stdio) + clone credential hang
- **Symptom**: 3 HTTP-backed tests ECONNREFUSED (server is stdio-only); rc_gh_compare returned "Cloning..." (fatal prompt on closed stdin).
- **Root cause**: stale test harness vs thresher-federated stdio reality; git clone prompting with stdin=/dev/null + invalid gh token.
- **Fix**: SDKS stdio client transport in tests; `GIT_TERMINAL_PROMPT=0` in runCli; live-github test skipIf(!ghHealthy). `dda139e`.
- **Contract test**: trio suite 45 pass / 1 documented skip / 0 fail.

## 84. GH tokens invalid box-wide (OPEN — rotation needed)
- **Symptom**: `gh auth status` invalid (hosts.yml + keyring GH_TOKEN both rejected by github); anonymous git clone flaky (401 intermittent).
- **Root cause**: revoked/expired tokens in both gh config and secretsmith keyring.
- **Fix**: pushes routed via `secretsmith exec --only GITHUB_TOKEN` + `x-access-token:` URL (works). Token ROTATION still required upstream.
- **Contract test**: keyring-auth push succeeded for kappa-code/olympus/trio/estate.

## 85. Ghost /home/toxic/estate recreated (single-truth lease violation)
- **Symptom**: `/home/toxic/estate/.state/` with live-models.json + provider-catalog caches (mtime Oct 30 17:13); systemd awrawr-mcp unit still points at `%h/estate/services/awrawr-mcp` (inactive; pitchfork lane is live at `~/.awrawr_mcp.py`).
- **Root cause**: a model-catalog writer defaulted to the estate path (writer hunt inconclusive — lease-guard script absent from estate-ops).
- **Fix**: ghost removed; state archived to `pens/estate/archive/2026-10-31-ghost-estate-state`.
- **Contract test**: `os.path.exists("/home/toxic/estate") == False`; watch for recurrence.

## 86. PATH sprawl: 11 entries, 3 bun copies, ghost dirs
- **Symptom**: PATH included `~/estate/bin` (ghost), `/bin` dup of usr-merged `/usr/bin`, THREE bun installs (~/.bun/bin, /usr/local/bin symlink, pacman 88MB binary).
- **Root cause**: accumulation (pacman bun + bun.sh + estate-ops era entries).
- **Fix**: pacman bun removed; `~/.bashrc.env` PATH slimmed to 4 entries (~/.local/bin primary, ~/.cargo/bin, /usr/local/bin, /usr/bin); 57 tool links folded into ~/.local/bin; envd port drifts fixed (4 stale values incl. GEMINI_MCP 25202→25227).
- **Contract test**: fresh-env resolution — bun/kappa/tau/gcloud/nvcc/nuclei all resolve from expected paths.

## 87. Decorative mcp.timeout silently dropped in V1
- **Symptom**: compat diag "Omitted native setting that cannot be represented in V1" for `mcp.timeout`.
- **Root cause**: `lowerTimeout` only lowers equal catalog/execution without startup; `request` isn't in the Timeout schema; emitted experimental.mcp_timeout has ZERO consumers (ast-grep: 0 refs).
- **Fix**: removed the block from SSOT config with rationale comment. `d14734c`.
- **Contract test**: boot diagnostics emit no mcp.timeout omission.

## 88. 3.8 GB tcpdump funnel capturing kappa loopback for 3.5 days
- **Symptom**: `sudo tcpdump -i lo -s 65535 -w /tmp/kappa/funnel-trace/funnel-keepalive.pcap` (ports 25127/25135/25136/25193/25217/25218) — full-payload capture of kappa↔thresher SSE incl. prompt content; every loopback RPC taxed.
- **Root cause**: leftover debug harness from the 2026-10-28 investigation (background-process-runner keepalive under tmux).
- **Fix**: killed process tree; pcap shredded (3.8 GB, root-owned, contained session payloads).
- **Contract test**: no tcpdump procs; pcap gone; loopback fetch latency normal.

## 89. Termius typing death over SSH (deobfuscated)
- **Symptom**: "I type with Termius and it just doesn't work" — letters never reach the terminal.
- **Root cause**: APK decompile (jadx) + device state: `use_normal_input_type_in_terminal` swaps to experimental InputConnection (p498ta/C25232b) that buffers commitText and routes non-modifier keys through a limited `handleExperimentalKeyEvent`; simultaneously Gboard suppressed (`mInputShown=false`, no HID keyboard attached, HID num_devices:0) — no letter input surface on screen.
- **Fix**: user-side 2 taps (collapse function strip / Settings→Terminal→disable "Use normal input type"); config keys documented.
- **Contract test**: Gboard visible + echo via Termius after toggle (awaiting user confirmation).

## 90. Dotfiles hyper-audit + declutter
- **Symptom**: 185 ~/.config entries; 29 junk backups; retired brand dirs (kilo/opencode); plaintext GH_TOKEN in environment.d; secretsmith-keyring-snapshot 24KB on disk; 14 tau.bak binaries; dots repo .config EMPTY vs live 185.
- **Root cause**: accumulation + dots repo not wired to live configs.
- **Fix**: 51 items archived to `pens/estate/archive/2026-10-31-dotfiles-declutter`; token conf archived; audit docs + metadata committed; PATH/dots table in `docs/path-dots-audit-2026-10-31.md`.
- **Contract test**: archive listing + clean `.config`; `ghp_` token string absent from all committed docs (scrubbed 2 docs before push).