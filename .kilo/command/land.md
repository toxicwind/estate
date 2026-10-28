---
description: Weave-land this repo onto origin/main with gates
---
Run `weave land --onto origin/main --json --certificate /tmp/kilo/land.json` in the current repo (background it if history is large). Report gate verdict counts (PROVEN/VERIFIED/REFUSED) and the published tip. On refusal, run `weave explain <file>` for each refused file and resolve.
