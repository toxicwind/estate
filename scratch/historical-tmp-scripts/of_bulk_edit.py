#!/usr/bin/env python3
"""OpenFang audit repairs — precise text edits with assertions. Run on yote."""
import sys

EDIT_LOG = []


def edit(path, old, new, count=1):
    with open(path) as f:
        content = f.read()
    found = content.count(old)
    assert found == count, f"{path}: expected {count}x, found {found}x: {old[:70]!r}"
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    EDIT_LOG.append(f"OK {path}: {old[:50]!r}...")


SOV = "/home/toxic/sovereign"

# ---- config/ports.env (SSOT) ----
edit(
    f"{SOV}/config/ports.env",
    "OPENFANG_PORT=25103",
    "# owner: openfang-front (mesh-front proxy -> :25196 kernel; pitchfork daemons.openfang-front)\nOPENFANG_PORT=25103",
)
edit(
    f"{SOV}/config/ports.env",
    "OPENFANG_API_PORT=25203",
    "# DEPRECATED 2026-09-21 (openfang full audit): :25203 ran a duplicate kernel\n"
    "# sharing the kernel's SQLite DB (double-writer hazard). Retired. The kernel is\n"
    "# OPENFANG_KERNEL_PORT (:25196); the public proxy is OPENFANG_PORT (:25103).\n"
    "# OPENFANG_API_PORT=25203",
)
edit(
    f"{SOV}/config/ports.env",
    "# owner: openfang kernel (pitchfork daemons.openfang, ops/openfang-run.sh)\nOPENFANG_KERNEL_PORT=25196",
    "# owner: openfang kernel (pitchfork daemons.openfang, ops/openfang-run.sh)\n"
    "# Canonical OpenFang map 2026-09-21: :25196 = the ONE kernel (dashboard UI + /v1 + /api);\n"
    "# :25103 (OPENFANG_PORT) = mesh-front proxy; :25203 RETIRED (duplicate kernel); :4200 RETIRED.\n"
    "OPENFANG_KERNEL_PORT=25196",
)

# ---- stack/services/openfang.sh ----
edit(
    f"{SOV}/stack/services/openfang.sh",
    "# Openfang service — Rust binary on OPENFANG_PORT.",
    "# OpenFang public front — mesh-front proxy on OPENFANG_PORT -> OPENFANG_KERNEL_PORT.\n"
    "# (The kernel itself is pitchfork daemons.openfang on :25196 and owns its own\n"
    "# lifecycle via ops/openfang-run.sh. This service never spawns the openfang\n"
    "# binary — see src/services/openfang.ts.)",
)

# ---- stack/services/fleet-power-exporter.ts (stale comment) ----
edit(
    f"{SOV}/stack/services/fleet-power-exporter.ts",
    "// fleet-power-exporter.ts — polls Fleet-Bench :25203/api/power and exposes",
    "// fleet-power-exporter.ts — polls Fleet-Bench /api/power (FLEET_BENCH_PORT env) and exposes",
)

# ---- docs/fleet-knowledgebase.md ----
edit(
    f"{SOV}/docs/fleet-knowledgebase.md",
    "| 4200 (127.0.0.1) | OpenFang kernel daemon |",
    "| 25196 (127.0.0.1) | OpenFang kernel daemon (single instance; dashboard UI + /v1 + /api) |\n"
    "| 25103 | OpenFang mesh-front (public proxy -> :25196 kernel, serves /mesh/* features) |",
)

# ---- docs/CONTROL_PLANE.md ----
edit(
    f"{SOV}/docs/CONTROL_PLANE.md",
    "| OpenFang agents / chat | `:25203` (backend) or `:25103` (mesh-front) |",
    "| OpenFang agents / chat | `:25196` (kernel) or `:25103` (mesh-front) |",
)

# ---- docs/SWAP_OPTIMIZATION.md ----
edit(
    f"{SOV}/docs/SWAP_OPTIMIZATION.md",
    "| **openfang**      | 25103/25203 | Agent kernel web UI",
    "| **openfang**      | 25196/25103 | Agent kernel web UI",
)

# ---- docs/ARCHITECTURE.md ----
edit(
    f"{SOV}/docs/ARCHITECTURE.md",
    "| **openfang**         | 25103/25203 | Rust                | Agent kernel — 206 models, 61 skills, Discord bridge |",
    "| **openfang**         | 25196/25103 | Rust                | Agent kernel — 206 models, 61 skills, Discord bridge |",
)

# ---- projects/yote/.env ----
edit(
    f"{SOV}/projects/yote/.env",
    "# Prefer OF backend :25203 for chat (mesh-front :25103 is fine for /health + /mesh).",
    "# OpenFang canonical 2026-09-21: single kernel on :25196 (chat + /v1 + /api);\n# mesh-front :25103 proxies the same kernel. (:25203 retired — was a duplicate kernel.)",
)
edit(
    f"{SOV}/projects/yote/.env",
    "OPENFANG_URL=http://127.0.0.1:25203",
    "OPENFANG_URL=http://127.0.0.1:25196",
)
edit(
    f"{SOV}/projects/yote/.env",
    "OPENFANG_HEALTH_URL=http://127.0.0.1:25203/api/health",
    "OPENFANG_HEALTH_URL=http://127.0.0.1:25196/api/health",
)

# ---- projects/yote/PLAN.md ----
edit(
    f"{SOV}/projects/yote/PLAN.md",
    "| **OpenFang Backend** | Running on :25203/:25103 | 20+ agents ready (bun) |",
    "| **OpenFang Backend** | Running on :25196 (kernel) / :25103 (mesh-front) | 8 agents running |",
)
edit(
    f"{SOV}/projects/yote/PLAN.md",
    "- [x] Ensure OpenFang is running on :25203 (mesh-backend)\n- [x] Verify :25103 is mesh-front (health/mesh only)",
    "- [x] Ensure OpenFang kernel is running on :25196 (single instance; :25203 retired 2026-09-21)\n- [x] Verify :25103 is mesh-front proxying the :25196 kernel",
)

# ---- projects/shell/ii READMEs ----
for readme in [
    f"{SOV}/projects/shell/ii/README.md",
    f"{SOV}/projects/shell/ii/.github/README.md",
]:
    edit(
        readme,
        "Agent kernel (206 models, 61 skills) — port 25103/25203",
        "Agent kernel (206 models, 61 skills) — port 25196/25103",
    )

# ---- ~/.openfang/config.toml (live, not in repo) ----
edit(
    "/home/toxic/.openfang/config.toml",
    'api_listen = "127.0.0.1:25203"',
    '# Canonical 2026-09-21: the single kernel listens on :25196 (OPENFANG_KERNEL_PORT).\n'
    '# (:25203 retired — was a duplicate kernel on the same DB.)\n'
    'api_listen = "127.0.0.1:25196"',
)

print("\n".join(EDIT_LOG))
print(f"\n{len(EDIT_LOG)} edits applied cleanly")
