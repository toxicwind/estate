I need to complete a massive Phase 1 setup. Let me start by creating a task plan and then systematically check/install all## Phase 1: Complete Plan

### Already Known
- Working directory: `/home/toxic`, Linux x86_64 (Cachyos), with pacman, cargo, go, npm, pip available
- Need to install/optimize ~60+ tools listed in §Context
- Need to configure MCP servers in `~/.agent/mcp.toml` and `~/.mcpproxy/mcp_config.json`
- Need to wire shell integration into `~/.bashrc.env`

### Step 1 — Inventory (command -v sweep)
Run a single bash script that checks `command -v` for every tool in the list, captures path + version, and outputs structured results. This avoids per-tool overhead. Tools span package managers:
- **pacman**: ripgrep, fd, bat, fzf, direnv, jq, tig, tldr (if in repo), bottom (if in repo)
- **cargo (rustup)**: ast-grep, eza, dust, procs, zoxide, sd, grex, hyperfine, just, xh, doggo, gping, starship, atuin, delta, difftastic, watchexec, bandwhich, gitui, lazygit, hexyl, pueue, tilth, seekrs, sgrep, miller, qsv, git-snitch, git-scout, gitgalaxy, gitcrawl, repodrift, gitundo, gitpanic, git-panic, easegit-cli, gitfix, git-merge-forge, hindsight-client, mcp-beacon(?), lgrep, codeseek, semble, sia-code, cocosearch, codegraph, octocode
- **pip/pipx**: tldr, yq, pygitwise
- **npm**: hound-search-mcp, nagato-mcp-tools, gitwand-mcp, merge-assist-cli, reconcile-ai, maybe some others
- **go**: some tools may be go-based

### Step 2 — Install Missing
- Categorize output from Step 1
- Install via `sudo pacman -S --needed --noconfirm` for arch packages
- `cargo install` for rust crates (batch where possible)
- `pip install` / `pipx install` for python tools
- `npm install -g` for npm packages
- Handle edge cases: some tools may have different names in repos vs cargo (e.g., `bat` → `bat` in pacman, `batcat` in older distros)

### Step 3 — Optimize Configs
- Check `~/.config/<name>/` for each installed tool
- Enable caching, set threads, tune where applicable (starship, direnv, zoxide, fzf, atuin, etc.)

### Step 4 — MCP Server Registration
- Create `~/.agent/mcp.toml` with all MCP server entries
- Create `~/.mcpproxy/mcp_config.json` with all MCP server entries
- Register: hound-search-mcp, nagato-mcp-tools, mcp-beacon, gitwand-mcp, merge-assist-cli, reconcile-ai (and any others discovered)

### Step 5 — Shell Integration
- Wire into `~/.bashrc.env`: PATH additions, starship init, direnv, zoxide, atuin, fzf, etc.
- Ensure all installed tools are discoverable via PATH

### Step 6 — Document
- Write `/home/toxic/phase1-tools.txt` with every tool's path, version, config path

### Risks & Edge Cases
- Some cargo crates may fail to compile or may not exist under expected names
- `choose`, `semble`, `sia-code`, `codeseek`, `lgrep`, `cocosearch`, `codegraph`, `octocode`, `git-scout`, `hindsight-client`, `tilth`, `seekrs` — need to verify these are real crates/tools
- Some tools may have different package names in AUR vs community
- Cargo installs can be slow; batch them
- `mcp-beacon` could be npm or cargo — need to check
- Tools like `gitpanic` and `git-panic` may be the same tool

### Verification
- Each installed tool: `command -v <tool>` returns path, `<tool> --version` succeeds
- Config files exist and are valid
- `~/.bashrc.env` sources correctly
- MCP config files are valid TOML/JSON

Now let me create the todo items and start executing.
Now executing Step 1 — comprehensive inventory sweep of all tools:The `command` builtin doesn't work via Python subprocess. Let me fix the approach:Let me use Python's `shutil.which` instead:19 installed, 45 missing. Note `ripgrep` binary is `rg`. Let me verify and categorizeGood - `rg` is installed (ripgrep). Now let me categorize and install all missing tools. Starting with pacman and checking for AUR helpersLet me check PATH and then start batch installationsGood - `.local/bin` is in PATH and some tools like `git-panic`, `gitfix`, `gitundo` exist there. Let me re-run a proper inventory then start installing everythingNow I have a clear picture: 23 installed, 43 missing. Let me install everything systematically. Starting with pacman and npmGood progress! bottom was already installed, bandwhich from AUR ✓. Now let me handle npm, pip, and cargo:pygitwise already installed ✓, hound-search-mcp ✓, merge-assist-cli ✓. Now installing cargo crates in batches:Cargo installs are running in background. While they compile, let me set up MCP configs and shell integration, and check some edgeLet me check mcp-beacon and some remaining tools, then proceed with MCP configSome cargo crates installed, many failed. Let me install the real crates that are still missing:
Cargo still compiling. Let me check remaining crates and start MCP/shell work while waiting:Batch 1 done: choose, difftastic, doggo ✓. Batch 2 still compiling. Let me proceed with MCP config and shell integration while waiting
Let me install remaining cargo crates and set up MCP configs in parallel
Let me read existing configs and check what's still compiling:
29 cargo processes still compiling. Let me proceed with MCP config and shell integration while waiting:

Now let me create MCP configs, wire shell integration, and create missing toolMCP configs and shell integration done. Let me check cargo progress and install remaining crates:


Cargo still compiling. Let me optimize existing tool configs and try installing remaining crates
