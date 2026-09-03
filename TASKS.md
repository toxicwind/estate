# Sovereign Fix Tasks - Live Tracker

## Task 0: Nuvio LG TV Deployment (HIGHEST PRIORITY)

### 0.1 Prerequisites
- [ ] Fork max level (streaming, MCP, pitchfork, boot all fixed)
- [ ] Review Nuvio UX in tools/nuvio-platform/
- [ ] Install WebOS SDK + ares-cli on toxic host
- [ ] LG TV in developer mode and paired

### 0.2 Build & Deploy
- [ ] Build WebOS app (ares-package)
- [ ] Package as .ipk
- [ ] Install on TV (ares-install)
- [ ] Launch (ares-launch)

### 0.3 Test
- [ ] Verify app runs on TV
- [ ] Test remote control integration
- [ ] Test network connectivity to sovereign services

---

## Status Legend
- [ ] Pending
- [x] Done
- [~] In Progress
- [!] Blocked

---

## Phase 1: Critical Bug Fixes (HIGH)

### 1.1 Streaming Bug Fix
- [x] Fix `Stream ended without finish_reason` in openai-completions.ts
- [x] Enable PI_DEBUG_STREAM=1 in bashrc for pi-agent profile
- [ ] Rebuild pi-agent to pick up changes
- [ ] Test streaming fix

### 1.2 Truncation Limits
- [x] Fix DEFAULT_MAX_BYTES to be adaptive (512KB → 4MB for 1M context)
- [x] Create `rf` (read-full) helper script
- [ ] Rebuild pi-agent

### 1.3 Debug Logging
- [x] Enable PI_DEBUG_STREAM in bashrc
- [x] Enable PI_DEBUG in bashrc
- [ ] Add debug logging to streaming code
- [ ] Verify debug output works

---

## Phase 2: LLM Bash Kernel Setup (HIGH)

### 2.1 Bash Kernel for pi
- [ ] Setup auto-hook for pi sessions
- [ ] Create pi-bashrc with full debugging
- [ ] Add trace_wrapper for command timing

### 2.2 Bash Kernel for grok
- [ ] Setup auto-hook for grok sessions
- [ ] Create grok-bashrc with full debugging

---

## Phase 3: Experimental Crisis Skills as MCP (HIGH)

### 3.1 Borrow Useful Code
- [ ] trace_wrapper.py → timing wrapper for commands
- [ ] auto_hook.py → connection monitoring (adapted)
- [ ] file_watcher.py → file watching (adapted)
- [ ] skill_runner.py → skill execution framework

### 3.2 Create Modular MCP Server
- [ ] Create MCP server with profile system (local, kimi, generic)
- [ ] Implement skill discovery from profiles
- [ ] Add tools: sdk-auditor, infra-recon, seed-hunter, stemforge
- [ ] Test MCP server

### 3.3 Add to mcpproxy
- [ ] Register experimental-crisis in mcp_config.json
- [ ] Test tools through mcpproxy

---

## Phase 4: Model Selection (HIGH)

### 4.1 Find Benchmark Data
- [ ] Search sovereign/ for benchmark results
- [ ] Search pi-agent/ for model benchmarks
- [ ] Compile RPM/latency data

### 4.2 Test Models
- [ ] Test current default model
- [ ] Test alternative fast models
- [ ] Select fastest model that won't hit limits

### 4.3 Set Default
- [ ] Update pi config with new default
- [ ] Document the change

---

## Phase 5: Pitchfork Fork (NORMAL)

### 5.1 Fork Setup
- [x] Fork pitchfork on GitHub (toxicwind/pitchfork)
- [ ] Add --json flag to start command
- [ ] Suppress DEBUG noise in non-verbose mode
- [ ] Build and install forked version

### 5.2 LLM-Friendly Wrappers
- [x] Create pitchfork-llm wrapper script
- [ ] Test wrapper with actual commands

---

## Phase 6: Boot & Integration (HIGH)

### 6.1 Pitchfork Boot
- [x] Enable pitchfork boot
- [ ] Fix tailscale-funnel in pitchfork.toml groups
- [ ] Add SSHX_PORT=25138 to ports.env
- [ ] Start all core daemons

### 6.2 Final Testing
- [ ] Test full boot sequence
- [ ] Test all daemons start
- [ ] Test MCP tools work
- [ ] Test streaming fix

---

---

## Phase 7: Firefox Nightly & First-Class Web UI Launcher (DONE)

### 7.1 Port 9222 & CDP Isolation
- [x] Analyze port 9222 collision (Chromium CDP vs `firefox-bidi.service`)
- [x] Keep port 9222 dedicated to Chromium CDP sandbox (`kataware-doki/cdp-node.ts`, `tools/bugbounty/lib/helpers.mjs`)
- [x] Isolate interactive Firefox Nightly (`g304xzha.default-release`) from background service profile locks

### 7.2 Hyprland & MIME Standardization
- [x] Override `browser = "firefox-nightly"` in `~/.config/hypr/custom/variables.lua`
- [x] Set `hl.env("BROWSER", "firefox-nightly")` in `~/.config/hypr/custom/env.lua`
- [x] Restore MIME associations to `firefox-nightly.desktop` for html/http/https/pdf
- [x] Set `export BROWSER=firefox-nightly` in `~/.bashrc`

### 7.3 Sovereign Web UI Launcher CLI
- [x] Create `scripts/open-web-uis.ts` with failfast probe, SSOT port lookup, and Firefox Nightly IPC
- [x] Create `scripts/open-web-uis.sh` wrapper
- [x] Add anonymous admin auto-login to `stack/services/grafana-mesh.sh`
- [x] Add `open-uis`, `open-uis-all`, `list-uis` tasks to `src/generators/mise.ts`
- [x] Regenerate `mise.toml` via `bun run scripts/generate.ts`
- [x] Add comprehensive test suite `tests/open_web_uis.test.ts` (4 pass, 67 assertions)
- [x] Document usage in `README.md`

## Current Focus
**Phase 1** - Rebuild pi-agent with streaming fix

## Blockers
- None currently

## Notes
- Pitchfork already has --json for list command
- Need to add --json to start, stop, status
- Experimental-crisis skills are mostly SKILL.md + references
- The useful Python scripts: trace_wrapper.py, auto_hook.py, file_watcher.py, skill_runner.py
- ZMQ kernel stuff is container-specific, skip it
