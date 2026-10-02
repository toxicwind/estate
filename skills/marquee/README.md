# marquee

Make any GitHub repo impossible to ignore — audit and maximalize it for stars at a hardcore level. Use this skill when the user says "star grade", "make this repo pop", "GitHub stars", "marquee", "make this presentable", "polish this repo", or wants a repo audited/fixed for public appeal. Also use when preparing any repo for public release, open-sourcing internal code, or when a repo looks dead/bare and needs the full treatment. Covers: README that hooks in 10 seconds, repo metadata (description/topics/social preview/license), docs structure, runnable examples, CI badges, contributing guide, issue/PR templates, and the star-killers to avoid. Do NOT use for private/internal repos that will never be public, or for gaming stars artificially (fake stars are detectable and destroy trust).

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

Transforms a GitHub repo into a star-maximizing presentation. Every instruction serves the 10-second verdict: within 10 seconds of landing, a visitor decides "this is useful AND alive AND I trust it." Borrows patterns from the highest-starred README/template repos on GitHub (`othneildrew/Best-README-Template` 16k⭐, `matiassingers/awesome-readme` 21k⭐) and grounds everything in research: stars+forks+mentions form the "interest" factor in open-source health models, and fake-star gaming is detectable (StarScout — 4.5M suspected fake stars measured). This skill does legitimate maximalization only.

## What It Does

- **10-second rule**: Hook (what is this), proof (show me it working), trust (is it alive and maintained) — in that order. Everything above the fold serves the hook; everything below serves proof and trust.
- **Audit-first workflow**: Run the audit script, fix in priority order, verify, then ship
- **Priority order**: First 5 items decide the 10-second verdict; everything after compounds it. Do not polish section 12 while section 1 is broken.
- **Repo presentation covers**: README that hooks in 10 seconds, repo metadata (description/topics/social preview/license), docs structure, runnable examples, CI badges, contributing guide, issue/PR templates, social preview image (1280×640), CHANGELOG.md

## Workflow

```
1. Audit → 2. Fix in priority order → 3. Verify → 4. Ship
```

### Step 1: Audit

Run the audit script against the target repo:

```bash
python3 ~/workspace/skills/marquee/scripts/marquee-audit.py /path/to/repo
```

It checks every item in `references/audit-checklist.md` and reports PASS/FAIL with specific gaps. Read the full checklist before fixing — the priority order matters.

### Step 2: Fix in priority order

Work the checklist top-down. The first 5 items decide the 10-second verdict; everything after compounds it. Do not polish section 12 while section 1 is broken.

1. **README exists and hooks** — see `references/readme-anatomy.md`
2. **License file present** — no license = no enterprise stars, period
3. **One-line description + topics** — see `references/repo-metadata.md`
4. **Demo above the fold** — GIF, screenshot, or asciinema; no demo = no excitement
5. **Quickstart that works** — copy-paste to first success in < 30 seconds
6. **CI badge green** — a red or missing badge reads as "abandoned"
7. **Docs beyond README** — `docs/` for depth, examples that run
8. **Contributing guide** — lowers the bar for the PRs that become stars
9. **Issue/PR templates** — `.github/ISSUE_TEMPLATE/`, `PULL_REQUEST_TEMPLATE.md`
10. **Social preview image** — 1280×640, what shows in link unfurls
11. **CHANGELOG.md** — signals the project is alive and maintained
12. **Star-killers removed** — see `references/star-killers.md`

### Step 3: Verify

Re-run the audit script. Every item should PASS. Then do the 10-second test yourself: open the README fresh and time how long until you understand what it does, see it working, and trust it. If any of those three takes more than 10 seconds, keep fixing.

### Step 4: Ship

Commit with a clear message (`docs: marquee star-grade pass`), push, and verify the GitHub repo page renders correctly (badges load, images resolve, links work). GitHub caches social previews — if you change it, the old one lingers for days, so get it right the first time.

## Principles

**The 10-second rule.** A visitor decides in 10 seconds. Hook (what is this), proof (show me it working), trust (is it alive and maintained). In that order. Everything above the fold serves the hook; everything below serves proof and trust.

**Show, don't tell.** A demo GIF beats three paragraphs. A runnable example beats a demo GIF. A one-command quickstart beats a runnable example. Climb that ladder as far as the project allows.

**Badges are trust signals, not decoration.** Every badge must be live and green. A red CI badge is worse than no badge — it advertises brokenness. A badge that 404s advertises carelessness. Audit every badge URL.

**Borrow, don't invent.** The README structures in `references/readme-anatomy.md` are borrowed from repos with 16k+ stars. They work. Customize the content, not the architecture.

**Never game stars.** Buying stars, star-for-star schemes, or fake engagement are detectable (StarScout, 4.5M suspected fake stars measured) and permanently destroy trust when exposed. This skill maximalizes legitimate appeal — the product and presentation earn stars, nothing else.

**Alive beats perfect.** Recent commits, a maintained CHANGELOG, and answered issues signal "this project is alive" louder than perfect docs on a dead repo. If the repo looks abandoned, the highest-leverage fix is a fresh commit, not a prettier README.

## Reference Files

Read the relevant reference based on what you're fixing — don't load them all:

- `references/readme-anatomy.md` — the full README structure, section by section, with the borrowed 16k⭐ template anatomy
- `references/repo-metadata.md` — description, topics, social preview, license selection, website link
- `references/community-files.md` — CONTRIBUTING.md, Code of Conduct, issue/PR templates, funding
- `references/star-killers.md` — the anti-patterns that murder star velocity, and why each one does
- `references/audit-checklist.md` — the full runnable checklist the audit script implements

## License

Open Claw — see `skill.toml` for details.

## Security

- Do NOT use for private/internal repos that will never be public
- Do NOT use for gaming stars artificially (fake stars are detectable and destroy trust when exposed)
- This skill maximalizes legitimate appeal — the product and presentation earn stars, nothing else
- If the repo looks abandoned, the highest-leverage fix is a fresh commit, not a prettier README