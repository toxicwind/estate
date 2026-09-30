# Star-Killers — the anti-patterns that murder star velocity

Each of these has killed real repos. Check for them during the audit and remove on sight.

## 1. No README / "TODO: write README"
The #1 star-killer. A repo with no README tells the visitor the maintainer doesn't care — so why should they? Fix: even a 20-line README with a one-liner, install command, and example beats nothing.

## 2. No license
Anyone who ships software professionally cannot touch unlicensed code. You've just excluded every enterprise developer from your star pool. Fix: add MIT (or Apache-2.0) — it takes 30 seconds.

## 3. Broken badges
A red CI badge advertises "this is broken." A 404 badge advertises "nobody maintains this." Both are worse than no badges. Fix: audit every badge URL; remove any you can't keep green.

## 4. No demo, no screenshot
The visitor cannot visualize what this does, so they cannot get excited about it. Walls of architecture prose don't excite anyone. Fix: one GIF above the fold. Record it with your actual tool — 30 seconds of effort.

## 5. Install instructions that don't work
The visitor tried your quickstart, it failed, they left, they told nobody. You've lost a star and gained an anti-evangelist. Fix: test the quickstart on a clean machine (or container) exactly as written. Every release.

## 6. Looks dead
No commits in 6+ months, unanswered issues from last year, a roadmap that stops in 2023. The visitor thinks "this will be abandoned when I need it." Fix: the highest-leverage move on a stale repo is a fresh commit + CHANGELOG entry, not a prettier README. Ship something small to prove it's alive.

## 7. README is a wall of text
3000 words before the first code block. The visitor's eyes glaze over at paragraph three. Fix: demo first, prose second. Code blocks early and often. If a section has no code block, question whether it belongs above the fold.

## 8. Jargon-first one-liner
"Leveraging synergistic paradigms for next-gen..." — the visitor has no idea what this does and won't invest 5 minutes to find out. Fix: `[Project] is [what] for [who] that [key benefit]`, plain words.

## 9. Fake stars / engagement gaming
Buying stars, star-for-star rings, bot engagement. Detectable (StarScout measured 4.5M suspected fake stars; the patterns are published), and exposure permanently destroys trust — worse than having few stars honestly. This is the one star-killer that's also an integrity killer. Never.

## 10. All sizzle, no substance
A gorgeous README for a tool that doesn't work, has no tests, and crashes on the happy path. Stars come fast and evaporate faster — and the issues become a graveyard. Fix: the README must not promise what the code can't deliver. CI green is the floor.

## 11. Hostile or absent contribution path
No CONTRIBUTING.md, PRs ignored for months, issues closed without comment. Contributors are your star multipliers — each one brings their network. Fix: CONTRIBUTING.md + answer one issue publicly to show the project welcomes people.

## 12. Name nobody can find
An unsearchable name (`x7q-tool`), a name colliding with a bigger project, or a name with no keywords. GitHub search is how most stars are discovered. Fix: pick a name with at least one searchable keyword for what the thing does.
