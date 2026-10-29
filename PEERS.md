# Estate peer relocation map

## Rule
Estate is a thin coordinator. Products are **peer standalone checkouts** under
`pens/` (referenced-not-owned). Estate must hold **zero gitlinks (mode 160000)**
and **no `.gitmodules`** (docs/REPO_TOPOLOGY.md, "Rule - no gitlinks").
Previously tracked as orphaned gitlinks with no `.gitmodules` entry; now
untracked peers kept on disk at their new homes.

## Old gitlink path → current home

| Old path | New home | Notes |
|---|---|---|
| `config/tau/agent/extensions/hashline-pi` | `products/estate-orphans/tau-extensions/` | pi extension configs + halfsh code folded here |
| `work/tau-extensions` | `products/estate-orphans/tau-extensions/` | tau-extensions source |
| `packages/theta` | *(removed — empty gitlink pointer)* | no content on disk |
| `engines/bornite/beellama.cpp` | *(removed — empty gitlink pointer)* | no content on disk |
| `engines/bornite/ik_llama.cpp` | *(removed — empty gitlink pointer)* | no content on disk |
| `engines/bornite/llama-cpp-turboquant` | *(removed — empty gitlink pointer)* | no content on disk |
| `submodules/phone-sentinel` | *(removed — empty gitlink pointer)* | no content on disk |
| `work/airspeak` | *(removed — empty gitlink pointer)* | no content on disk |
| `devices/lg-webos` | `products/estate-orphans/devices/lg-webos/` | device profile README |

## Peer products (untracked, kept on disk)
These were real standalone checkouts (`mode 160000` gitlinks with an origin);
the index no longer claims them:
- `products/docs-mcp`
- `products/estate-dispersal`
- `products/estate-dispersal-monolith`
- `products/estate-end4`
- `products/estate-hatch-toolkit`
- `products/estate-kappa-plugin`
- `products/estate-monitor`
- `products/estate-ops`
- `products/estate-recon`
- `products/estate-shell`
- `products/estate-skills`
- `products/estate-skills-hub`
- `products/estate-whoa-breakthrough`
- `products/estate-orphans/` (disparate/orphaned content above)

## Verification
- `git ls-files -s | awk '$1==160000{print}' | wc -l` → 0
- `test -f .gitmodules` → absent
- `git submodule status` → exits 0
- `git check-ignore -q products/docs-mcp` → ignored
- Estate/.gitignore renders `/products/` (regenerated via `ops/bin/gitignore-sync.ts`)
