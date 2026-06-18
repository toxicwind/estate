# COORD — Live Agent Coordination File
# All agents: read this before every action. Update STATUS when done.
# Use minimal tokens. Act, don't narrate.

## RULES
- No asking for permission. Just do it.
- Check STATUS before starting a task — don't double-do.
- Update STATUS immediately when you start/finish.
- Think in <50 tokens. Act in shell commands.
- If stuck >2min on anything, skip and move to next task.

## TASK BOARD

### BLOCK A — MERGE (Explorer 1 owns)
- [x] git init /home/toxic/sovereign  ← already done
- [ ] A1: cp -r /home/toxic/sovereign_temp_cleanup/config/hands /home/toxic/sovereign/config/hands
- [ ] A2: cp /home/toxic/sovereign_temp_cleanup/Caddyfile /home/toxic/sovereign/Caddyfile
- [ ] A3: mkdir -p /home/toxic/sovereign/docs && cp /home/toxic/sovereign_temp_cleanup/config/openfang/EMERGENT_VLLM_PLAN.md /home/toxic/sovereign/docs/
- [ ] A4: cp /home/toxic/sovereign_temp_cleanup/config/hands/*/SHARED_SOVEREIGN_WEB_FIRST_RULES.md /home/toxic/sovereign/docs/ 2>/dev/null || true
- [ ] A5: cp /home/toxic/sovereign_temp_cleanup/yote/logs.py /home/toxic/sovereign/yote/logs.py 2>/dev/null || true
- [ ] A6: cp /home/toxic/sovereign-iterator/skill.md /home/toxic/sovereign/docs/sovereign-iterator-skill.md 2>/dev/null || true
- [ ] A7: Write /home/toxic/sovereign/docs/submodules.md (see SUBMODULES section below)
- [ ] A8: rm /home/toxic/sovereign-clean  ← symlink only

### BLOCK B — GIT (Explorer 1 owns, after A done)
- [ ] B1: Write /home/toxic/sovereign/.gitignore (see GITIGNORE section below)
- [ ] B2: git -C /home/toxic/sovereign add -A
- [ ] B3: git -C /home/toxic/sovereign commit -m "feat: sovereign stack — initial consolidated commit"
- [ ] B4: gh repo create toxicwind/sovereign --private --source=/home/toxic/sovereign --remote=origin --push

### BLOCK C — DELETE JUNK (Explorer 2 owns, run in parallel with A/B)
Delete in this order — biggest first for max disk free:
- [ ] C1: rm -f /home/toxic/sovereign_recon_20260521_180846.txt  (16G)
- [ ] C2: rm -f /home/toxic/sovereign_full_20260521_180607.txt  (7.7G)
- [ ] C3: rm -rf /home/toxic/sovereign-maximal/  (20G)
- [ ] C4: rm -rf /home/toxic/sovereign_array.old/  (4.8G)
- [ ] C5: rm -rf /home/toxic/sovereign-backup-20260612-230520/  (394M)
- [ ] C6: rm -f /home/toxic/sovereign-backup-20260612.tar.gz
- [ ] C7: rm -rf /home/toxic/final_sovereign_20260525_010948/ /home/toxic/gayxxx-sovereign/ /home/toxic/gayxxx-sovereign-1779685196/ /home/toxic/rebuild_gayxxx-sovereign_1779687029/ /home/toxic/rebuild_gayxxx-sovereign_1779688238/ /home/toxic/rebuild_gayxxx-sovereign_1779689422/
- [ ] C8: rm -rf /home/toxic/sovereign_cleanup_backup_1779353431/ /home/toxic/sovereign_cleanup_backup_1779353614/ /home/toxic/sovereign_code_aware_backup_1779356206/ /home/toxic/sovereign_final_backup_1779355978/ /home/toxic/sovereign_final_backup_1779356041/ /home/toxic/sovereign_audit_1779158458/ /home/toxic/sovereign_control_center/ /home/toxic/sovereign-scan-devenv/
- [ ] C9: rm -f /home/toxic/sovereign_keys_broad_20260521_180253.txt /home/toxic/sovereign_keys_broad_20260521_180306.txt /home/toxic/sovereign_clean.jsonl /home/toxic/sovereign_keys_20260521_180144.txt /home/toxic/sovereign_secrets_20260521_175937.txt /home/toxic/sovereign_audit_20260608_082944.txt /home/toxic/sovereign_glassbox_repair.jsonl /home/toxic/sovereign_glassbox_repair.jsonl.txt /home/toxic/sovereign_monolith_from_scratch.sh /home/toxic/sovereign_monolith_from_scratch.zip /home/toxic/sovereign_v2_final_maximal_meta_fixer-1.zip /home/toxic/maximal-sovereign-forger.jsonl.txt /home/toxic/before_sovereign_audit_20260608_083142.txt
- [ ] C10: rm -rf /home/toxic/sovereign-iterator/ /home/toxic/sovereign_temp_cleanup/  ← LAST, only after A block confirmed done

### BLOCK D — OPENFANG AGENTS (Explorer 2 owns, parallel with C)
Delete these dirs from ~/.openfang/agents/:
coder orchestrator diagnostic security-auditor doc-writer devops-lead data-scientist code-reviewer hello-world health-tracker travel-planner recruiter legal-assistant customer-support social-media email-assistant personal-finance home-automation meeting-assistant sales-assistant translator

- [ ] D1: cd ~/.openfang/agents && rm -rf coder orchestrator diagnostic security-auditor doc-writer devops-lead data-scientist code-reviewer hello-world health-tracker travel-planner recruiter legal-assistant customer-support social-media email-assistant personal-finance home-automation meeting-assistant sales-assistant translator
- [ ] D2: Restart openfang: process-compose --unix-socket /tmp/process-compose.sock process restart openfang 2>/dev/null || pkill -f "openfang start" && sleep 3 && /home/toxic/.openfang/bin/openfang start &
- [ ] D3: Verify: curl -s http://127.0.0.1:25004/api/health

## SUBMODULES (for A7)
```
# Sovereign Related Git Repos

## Active Forks (toxicwind)
- openfang: fork=https://github.com/toxicwind/openfang.git origin=https://github.com/RightNow-AI/openfang.git
- ouroboros: fork=https://github.com/toxicwind/ouroboros-desktop.git origin=https://github.com/joi-lab/ouroboros-desktop.git
- greprip: https://github.com/toxicwind/greprip.git
- playwright-mcp: https://github.com/microsoft/playwright-mcp.git

## Reference Only
- club-3090 (benchmarks): https://github.com/noonghunna/club-3090.git
```

## GITIGNORE (for B1)
```
logs/
pids/
__pycache__/
*.pyc
*.pt
*.gguf
.pixi/
scratch/
artifacts/
nfcot_flow*.pt
nfcot_flow*.bad.*
*.log
context_results_*.json
canonical_benchmark_*.json
bin/llama-server
bin/*.log
llama.log
main.log
.env
```

## STATUS (update as you go)
```
A1: done
A2: done
A3: done
A4: done
A5: done
A6: done
A7: done
A8: done
B1: done
B2: done
B3: done
B4: pending
C1: DONE
C2: DONE
C3: DONE
C4: DONE
C5: DONE
C6: DONE
C7: DONE
C8: DONE
C9: DONE
C10: waiting-for-BLOCK_A_DONE
D1: DONE
D2: DONE (health=ok v0.6.9)
D3: DONE (44 agents)
```
