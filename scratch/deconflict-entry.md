
## 2026-09-14 ~12:39 MDT - main leader -> fleet: model-audit deconfliction (Chris: "Collision? Fix it")

Two model-audit efforts are running in parallel and both touch tau engine KDLs:
- main-chat worker 819d89b0 (Chris-ordered): fleet-wide model audit + switch to faster models, INCLUDING tau engine KDL pins. Already briefed to coordinate with the tau repair worker (pull --ff-only, build on top, no clobber).
- 0fcb5f23 side-chat model-speed worker: local audit + latency benchmark + claude shim default.

DECISION: tau engine KDLs (sovereign-projects/tau — auth/nvidia.kdl, providers/nvidia.kdl, any other model pins) are OWNED by main-chat worker 819d89b0. The side-chat model-speed worker must NOT edit tau KDLs — read-only there. Side worker keeps: latency benchmarks (read-only) and the claude bun shim default. If pushes conflict, pull --ff-only and re-apply; KDL owner wins ties. No other file overlaps expected.
