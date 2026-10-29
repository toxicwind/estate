# Estate peers — post-unsubmodule relocation map (2026-10-28)

Estate is a thin control plane: zero gitlinks (mode 160000), no .gitmodules.
Every product is a standalone peer checkout under products/ (own origin).
Scattered/orphaned content consolidated under products/estate-orphans/.

| old path | current home |
|---|---|
| products/docs-mcp | products/docs-mcp (in place, peer) |
| products/estate-dispersal | products/estate-dispersal (in place, peer) |
| products/estate-dispersal-monolith | products/estate-dispersal-monolith (in place, peer) |
| products/estate-end4 | products/estate-end4 (in place, peer) |
| products/estate-hatch-toolkit | products/estate-hatch-toolkit (in place, peer) |
| products/estate-kappa-plugin | products/estate-kappa-plugin (in place, peer) |
| products/estate-monitor | products/estate-monitor (in place, peer) |
| products/estate-ops | products/estate-ops (in place, peer; canonical ops live at pens/barn/estate-ops) |
| products/estate-recon | products/estate-recon (in place, peer) |
| products/estate-shell | products/estate-shell (in place, peer) |
| products/estate-skills | products/estate-skills (in place, peer) |
| products/estate-skills-hub | products/estate-skills-hub (in place, peer) |
| products/estate-whoa-breakthrough | products/estate-whoa-breakthrough (in place, peer) |
| products/estate-brain | products/estate-brain (in place, peer) |
| config/tau/agent/extensions/hashline-pi | products/estate-orphans/tau-extensions (pi extension configs + source folded) |
| work/tau-extensions | products/estate-orphans/tau-extensions |
| devices/lg-webos | products/estate-orphans/devices/lg-webos |
| packages/theta | removed (empty gitlink pointer, no content) |
| engines/bornite/beellama.cpp | removed (empty gitlink pointer) |
| engines/bornite/ik_llama.cpp | removed (empty gitlink pointer) |
| engines/bornite/llama-cpp-turboquant | removed (empty gitlink pointer) |
| submodules/phone-sentinel | removed (empty gitlink pointer) |
| work/airspeak | removed (empty gitlink pointer) |
