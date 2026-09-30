# nucleosynthesis-oddity

![type](https://img.shields.io/badge/type-research_papers-blue)
![status](https://img.shields.io/badge/status-papers_%2B_proof-green)

> Two research artifacts — a forensic-taxonomy paper and a numerical scale proof — on anomalous-energy claims and the layered stacks that study them. Plus the unbuilt workspace they were exported from.

## The papers

### Strata Debt — a forensic taxonomy of layered artifacts (2026-08-31)

[`artifacts/STRATA_DEBT_UINTA_2026-08-31.md`](./artifacts/STRATA_DEBT_UINTA_2026-08-31.md) (~1,900 words; LaTeX fragment alongside in `.tex.txt`) coins **Strata Debt**: the accumulated superposition of (1) verifiable mechanical reality, (2) operational mythology, (3) incomplete sanitization, and (4) surface documentation across a system's lifespan. Applied to Skinwalker Ranch, AAWSAP, AARO, and the analyst's own container — "the Uinta node, the Pentagon paper trail, the History Channel season, and the analyst's own container are the same class of object."

### Lattice vs nucleosynthesis: scale proof

[`artifacts/lattice_nucleosynthesis_scale_proof.py`](./artifacts/lattice_nucleosynthesis_scale_proof.py) — a numerical scale analysis (numpy / scipy / sympy: binding energies, Coulomb barriers, resonant-lattice concentration estimates) arguing that observed Skinwalker/Uinta energy scales cannot produce new nuclei.

```sh
python3 artifacts/lattice_nucleosynthesis_scale_proof.py
```

## Supporting material

| Path | Contents |
|------|----------|
| [`artifacts/exa/`](./artifacts/exa/) | 25 Exa search-result dumps backing the research (`aaro`, `aawsap`, `coulomb`, `deepq`, …) |
| [`attachments/`](./attachments/) | 6 PNGs, 2 PDFs, county histories, and config backups collected during the research |

## Workspace note

The repo root is a Grok App Builder workspace export (`AGENTS.md`, `src/`, `server/`, `scripts/`, `migrations/`, `.grok/`) — a **template with no app ever scaffolded** (`src/routes/` is absent). It is the export vessel, not the work; the work is in `artifacts/`.
