---
name: fork-check
description: Check (and create if missing) a fork of a GitHub repo.
aliases: [fork]
parameters: [repo, clone_to]
---
Call `gh_fork_state({repo:"{{ repo }}"})`, then `gh_fork_ensure({repo:"{{ repo }}", clone_to:"{{ clone_to }}"})`.
Report the fork path, default branch, and whether it matches upstream.
