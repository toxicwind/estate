# 34k-apis — recon of the api-evangelist org

Recon project on the **api-evangelist** GitHub org (34,531 public repos). The
name: a recon *of api-evangelist specifically* — not a generic
scanner.

## What this recon found

api-evangelist is an **API-surface index**, not a product org:

- **~34.4k (~99.4%) are per-company API-surface dumps** — described
  *"Company profile (portfolio lead)"* / *"independent third-party profile of a
  public API surface"*. Batch-generated, alphabetical, low signal. Filter:
  `grep -viE 'company profile|third-party profile of a public api'`.
- **~a few dozen tooling/metadata repos** — the actual machinery:

| repo | ★ | deeplink |
| --- | --- | --- |
| `public-apis` | 57 | https://github.com/api-evangelist/public-apis |
| `api-evangelist-network` | 46 | https://github.com/api-evangelist/api-evangelist-network |
| `posts` | 3 | https://github.com/api-evangelist/posts (16y blog → REST+MCP) |
| `apis-io` | 3 | https://github.com/api-evangelist/apis-io |
| `unified-apis` | 0 | https://github.com/api-evangelist/unified-apis |
| `monitoring` | 0 | https://github.com/api-evangelist/monitoring (SyntheticCheck schema) |
| `observability` | 1 | https://github.com/api-evangelist/observability |
| `nvidia-nim` | 1 | https://github.com/api-evangelist/nvidia-nim (openapi + rate-limits) |
| `nvidia` | 0 | https://github.com/api-evangelist/nvidia |

## Probing link to Rhodochrosite

Rhodochrosite vendors the probing-relevant subset as **submodules** under
`pens/geode/products/rhodochrosite/reference/`: `nvidia-nim`, `nvidia`, `monitoring`,
`observability`. The merged prober (`proxy/tools/probe-catalogs.ts`) consumes
them (rate limits + SyntheticCheck schema).

## Analysis (dataframe)

`bun analyze.ts [N]` collects `N` repos (default 600) into a dataframe-js
`DataFrame`, classifies each dump vs tooling, and writes `out/findings.json` +
`out/catalog.csv`. First measured sample (1500 repos): **1491 dumps / 9
tooling** — confirming the org is ~99.4% surface dumps.

## Trust caveat

api-evangelist `rate-limits.yml` are stale **May-2026 `method: generated`**
stubs (even after `git submodule update --remote`). Treat as advisory; the
authoritative limit signal is **live 429 `Retry-After`**.
