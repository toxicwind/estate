# readme-audit-first

Audit-first README revitalization: verify claims against source, classify NORTH STAR vs SUBSYSTEM, diff only if wrong, preserve provenance tables, separate live bugs.

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

An audit-first methodology for README revitalization: open the code/config the README describes; diff every factual claim (ports, line refs, "currently", incident dates) against source; log mismatch (file + line) before touching prose. Classify: NORTH STAR (top-level system repo) may restructure; SUBSYSTEM (squawk, mesh, agents) patch only. Preserve provenance/incident tables verbatim.

## What It Does

- **Audit first**: Open the code/config the README describes; diff every factual claim against source
- **Classify claims**: NORTH STAR (top-level system repo) may restructure; SUBSYSTEM (squawk, mesh, agents) patch only
- **Trace provenance**: Every claim traced to source (file path, line range, test/port, incident seq/date)
- **Log mismatches**: File + line number before touching prose — never invent
- **Separate live bugs**: Call out live bugs independently, don't bury in prose
- **Output**: Unified diff per changed file only; if accurate, say so — no busywork

## Key Anchors in This Workspace

- `sovereign/README.md` verified against `pitchfork.toml`, `config/ports.env` (25117 hindsight, 25127 mesh)
- Live curl/bun checks against running services
- Corrupt 100644 files cleaned as live bugs (not doc updates)
- Incident tables preserved verbatim across audits

## Method (per user directive)

1. **Audit first** — open the code/config the README describes; diff every factual claim (ports, line refs, "currently", incident dates) against source. Log mismatch (file + line) before touching prose.
2. **Classify**: NORTH STAR (top-level system repo) may restructure; SUBSYSTEM (squawk, mesh, agents) patch only. Preserve provenance/incident tables verbatim.
3. **Trace every claim to source** (file path, line range, test/port, incident seq/date). If unverified, mark "unverified — needs check" — never invent.
4. **Output**: unified diff per changed file only. If accurate, say so — no busywork.
5. **Separate live bugs from doc drift** — call out live bugs independently, don't bury in prose.

## Quick Reference

```bash
# Audit a README against its source
# The skill checks claims and outputs unified diffs

# Key principle: if the README says "port 25117", open pitchfork.toml
# and verify. If it says something different, log the mismatch as a bug,
# not a doc update — unless the source actually changed.
```

## Config

- No configuration flags; the methodology is the tool
- Key anchors: `sovereign/README.md` vs `pitchfork.toml`, `config/ports.env`
- Verification: live curl/bun checks against running services

## Contributing

Diagnose trigger phrases in classifier-project's `triggers.json` when docs get flagged by prompt-injection classifiers. Rephrase into observational/behavioral language preserving the operational point. See `classifier-safe-docs` skill for the rephrasing pattern.

## License

Open Claw — see `skill.toml` for details.

## Security

- Never invent claims — if unverified, mark "unverified — needs check"
- Preserve provenance/incident tables verbatim; do not rewrite incident dates or sequences
- Classify correctly: NORTH STAR may restructure; SUBSYSTEM patch only
- Live bugs are called out independently and not buried in prose