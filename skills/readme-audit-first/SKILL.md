---
name: readme-audit-first
description: "Audit-first README revitalization: verify claims against source, classify NORTH STAR vs SUBSYSTEM, diff only if wrong, preserve provenance tables, separate live bugs"
---

# README Audit-First Revitalization

Method (per user directive):
1. Audit first — open the code/config the README describes; diff every factual claim (ports, line refs, "currently", incident dates) against source. Log mismatch (file + line) before touching prose.
2. Classify: NORTH STAR (top-level system repo) may restructure; SUBSYSTEM (squawk, mesh, agents) patch only. Preserve provenance/incident tables verbatim.
3. Trace every claim to source (file path, line range, test/port, incident seq/date). If unverified, mark "unverified — needs check" — never invent.
4. Output: unified diff per changed file only. If accurate, say so — no busywork.
5. Separate live bugs from doc drift — call out live bugs independently, don't bury in prose.

Key anchors in this workspace: sovereign/README.md verified against pitchfork.toml, config/ports.env (25117 hindsight, 25127 mesh), live curl/bun checks; corrupt 100644 files cleaned as live bug.
