# Original User Request

## Initial Request — 2026-06-18T12:10:02-06:00

Consolidate every sovereign-related folder on the system into `/home/toxic/sovereign`, init a clean git repo, stage everything properly, trim the openfang agent fleet of duplicates, and delete all legacy junk — without losing anything of value.

Working directory: /home/toxic/sovereign
Integrity mode: development

---

## Context (read before acting)

- `/home/toxic/sovereign` is the **live, running stack** — sovereign-engine.service is active. Do NOT touch `process-compose.yaml`, `bin/llama-server`, or any running process configs.
- `/home/toxic/sovereign-clean` is already a symlink → `/home/toxic/sovereign`. Remove the symlink only, do not delete the target.
- Git was just initialized: `git init` was already run in `/home/toxic/sovereign`. There is no remote yet.
- The openfang agent config lives in `~/.openfang/agents/` (not inside sovereign). Deleting agent dirs there removes them from openfang on next reload.
- `gh` CLI is authenticated as toxicwind.

---

## Requirements

### R1. Merge Valuable Content from Other Dirs into /home/toxic/sovereign

Pull in anything useful before deleting source dirs. Specifically:

**From `/home/toxic/sovereign_temp_cleanup/`:**
- `config/hands/` → `sovereign/config/hands/` (HAND.toml configs for coder, orchestrator, diagnostic, security-auditor, browser, researcher, arbitrage_monitor + SKILL.md files + any SHARED_SOVEREIGN_WEB_FIRST_RULES.md)
- `Caddyfile` → `sovereign/Caddyfile`
- `config/openfang/EMERGENT_VLLM_PLAN.md` → `sovereign/docs/EMERGENT_VLLM_PLAN.md`
- `yote/logs.py` → `sovereign/yote/logs.py` (only if not already present)

**From `/home/toxic/sovereign_temp_cleanup/agents/` — do NOT copy full repos, just document remotes:**
- Create `sovereign/docs/submodules.md` listing all related git repos with their remote URLs:
  - greprip: https://github.com/toxicwind/greprip.git
  - club-3090: https://github.com/noonghunna/club-3090.git
  - openfang (fork): https://github.com/toxicwind/openfang.git | origin: https://github.com/RightNow-AI/openfang.git
  - ouroboros (fork): https://github.com/toxicwind/ouroboros-desktop.git | origin: https://github.com/joi-lab/ouroboros-desktop.git
  - playwright-mcp (from sovereign-maximal): https://github.com/microsoft/playwright-mcp.git (check actual remote)

**From `/home/toxic/sovereign-iterator/`:**
- `skill.md` → `sovereign/docs/sovereign-iterator-skill.md`

**Remove symlink only:**
- `rm /home/toxic/sovereign-clean` (it's a symlink, not a real dir)

### R2. Initialize a Clean Git Repo in /home/toxic/sovereign

1. Write a comprehensive `.gitignore` covering: `logs/`, `pids/`, `__pycache__/`, `*.pyc`, `*.pt`, `*.gguf`, `.pixi/`, `scratch/`, `artifacts/`, `nfcot_flow*.pt`, `nfcot_flow*.bad.*`, `*.log`, `context_results_*.json`, `canonical_benchmark_*.json`, `bin/llama-server`, `bin/*.log`, `llama.log`, `main.log`
2. `git add -A`
3. `git commit -m "feat: sovereign stack — initial consolidated commit"`
4. Create a new **private** GitHub repo and push: `gh repo create toxicwind/sovereign --private --source=. --remote=origin --push`

### R3. Delete All Legacy Sovereign Junk

After R1 merge is confirmed complete, delete these:

**Giant files/dirs (free up ~40GB+):**
- `/home/toxic/sovereign_recon_20260521_180846.txt` (16G)
- `/home/toxic/sovereign_full_20260521_180607.txt` (7.7G)
- `/home/toxic/sovereign-maximal/` (20G)
- `/home/toxic/sovereign_array.old/` (4.8G)
- `/home/toxic/sovereign_temp_cleanup/` (5.3G — only AFTER R1 merge confirmed)
- `/home/toxic/sovereign-backup-20260612-230520/` (394M)
- `/home/toxic/sovereign-backup-20260612.tar.gz` (15M)

**Old experiment dirs:**
- `/home/toxic/sovereign-iterator/` (after merge)
- `/home/toxic/final_sovereign_20260525_010948/`
- `/home/toxic/gayxxx-sovereign/`
- `/home/toxic/gayxxx-sovereign-1779685196/`
- `/home/toxic/rebuild_gayxxx-sovereign_1779687029/`
- `/home/toxic/rebuild_gayxxx-sovereign_1779688238/`
- `/home/toxic/rebuild_gayxxx-sovereign_1779689422/`
- `/home/toxic/sovereign_cleanup_backup_1779353431/`
- `/home/toxic/sovereign_cleanup_backup_1779353614/`
- `/home/toxic/sovereign_code_aware_backup_1779356206/`
- `/home/toxic/sovereign_final_backup_1779355978/`
- `/home/toxic/sovereign_final_backup_1779356041/`
- `/home/toxic/sovereign_audit_1779158458/`
- `/home/toxic/sovereign_control_center/`
- `/home/toxic/sovereign-scan-devenv/`

**Junk txt/jsonl/zip files in /home/toxic:**
- `sovereign_keys_broad_20260521_180253.txt`
- `sovereign_keys_broad_20260521_180306.txt`
- `sovereign_clean.jsonl`
- `sovereign_keys_20260521_180144.txt`
- `sovereign_secrets_20260521_175937.txt`
- `sovereign_audit_20260608_082944.txt`
- `sovereign_glassbox_repair.jsonl`
- `sovereign_glassbox_repair.jsonl.txt`
- `sovereign_monolith_from_scratch.sh`
- `sovereign_monolith_from_scratch.zip`
- `sovereign_v2_final_maximal_meta_fixer-1.zip`
- `maximal-sovereign-forger.jsonl.txt`
- `before_sovereign_audit_20260608_083142.txt`

### R4. Consolidate Openfang Agents (44 → ~20)

Delete these agent dirs from `~/.openfang/agents/` (redundant/bloat):
- `coder` (superseded by coder-max)
- `orchestrator` (superseded by orchestrator-max)
- `diagnostic` (superseded by diagnostic-max)
- `security-auditor` (superseded by security-auditor-max)
- `doc-writer` (same as writer — keep writer, remove doc-writer)
- `devops-lead` (same as ops)
- `data-scientist` (same as analyst)
- `code-reviewer` (same as debugger)
- `hello-world`
- `health-tracker`
- `travel-planner`
- `recruiter`
- `legal-assistant`
- `customer-support`
- `social-media`
- `email-assistant`
- `personal-finance`
- `home-automation`
- `meeting-assistant`
- `sales-assistant`
- `translator`

**Keep:** assistant, aria, sage, coder-max, orchestrator-max, diagnostic-max, security-auditor-max, solidity-security-auditor, architect, researcher, analyst, debugger, planner, ops, arbitrage-monitor, browser-hand, lead-hand, collector-hand, predictor-hand, researcher-hand, writer

After deleting agents, trigger openfang reload by sending SIGHUP or restarting via process-compose:
```
process-compose --unix-socket /tmp/process-compose.sock process restart openfang 2>/dev/null || true
```

---

## Acceptance Criteria

### Consolidation
- [ ] `/home/toxic/sovereign/config/hands/` exists with HAND.toml files inside
- [ ] `/home/toxic/sovereign/Caddyfile` exists
- [ ] `/home/toxic/sovereign/docs/submodules.md` exists listing all referenced git repos
- [ ] `/home/toxic/sovereign/yote/logs.py` exists
- [ ] `/home/toxic/sovereign-clean` symlink is GONE

### Git Clean
- [ ] `git -C /home/toxic/sovereign status` shows clean working tree
- [ ] `git -C /home/toxic/sovereign log --oneline -1` shows the initial commit
- [ ] `git -C /home/toxic/sovereign remote -v` shows origin pointing to github.com/toxicwind/sovereign
- [ ] `gh repo view toxicwind/sovereign` succeeds

### Cleanup (disk space reclaimed)
- [ ] `ls /home/toxic/ | grep -E "^sovereign" | grep -v "^sovereign$"` returns nothing (or only the .jsonl/.txt files if they haven't been cleaned yet)
- [ ] `df -h /home` shows at least 30GB freed vs before

### Openfang
- [ ] `ls ~/.openfang/agents/ | wc -l` outputs ≤ 22
- [ ] `curl -s http://127.0.0.1:25004/api/health` returns status ok
- [ ] Agent count via API ≤ 22

### Stack Still Running (critical)
- [ ] `curl -s http://127.0.0.1:25008/health | grep ok` passes
- [ ] `curl -s http://127.0.0.1:25004/api/health | grep ok` passes
- [ ] `systemctl --user is-active sovereign-engine.service` returns active
