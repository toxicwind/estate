---
crew: 'modelmap-round2'
scope: 'Model-stack round 2 (Chris: "Fix all three of those maximally"): (1) oracle-judge-local re-entrant shim deadlock -- shim hosted INSIDE llama-swap forwarded to beellama/gemma-96k, another cmd model; swapper could not swap while shim held the slot (health 200, completions hung 8s -> 502). Fixed as native llama-swap alias; alias-shim v3.1 hardened (split connect/read timeouts, loud 502s, no-shim-targeting-cmd-models rule). (2) small/medium/code/long: round-1 ''undefined vars'' diagnosis was WRONG -- macros defined, gguf on disk, routes 200; real fault was aliases were worktree-only WIP wiped by an unrelated 06:26 MDT config rewrite -> now committed; dead beellama-fast dup removed. (3) Kimi exhaustion: NO free Kimi completes -- OpenRouter removed :free Kimi IDs (404), HF monthly credits depleted (402), Moonshot 429 billing-suspended (key valid), NIM 410 gone, Pollinations 404, no local weights (1T MoE cannot fit 24GB); kimi/kimi-k2/kimi-code/kimi-auto fail loudly with genuine upstream status; kimi-auto-shim :25153 TOML-vs-snapshot drift reconciled to the free-Kimi chain. MOONSHOT STOOD DOWN 2026-09-21 (eclipse, Chris: no top-up, ever): chat completions -> exceeded_current_quota_error (suspended, insufficient balance; key itself valid, /v1/models 200). Peer parked in herd.yaml; kimi route names re-pointed at the free-Kimi chain.'
owner: 'modelmap-round2 (Ember''s crew)'
status: 'DONE (2026-09-21) -- sovereign-projects `bff26f8931` (judge deadlock fix + alias-shim v3.1) + `35ca8d4855` (tier aliases committed); proofs: judge 10/10 + 3/3 post-restart 200s with exact content, tiers 4/4 200s real completions post-restart, kimi 4/4 loud 402/404/429; herd + kimi-auto-shim restarted via bin/pitchfork-restart; remote refs ls-remote verified'
order: 60
registered: '2026-09-21'
updated: '2026-09-29'
---

# modelmap-round2

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
