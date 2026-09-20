# Stash-safe maximalization of tau work

Goal ID: goal_0b019dab0b8a
Goal slug: stash-safe-maximalization-of-tau-work

## Description
Maximal continuation of the recent tau repo consolidation: a coordinator is inventorying every git repo on awrawr-pc for stashes, unpushed commits, and dirty worktrees, pushing at-risk work to safe backup branches. A second worker is archiving sovereign-scripts, sovereign-skills, sovereign-swap, sovereign-zed, and omp-extensions into sovereign-projects/tau/archive/ with blob-level dedup. All deletions are held until the stash audit completes.
