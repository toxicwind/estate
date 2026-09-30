
import sys
lines = open("docs/fleet-knowledgebase.md").read().splitlines()
row = "| yote-consolidation (ember-ironwright) | Herd FQN + config durability + Telegram delivery (Chris directive) | ember-ironwright (Ember's crew) | DONE (2026-09-21): WS1 FQN regression (sovereign-swap main 61e497ee) + immutable deploy live :25100; bare+FQN 200, incident FQN 200, openfang:coyote 200. WS2: manifest.yaml, estate-reconcile 12/12, real-drift restore, OpenFang SQLite self-heal (0-byte DB found). WS3: sqlite inbox+cursor+dedupe+DLQ live :25102, 44/44 tests, crash-replay PASS, e2e send ok + dupe denied. |"
assert lines[105].startswith("| stall-slayer | Stalled/idle"), lines[105][:50]
lines.insert(106, row)
contract = """
---

## WS2 declared-vs-runtime contract (ferrous-warden, 2026-09-20)

**Declared** (intent -- deploy/manifest.yaml + pitchfork.toml + configs): changes only via
commits or content-hash-gated deploy scripts. A daemon or agent rewriting declared state by
hand is DRIFT, not an edit.

**Runtime** (fact -- process table, /proc/*/exe, paths under runtime_paths in the
manifest): the reconciler reads it, never converges toward it. Daemons write under
runtime_paths freely; those paths are EXEMPT from drift detection by construction.

**Machinery**: deploy/manifest.yaml pins herd (llama-swap 9305f95663db..), herd-keypool,
herd-model-guard, openfang-kernel. bin/estate-reconcile: check/--apply/watch/proc-audit.
ops/openfang-sqlite-check.sh on OpenFang boot: integrity_check + non-empty + schema version,
snapshots (keep 5), atomic self-heal. Configs REPORT-ONLY (shared tree WIP).
"""
content = "\n".join(lines).rstrip("\n") + "\n" + contract
open("docs/fleet-knowledgebase.md","w").write(content)
print("KB-OK lines=%d" % len(content.splitlines()))
