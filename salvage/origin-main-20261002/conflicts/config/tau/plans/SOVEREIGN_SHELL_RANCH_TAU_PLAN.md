# Sovereign Shell, Ranch, and Tau Consolidation Plan

## Context
WezTerm tabs and window switching are broken due to `enable_tab_bar = false` in `wezterm.lua`, absent tab/window keybindings in WezTerm, and missing `Alt+Tab`/`cycle_next` bindings in Hyprland for stacked/identical-coordinate windows. Furthermore, `~/.config/wezterm` was never tracked inside the sovereign shell repository (`sovereign/projects/shell/ii/dots/`), `sovereign-end4` lacked its upstream remote (`end-4/dots-hyprland`), and the service routing stack exhibits drift (such as `squawk-feed` referencing a relocated path). This plan establishes the sovereign shell repo as the permanence controller for desktop configurations, repairs WezTerm and Hyprland window/tab switching, audits the inference and router fleet, formalizes the placement of the Sovereign Socket Stream and Cognitive EKG between Ranch and Tau, and updates the main documentation to eliminate obsolete references.

---

## Architectural Placement: Socket Stream & Cognitive EKG between Ranch and Tau

### 1. Section 1 (Direct Socket Task Runner & Egress) -> Ranch Transport Adapter
- **Placement**: `sovereign/projects/range/ranch/stockyard/stream-broker` & `packages/sovereign-utils/src/transport/socket-stream.ts`.
- **Role**: Ranch operates as the external provider multiplexer and inference front door (`herd` :25100, `flock` :25193). Standard Node/Python fetch layers drop SSE streams during prolonged model thinking phases when middlebox TCP keepalive fails.
- **Mechanism**: The Direct Socket Task Runner establishes OS-level keepalive (`SO_KEEPALIVE`, `TCP_KEEPIDLE=30`, `TCP_KEEPINTVL=10`, `TCP_KEEPCNT=3`, `TCP_NODELAY=1`) and exposes a local UNIX domain socket (`/run/user/1000/sovereign-stream-broker.sock`). When connection reset occurs mid-generation, it salvages validated reasoning tokens in an append-only ring buffer and performs assistant-prefix continuation instead of re-prompting from scratch.

### 2. Section 2 (Telemetric Runtime Oracle & Thermodynamic Loop Interception) -> Tau Agent Runtime
- **Placement**: `sovereign/tau/engine/packages/coding-agent/src/telemetry/cognitive-ekg.ts` and `tau` turn supervisor.
- **Role**: Tau manages agent turns, context window horizons ($\Omega_{\text{horizon}}$), prompt token budgeting ($M_{\text{in}}$), and completion streaming ($Y_{\text{out}}$).
- **Mechanism**: Tau calculates the 7-dimensional telemetry vector $\mathbf{\tau}(t) = \langle t, \Delta t, M_{\text{in}}, Y_{\text{out}}, \Omega_{\text{ctx}}, \delta_{\text{turn}}, v_{\text{gen}} \rangle$ and evaluates the 4-state transition matrix:
  - **NOMINAL** ($S_{\text{ctx}} < 0.80, \eta_{\text{gen}} > 0.25, v_{\text{gen}} > 30\text{ tok/s}$): Unimpeded generation.
  - **SATURATED** ($0.80 \le S_{\text{ctx}} \le 0.88$): Soft checkpoint advisory injected into session stream.
  - **THRASHING** ($S_{\text{ctx}} \ge 0.88, \eta_{\text{gen}} < 0.15$ or trigram diversity $< 0.38$): Dispatches out-of-band interrupt, commits state to SQLite, prunes repetition, and forces context compaction.
  - **STALLED** ($v_{\text{gen}} < 15\text{ tok/s}$): Routes socket to fast local fallback.

### 3. Section 3 (Sovereign Master Orchestrator) -> Pitchfork Supervised Daemon
- **Placement**: `sovereign/pitchfork.toml` daemon `[daemons.sovereign-stream-broker]`, listening on UNIX socket and port :25145, supervised with auto-restart.

---

## Approach

### Part 1: WezTerm Tab Bar and Window Switching Permanent Fix
1. **Enable Tab Bar and Configure Responsive Visuals**:
   - Target: `sovereign/projects/shell/ii/dots/.config/wezterm/wezterm.lua`.
   - Set `enable_tab_bar = true`.
   - Set `use_fancy_tab_bar = false` (lightweight, high-contrast terminal tab bar that does not waste vertical pixels).
   - Set `tab_bar_at_bottom = false`.
   - Set `hide_tab_bar_if_only_one_tab = false` so tabs are always visible when working in multi-task workflows.
   - Configure Catppuccin Mocha tab bar color palette (`active_tab`, `inactive_tab`, `new_tab`).
2. **Add Tab and Window Switching Keybindings**:
   - In `wezterm.lua` `keys` table:
     - `CTRL+SHIFT+T`: `SpawnTab "CurrentPaneDomain"`
     - `CTRL+SHIFT+W`: `CloseCurrentTab { confirm = true }`
     - `CTRL+Tab`: `ActivateTabRelative(1)`
     - `CTRL+SHIFT+Tab`: `ActivateTabRelative(-1)`
     - `LEADER + [`: `ActivateTabRelative(-1)`
     - `LEADER + ]`: `ActivateTabRelative(1)`
     - `LEADER + 1` through `LEADER + 9`: `ActivateTab(0)` through `ActivateTab(8)`
     - `ALT + 1` through `ALT + 9`: `ActivateTab(0)` through `ActivateTab(8)`
     - `LEADER + o`: `ShowTabNavigator` (searchable fuzzy list of all tabs and windows)
     - `LEADER + w`: `ShowLauncherArgs { flags = "FUZZY|WORKSPACES|TABS" }`
     - `LEADER + p`: `ActivateWindowRelative(-1)`
     - `LEADER + n`: `ActivateWindowRelative(1)`
     - Preserve existing pane splits (`LEADER + v`, `LEADER + s`) and pane navigation (`LEADER + h/j/k/l`).

### Part 2: Sovereign Shell Permanence Controller & Submodule Unification
1. **Move WezTerm Configuration into the Shell Submodule**:
   - Copy `/home/toxic/.config/wezterm/wezterm.lua` into `/home/toxic/sovereign/projects/shell/ii/dots/.config/wezterm/wezterm.lua`.
   - Ensure `plugins/wezterm-cmdpicker` and `shell-integration.sh` remain cleanly colocated in `dots/.config/wezterm/`.
2. **Symlink ~/.config/wezterm to Sovereign Shell Dots**:
   - Remove the unmanaged directory `/home/toxic/.config/wezterm` (backing up any untracked files).
   - Symlink `/home/toxic/.config/wezterm -> /home/toxic/sovereign/projects/shell/ii/dots/.config/wezterm`.
3. **Update Dotbot Installation Manifest**:
   - Edit `sovereign/projects/shell/ii/install.conf.yaml`:
   - Under `- link:` add:
     ```yaml
     ~/.config/wezterm: dots/.config/wezterm
     ```
   - Verify `~/.config/hypr` and `~/.config/quickshell` links are documented and intact.
4. **Audit and Configure Upstream Git Remotes**:
   - In `sovereign/projects/shell/ii`:
     - Keep `origin https://github.com/toxicwind/sovereign-end4.git`.
     - Register `upstream https://github.com/end-4/dots-hyprland.git`.
     - Fetch upstream branches (`upstream/main`).

### Part 3: Hyprland Window Switching & End-4 Navigation Features
1. **Implement Window Cycling Dispatcher Bindings**:
   - Target: `sovereign/projects/shell/ii/dots/.config/hypr/hyprland/keybinds.lua`.
   - Add bindings for cycling through stacked / overlapping windows (resolves inability to switch between WezTerm windows at identical coordinates `1285,745`):
     ```lua
     --# Window Cycling (Alt+Tab / Alt+Shift+Tab)
     hl.bind("ALT + Tab", hl.dsp.window.cycle_next(), { description = "Window: Cycle next window" })
     hl.bind("ALT + SHIFT + Tab", hl.dsp.window.cycle_next({ prev = true }), { description = "Window: Cycle previous window" })
     hl.bind("SUPER + Tab", hl.dsp.window.cycle_next(), { description = "Window: Cycle next window" })
     hl.bind("SUPER + SHIFT + Tab", hl.dsp.window.cycle_next({ prev = true }), { description = "Window: Cycle previous window" })
     ```
   - Re-map Quickshell Overview toggle to `SUPER + Grave` or `SUPER + Space` / `CTRL + SUPER + Tab` so it does not conflict with standard window cycling.
2. **Support Shift+Tab in Quickshell Search & Overview**:
   - Target: `sovereign/projects/shell/ii/dots/.config/quickshell/ii/modules/ii/overview/SearchBar.qml` and `SearchWidget.qml`.
   - Add `Qt.Key_Backtab` handler alongside `Qt.Key_Tab` to cycle results backward.

### Part 4: Inference Stack & Router Fleet Audit & Remediation
1. **Audit & Fix Daemon Definitions in `pitchfork.toml`**:
   - **`squawk-feed`**: Update `/home/toxic/sovereign/hatch/agents/ember/squawk-relay/run-feed.sh` line 9 to execute `/home/toxic/sovereign/projects/range/ranch/squawk/squawk_feed.py` instead of the nonexistent `/home/toxic/squawk/squawk_feed.py`. Restart `sovereign/squawk-feed`.
   - **`model-guard`**: Edit `/home/toxic/sovereign/bin/herd-model-guard.py` to catch `ConnectionResetError` and `BrokenPipeError` in request handling without crashing the server thread. Restart `sovereign/model-guard`.
   - **`sovereign-router`**: Add `auto = ["start"]` to `[daemons.sovereign-router]` in `sovereign/pitchfork.toml` and verify health on port 25104.
   - **`herd` (:25100)**: Audit status (currently running, health OK).
   - **`flock` (:25193)**: Audit status (currently running, health ok).
   - **`rust-web` (:25201)**: Audit status (currently running, serving ops dashboard).
   - **`shep` (:25127)**: Audit status (currently running, MCP federation).
   - **`keypool` (:25109)**: Audit status (currently running).
2. **Audit Port SSOT (`sovereign/config/ports.env`)**:
   - Run `bin/port-audit` to confirm zero listener collisions across the 25xxx port space.

### Part 5: Main README.md & Old Reference Consolidation
1. **Revise `sovereign/README.md`**:
   - Replace legacy references to retired `scripts/generate.ts` with explicit documentation of hand-edited `pitchfork.toml` and `mise.toml`.
   - Add architectural documentation for Ranch (`projects/range/ranch`), the Herd/Flock inference contract, and the sovereign shell submodule (`projects/shell/ii`).
   - Document the Socket Stream and Cognitive EKG specification in `docs/architecture/socket-stream-cognitive-ekg.md` and link from `README.md`.
   - Clarify the role of `projects/shell/ii` as the permanence controller for desktop configurations (`~/.config/hypr`, `~/.config/quickshell`, `~/.config/wezterm`).
2. **Update Repo Documentation**:
   - Update `sovereign/projects/shell/README.md` to document the WezTerm configuration structure, tab navigation keybinds, and dotfiles symlink layout.

---

## Critical Files & Anchors

1. `sovereign/projects/shell/ii/dots/.config/wezterm/wezterm.lua` (New in git repo): Primary configuration for WezTerm with tab bar enabled, mocha colors, and tab/window navigation keybindings.
2. `sovereign/projects/shell/ii/dots/.config/hypr/hyprland/keybinds.lua`: Hyprland keybindings file; anchors at line 155 (`Window: Focus`) where `ALT + Tab` and `cycle_next` are bound.
3. `sovereign/projects/shell/ii/install.conf.yaml`: Dotbot manifest defining declarative symlinks between `dots/` and `~/.config`.
4. `sovereign/hatch/agents/ember/squawk-relay/run-feed.sh`: Launcher script for `squawk-feed`; anchor at line 9 (path to `squawk_feed.py`).
5. `sovereign/pitchfork.toml`: Master Pitchfork daemon supervisor; anchors at `[daemons.sovereign-router]`, `[daemons.model-guard]`, and `[daemons.squawk-feed]`.
6. `sovereign/README.md`: Central documentation for the sovereign estate.

---

## Verification

1. **WezTerm Tab & Window Functionality**:
   - Launch `wezterm`. Verify tab bar is visible at the top/bottom.
   - Press `CTRL+SHIFT+T` (or `LEADER + t`): confirm new tab opens and tab bar displays multiple tabs.
   - Press `CTRL+Tab` / `CTRL+SHIFT+Tab`: confirm instant cycling between tabs.
   - Press `LEADER + o`: confirm searchable fuzzy Tab Navigator window opens.
   - Spawn multiple WezTerm windows (`LEADER + n`).
   - Press `ALT + Tab` in Hyprland: confirm focus switches between stacked WezTerm windows even when at identical coordinates.
2. **Sovereign Shell Permanence**:
   - Run `ls -l ~/.config/wezterm`: verify it points to `/home/toxic/sovereign/projects/shell/ii/dots/.config/wezterm`.
   - Run `git -C /home/toxic/sovereign/projects/shell/ii status`: verify `wezterm.lua` is tracked in git.
   - Run `git -C /home/toxic/sovereign/projects/shell/ii remote -v`: verify both `origin` and `upstream` remotes are active.
3. **Router & Service Health Audit**:
   - Run `curl -fsS http://127.0.0.1:25100/health`: expect `OK` (herd).
   - Run `curl -fsS http://127.0.0.1:25193/health`: expect `ok` (flock).
   - Run `curl -fsS -I http://127.0.0.1:25201/`: expect `200 OK` (rust-web ops dashboard).
   - Run `curl -fsS http://127.0.0.1:25104/health`: expect `ok` or JSON status (sovereign-router).
   - Run `pitchfork status sovereign/squawk-feed`: expect `running`.
   - Run `mise run health`: verify all core daemons pass health checks.

---

## Assumptions & Contingencies

1. **Hyprland Overview vs Alt+Tab**:
   - *Assumption*: Users expect standard `ALT + Tab` to cycle through active windows on the current workspace, while `SUPER + Tab` or `SUPER + Grave` can open the Quickshell overview.
   - *Contingency*: We bind `ALT + Tab` to `hl.dsp.window.cycle_next()` and retain `SUPER + Grave` (or `CTRL + SUPER + Tab`) for Quickshell overview so both are instantly accessible.
2. **WezTerm Tab Bar Position**:
   - *Assumption*: Non-fancy tab bar at top or bottom with `Catppuccin Mocha` theme is preferred to match the existing sovereign desktop aesthetic.
   - *Contingency*: If user prefers tab bar at bottom or custom font size, it is a single setting in `wezterm.lua` (`tab_bar_at_bottom = true`).
3. **Shell Submodule Remote URLs**:
   - *Assumption*: `origin` is `toxicwind/sovereign-end4` and `upstream` is `end-4/dots-hyprland`.
   - *Contingency*: If push credentials for `origin` require ssh instead of https, git config can use `git@github.com:toxicwind/sovereign-end4.git`.
