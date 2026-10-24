# Recon: `api-evangelist` (34,531 public repos)

Recon project on the **API Evangelist** GitHub org. Filed under
`estate/docs/recon/api-evangelist/`. Co-owned by Hodos (the merged router
consumes the probing-relevant subset as submodules under
`pens/olympus/products/hodos/reference/`).

## The account, at scale

| metric           | value                                                            |
| ---------------- | ---------------------------------------------------------------- |
| org              | [`github.com/api-evangelist`](https://github.com/api-evangelist) |
| created          | 2012-12-12 (16+ years of API-blogging)                           |
| **public_repos** | **34,531**                                                       |
| shape            | an **API-surface index**, not a product org                      |

**Two layers:**

1. **~34.5k "profile" repos** — per-company API-surface dumps, all described as
   _"independent third-party profile of a public API surface, by API Evangelist."_
   Batch-generated, alphabetical (the newest dumps are dated 2026-10-24).
   **Low signal.** Filter these out of any probing/tooling search with:
   `grep -viE 'company profile|third-party profile of a public api'`.
2. **~a few dozen tooling / metadata repos** — the actual machinery: the
   central index, the 16-year blog-as-API, unified-API tracking, and the
   probing library we consume. **These are the interesting ones.**

## The tooling layer (deeplinks + recency)

Actively maintained (pushed 2026-10-23/24):

| repo                     | ★   | deeplink                                                 | what it is                                                 |
| ------------------------ | --- | -------------------------------------------------------- | ---------------------------------------------------------- |
| `public-apis`            | 57  | https://github.com/api-evangelist/public-apis            | public API catalog (mirror of public-apis index)           |
| `api-evangelist-network` | 46  | https://github.com/api-evangelist/api-evangelist-network | the whole network index                                    |
| `posts`                  | 3   | https://github.com/api-evangelist/posts                  | 16 years of posts exposed as **one REST API + MCP server** |
| `apis-io`                | 3   | https://github.com/api-evangelist/apis-io                | the **central APIs.io index**                              |
| `unified-apis`           | 0   | https://github.com/api-evangelist/unified-apis           | index of **unified API service/tooling repos**             |
| `nvidia-nim`             | 1   | https://github.com/api-evangelist/nvidia-nim             | NVIDIA NIM surface + `openapi/` + rate-limits _(pulled)_   |
| `nvidia`                 | 0   | https://github.com/api-evangelist/nvidia                 | broader NVIDIA surface + rate-limits _(pulled)_            |
| `monitoring`             | 0   | https://github.com/api-evangelist/monitoring             | **probe schemas** (SyntheticCheck) _(pulled)_              |
| `observability`          | 1   | https://github.com/api-evangelist/observability          | observability tooling index _(pulled)_                     |

Metadata/schema tooling (smaller, but relevant): `interface-research`,
`schemathesis`, `schemasure`, `schema-validation`, `database-schema-design`,
`json-schema`, `commons`.

## Probing relevance (why we pulled 4 of them)

The merged Hodos prober (`hodos/proxy/tools/probe-catalogs.ts`) consumes these
vendored submodules:

| submodule       | path                      | role in probing                                               |
| --------------- | ------------------------- | ------------------------------------------------------------- |
| `nvidia-nim`    | `reference/nvidia-nim`    | NIM API surfaces (`openapi/*`), **rate limits**, capabilities |
| `nvidia`        | `reference/nvidia`        | NVIDIA limits / llms / broader surface                        |
| `monitoring`    | `reference/monitoring`    | canonical **`SyntheticCheck`** JSON schema for prober output  |
| `observability` | `reference/observability` | observability tooling index                                   |

## Audit / trust caveats

- **Rate limits are NOT trustworthy.** Both `rate-limits.yml` files are
  self-declared `method: generated` / `generated: '2026-05-25'` (a May-2026
  snapshot). Even after `git submodule update --remote` (remote synced
  2026-10-23), these stubs were **never regenerated**. Mark as advisory; the
  authoritative signal is the **live 429 `Retry-After`** hodos already emits.
- **The profile-dump mass is noise** for probing. Only the ~9 tooling repos
  matter; the 34.5k company dumps are a search-index catalog, not tooling.
- The OpenAPI **surface** schemas (`nvidia-nim/openapi/*`) are current
  (synced 2026-10-23) and usable; the **limit figures** are the stale part.

## Ownership status

- Branches from other forks: hodos vendors these as **git submodules** under
  `reference/`. Forking to `toxicwind/*` for ownership was **blocked on the
  stale GitHub credential** (`gh repo fork` → `401 Bad credentials`) — retry
  after `gh auth refresh -h github.com`.

## Reference

- Org API: `https://api.github.com/orgs/api-evangelist` (public_repos 34531).
- Repo list sorted by recent: `?sort=pushed&per_page=40` (all company dumps).
- Probing filter: `grep -viE 'company profile|third-party profile of a public api'`.
