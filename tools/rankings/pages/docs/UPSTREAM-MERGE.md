# Upstream merge — the process, not just the result

Roundup is a fork of [`vllm-project/guidellm`](https://github.com/vllm-project/guidellm).
This file is the record of **how** upstream changes get in, because the fork's
history is the thing we are protecting and the process is what protects it.

If you are about to sync from upstream, read this end to end first.

## The two locations, and why both exist

| Location | Holds | Why |
|---|---|---|
| `https://github.com/toxicwind/roundup` | the fork's **real git history** + the `upstream` remote | the only place a merge can actually happen |
| `ranch/roundup/fork/` | 525 tracked files, 18 MB, vendored **in-tree** | the working copy the benchmarks import |

`fork/` is not a nested repository — it is real tracked files in the
`toxicwind/ranch` monorepo, so a fresh clone of the ranch gets the benchmark
tool with no second checkout and no submodule dance. That is the whole reason
the code is duplicated rather than symlinked or submoduled.

The duplication is not drift. It is **a build artefact of the merge**, and
`scripts/upstream-merge.sh` is what keeps the two in step.

There is currently **no standalone checkout of `toxicwind/roundup` on this
box** — only the GitHub remote. To merge, clone it somewhere first.

## The rules

1. **Never rewrite the fork's history.** No rebase of our commits, no squash,
   no force-push to `main`. The four commits below are the audit trail; the
   2026-09-20 audit cites them by hash and that citation must keep resolving.
2. **Merge upstream into the fork with a merge commit.** When upstream takes
   our PRs and we pull their changes back, it is a merge — not a rebase. The
   histogram has to show that both sides happened.
3. **One PR per upstreamable commit**, cut from a branch at the fork HEAD.
   Never from `main`.
4. **PRs to `vllm-project/guidellm` are Chris's call.** They speak as
   toxicwind to an external maintainer group. Agents audit and prepare; they
   do not open.
5. **Record every merge.** Append the decision block to `fork/MERGE-DECISIONS.md`.
   A merge with no recorded decision is a merge we will not be able to explain.

## Current state (audit of 2026-09-20, still the reference)

- **Fork HEAD:** `6b40c21e251a5095a7ae8064a6603a3f2c4b6d32`
- **Upstream HEAD at audit:** `4601968d8a06ffc1aecce987753da1118ea637a0`
- **Delta:** `git log 4601968d..6b40c21e` — 4 commits, full messages, no squashes

| # | Commit | What it adds | Upstreamable |
|---|---|---|---|
| 1 | `74ec8623` | Pluggable response-quality scoring; `guidellm/benchmark/scoring/` with the `instruction_following` scorer (exact/contains). Touches `benchmarker.py`, `entrypoints.py`, `schemas/{accumulator,base,benchmark}.py` | yes — additive, self-contained |
| 2 | `bb96157f` | HF tokenizer load failures split into auth / missing-revision / network instead of one opaque exception (+142-line test) | yes — pure error taxonomy |
| 3 | `99540b90` | Empty output scores `0.0` rather than skipping; scorer exceptions record `0.0` with error metadata; `score_details` persisted | yes, with discussion |
| 4 | `6b40c21e` | Quality aggregates cover **completed** requests only (per-request scores still recorded for every terminal request) | yes, as a pair with #3 |

Commits #3 and #4 encode our judgment about what counts as a measurement
versus a skip *in our benchmark runs*. That is a real disagreement waiting to
happen upstream, which is why they go together in one PR.

### Why nothing was pushed upstream yet

1. Outward action — Chris's decision, not an agent's.
2. #3–#4 are harness-specific tuning; a PR needs that debate, not a drive-by.
3. No urgency. The fork serves our benchmarks today; nothing is lost by waiting.

## Last recorded merge

`fork/MERGE-DECISIONS.md`:

```
Processed: true
Resulting commit: 74b05b3683179f29b8da2f305ab30011d3babc33
Tag: refs/recovery/maximal-merge
```

## Procedure

```bash
# 1. clone the fork somewhere writable (it is NOT on this box)
git clone https://github.com/toxicwind/roundup ~/roundup-standalone
cd ~/roundup-standalone

# 2. wire and fetch upstream
git remote add upstream https://github.com/vllm-project/guidellm
git fetch upstream

# 3. see exactly what we would be taking
git log --oneline HEAD..upstream/main | head -50
git diff --stat HEAD upstream/main | tail -20

# 4. merge — never rebase our four commits away
git merge upstream/main          # merge commit, resolve, do not squash

# 5. record the decision before pushing anything
#    append to fork/MERGE-DECISIONS.md:
#      Processed: true
#      Resulting commit: <new sha>
#      Tag: refs/recovery/maximal-merge-<date>

# 6. verify the four originals survived
git log --oneline | grep -E '74ec8623|bb96157f|99540b90|6b40c21e'

# 7. sync the in-tree copy so the benchmarks run the merged code
./scripts/upstream-merge.sh --sync-into
```

## What the audit doc gets wrong

`docs/upstream-audit-guidellm-2026-09-20.md` calls `fork/`
"Local working copy (**git-ignored**, benchmark runs)". That is **stale**.
`git ls-files fork` returns **525 tracked files** — `fork/` is committed to
the ranch monorepo on purpose, which is the entire reason it can be vendored.
Treat the audit as accurate about commits and wrong about tracking.