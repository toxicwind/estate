#!/usr/bin/env python3
"""Add modelmap-round2 DONE row to fleet KB Active Crews table. Run on yote."""
import sys

p = sys.argv[1] if len(sys.argv) > 1 else '/home/toxic/sovereign/docs/fleet-knowledgebase.md'
s = open(p).read()

row = ("| modelmap-round2 | Model-stack round 2 (Chris: \"Fix all three of those maximally\"): "
       "(1) oracle-judge-local re-entrant shim deadlock -- shim hosted INSIDE llama-swap forwarded to beellama/gemma-96k, "
       "another cmd model; swapper could not swap while shim held the slot (health 200, completions hung 8s -> 502). "
       "Fixed as native llama-swap alias; alias-shim v3.1 hardened (split connect/read timeouts, loud 502s, no-shim-targeting-cmd-models rule). "
       "(2) small/medium/code/long: round-1 'undefined vars' diagnosis was WRONG -- macros defined, gguf on disk, routes 200; "
       "real fault was aliases were worktree-only WIP wiped by an unrelated 06:26 MDT config rewrite -> now committed; "
       "dead beellama-fast dup removed. "
       "(3) Kimi exhaustion: NO free Kimi completes -- OpenRouter removed :free Kimi IDs (404), HF monthly credits depleted (402), "
       "Moonshot 429 billing-suspended (key valid), NIM 410 gone, Pollinations 404, no local weights (1T MoE cannot fit 24GB); "
       "kimi/kimi-k2/kimi-code/kimi-auto fail loudly with genuine upstream status; kimi-auto-shim :25153 TOML-vs-snapshot drift reconciled to the free-Kimi chain. "
       "MONEY ASK: top up Moonshot to restore the genuine direct Kimi route. "
       "| modelmap-round2 (Ember's crew) | DONE (2026-09-21) -- sovereign-projects `bff26f8931` "
       "(judge deadlock fix + alias-shim v3.1) + `35ca8d4855` (tier aliases committed); proofs: judge 10/10 + 3/3 post-restart 200s with exact content, "
       "tiers 4/4 200s real completions post-restart, kimi 4/4 loud 402/404/429; herd + kimi-auto-shim restarted via bin/pitchfork-restart; remote refs ls-remote verified |\n")

anchor = "Retired/completed crews stay listed here with status DONE"
assert anchor in s, 'anchor not found'
assert 'modelmap-round2' not in s, 'row already present'
s = s.replace(anchor, row + "\n" + anchor, 1)
open(p, 'w').write(s)
print('KB row added')
