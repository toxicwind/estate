# Estate memory system — "make it ours" integration design (tau, 2026-11-02)

## The 4 estate pieces (proven ground truth)

| Lane | What it is | Status (verified 2026-11-02) |
|------|------------|------------------------------|
| **hindsight** | Remote memory daemon backend (`memory.backend=hindsight`, apiUrl/apiToken keys) | LIVE (memory backend) |
| **qdrant** | Vector store :25133, 1024-dim cosine collections (cosmic_disclosure etc.) | LIVE (anomaly #79 dim gate) |
| **freeinference bge-m3** | Embedding model via freeinference.org/v1 (1024-dim) | **PROVEN LIVE 200** (this session; the "embed key invalid" claim was a red herring) |
| **sharpshooter** | Decision-memory backend (in-process, per-project decision files) | LIVE — **substring search only today** |

## The flaw the architect flagged (design truth)

- `memory.backend` selects ONE backend; mnemotau's embed keys were **condition-gated to mnemotauActive**
- With hindsight active, the **in-process local embed lane (mnemotau's) is dead weight** — hindsight embeds server-side, invisibly
- Sharpshooter search does substring matching; no semantic rank

## Integration design (estate-owned, both agents, full pens)

1. **Sharpshooter gains bge-m3 semantic search** — its OWN ungated keys
   (`sharpshooter.embeddingModel/ApiUrl/ApiKey`, added to schema this session),
   backed by freeinference bge-m3 (keyring-SSOT), substring fallback.
   → decision memory becomes semantic, offline-capable, in-process.

2. **Qdrant becomes the shared vector surface** — the 1024-dim collections
   (cosmic_disclosure, estate_sweep) get a kappa/tau-neutral write path via the
   proven cosmic ingest lane (ops e1fc150) so BOTH agents' decision/artifact
   memories share one index.

3. **hindsight stays the recall brain** — but its client-side recall budget can
   layer the same freeinference bge-m3 for query expansion (estate-owned key).

4. **kappa mirror** — kappa has no advisor/memory backend today; the kappa arc
   mirrors: same `memory.backend` contract, same bge-m3 keyring key, qdrant
   client against the same collections.

5. **pens ecosystem** — the embed lane is already estate-wide SSOT via
   secretsmith (FREEINFERENCE_API_KEY); typo-fix (9748634) + cosmic ingest
   (9f7fb4d) are the first consumers; sharpshooter search is the next.

## Landed this session (already committed/pushed)
- `sharpshooter.embedding*` schema keys (tau)
- semantics-search module + TDD test (tau, pending wire)
- tau config `mnemoni` embed keys → freeinference bge-m3 (config.yml)
- dead provider cleanup (models.yml, model-router → fcb78beee9/f00961e783/98c7b78dc8)
- cosmic-local-ingest + cosmic-search (ops e1fc150/9f7fb4d)

## Deferred (needs architect pick)
- kappa mirror scope (backend contract parity)
- qdrant collection naming for shared agent memory
- hindsight client-side query-expansion enable flag