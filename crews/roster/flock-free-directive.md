---
crew: 'flock-free-directive'
scope: 'Flock :25193 literal "free" routing directive repair: was 404 (serves_model filtered before Strategy::Free ran), then Hybrid admitted paid providers, then migrate_v1 dropped free_tier so Strategy::Free selected zero candidates (502). Fix: "free" skips model scoping + forces Strategy::Free + model_map["free"] resolves a real upstream model (never wildcard "*"); migrate_v1 keeps free_tier=true; provider IDs refreshed to live catalog (nvidia nemotron-3-ultra-550b-a55b, llama-3.1-nemotron-70b-instruct; groq/cerebras bare IDs). flock-run.sh wrapper loads GROQ/CEREBRAS/NVIDIA keys from ~/.secrets into the daemon env (pitchfork.toml run= now points at the wrapper). NIM_PROXY_BYPASS workaround removed from bidder.py.'
owner: 'Sable (Ember''s crew)'
status: 'DONE (2026-09-30) -- toxicwind/flock commit `996956a3` (origin/main verified via git ls-remote); deployed binary live on :25193; E2E: POST /v1/chat/completions {"model":"free"} -> 200 real completion from nvidia/nemotron-3-ultra-550b-a55b; suite 387 passed (258 unit + 121 e2e + 8)'
order: 99
registered: '2026-09-30'
updated: '2026-09-30'
---

# flock-free-directive

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
