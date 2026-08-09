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
