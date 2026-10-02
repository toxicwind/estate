# README Revitalization Plan — Shrew audit-first

## Context
NORTH STAR (sovereign/README.md) verified 10/10 claims vs pitchfork.toml, config/ports.env, live services (:25100 up, :25117/:25127 up), session evidence — 0 mismatches; no diff needed. SUBSYSTEM (squawk, mesh, oracle-market) accurate per user directive, unchanged. Only live bug separate: corrupt 100644: files from old worktree dirs (cleaned, verified PASS).

## Approach
1. Audit NORTH STAR: claims vs pitchfork.toml lines, ports.env keys (HINDSIGHT_API_PORT=25117, MCP_PROXY_PORT=25127), mise.toml, running herd/tau/shep. Log mismatches file+line.
2. Audit SUBSYSTEM READMEs (hatch/agents/ember/, projects/mesh/, agents/, tools/): open described code, diff claims (cadence, ports, line numbers). Accurate → unchanged; wrong → unified diff only.
3. Classify: NORTH STAR may restructure top-thesis opening (system purpose before folder refs, per squawk model); SUBSYSTEM patch only.
4. Preserve provenance/incident tables verbatim unless factually wrong.
5. Traceable claims: file path + line range + test/result/incident date. Unverified → "needs check", not asserted.
6. Flag doc/code mismatches that are live bugs separately (already done: 100644 cleanup).

## Critical files & anchors
- /home/toxic/estate/README.md (NORTH STAR — verified accurate)
- /home/toxic/estate/pitchfork.toml (service definitions, port group SSOT)
- /home/toxic/estate/config/ports.env (port SSOT — 25117 hindsight, 25127 mesh)
- /home/toxic/estate/docs/fleet-knowledgebase.md (required reading, estate map)
- /home/toxic/estate/hatch/agents/ember/docs/ + projects/mesh/README.md (SUBSYSTEM — spot-check only)

## Verification
- bun helpers/estate-scanner.ts → PASS (0 broken bin, /tmp/estate-verify-2.jsonl)
- bun helpers/health-audit.ts --json → 6/19 UP (/tmp/tau-audit-verify.json; hindsight UP :25117, mesh UP :25127)
- echo '{"jsonrpc":"2.0","id":1,"method":"initialize"...}' | bun sovereign-mcp-server.ts → RESPONDED (/tmp/mcp-verify.jsonl)
- fclones group + dedupe across projects/sovereign/cold-storage (~4.8 GB, 18,078 files)
- Worktrees: only /home/toxic/estate; backup/wt-* preserved; 32 stale removed

## Assumptions
- User wants only real mismatches changed; accurate docs untouched.
- SUBSYSTEM READMEs accurate per directive; skip if audit finds none.
- New consolidation claims point to /tmp/estate-verify-2.jsonl, fclones output, or git worktree list.
