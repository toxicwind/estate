#!/bin/bash
set -e
SRC=/home/toxic/sovereign
DST=/tmp/sp-salvage
cd "$DST"
git fetch -q origin
git reset -q --hard origin/main
echo "BASE=$(git rev-parse --short origin/main)"
FILES="projects/mesh/bin/landing.py projects/tau/engine/packages/coding-agent/src/cli/startup-cwd.ts projects/tau/upstream-changes/scripts/ingest.sh projects/yote/PLAN.md ops/nginx/nginx.conf projects/bridge/bin/bg-ctl.py projects/openrouter-probe/e2e-probe.py projects/openrouter-probe/rewire_peer_v3.py"
for f in $FILES; do
  mkdir -p "$(dirname "$f")"
  cp "$SRC/$f" "$f"
  git add "$f"
done
git -c user.name=ember -c user.email=ember@hatch commit -q -m "sweep: salvage crew work stranded in stale nim-probe-20260920 tree

Rescues genuinely-new content from the /home/toxic/sovereign +
/home/toxic/projects/sovereign-projects twins (both stuck on
nim-probe-20260920, 324 behind main; working trees byte-identical,
so the duplicate checkout contributed nothing extra). Each file was
verified: working-tree blob differs from BOTH branch HEAD and
origin/main (i.e. not stale drift, not already landed).

- projects/mesh/bin/landing.py: env-driven ports (MESH_LANDING_PORT,
  AWR_MCP_PORT, BRIDGE_EXEC_PORT, GEMINI_MCP_PORT); no more hardcoded 8443
- projects/tau/engine/.../startup-cwd.ts: disable auto-chdir to tmp dirs,
  stay in CWD unless --cwd given
- projects/tau/upstream-changes/scripts/ingest.sh: SOV_TMP export ordering fix
- projects/yote/PLAN.md: openfang kernel :25196, :25203 retired 2026-09-21
- ops/nginx/nginx.conf: managed-source nginx config (pitchfork nginx daemon)
- projects/bridge/bin/bg-ctl.py: offset-based tail + job listing for bridge-bg
- projects/openrouter-probe/e2e-probe.py: GuideLLM e2e probe tooling
- projects/openrouter-probe/rewire_peer_v3.py: v3 openrouter-free rewire tool

Deliberately excluded: hatch/agents/*/var+state (runtime), *.pid/*.lock,
rust_algo_web build assets, probe result JSON/logs (ephemeral data),
33MB upstream-18.2.8.patch (regenerable from upstream mirror),
pitchfork.toml/README/mise.toml/ports.env local drift (stale vs main;
pitchfork needs the careful live reconciliation, not a blind commit),
openfang config deletions (tied to gutted-tree work, out of scope),
doc deletions at root (unverifiable intent), projects/AURKA (nested .git)."
SHA=$(git rev-parse HEAD)
echo "COMMIT=$SHA"
git push origin main 2>&1 | tail -2
echo "== verify =="
git ls-remote origin main
