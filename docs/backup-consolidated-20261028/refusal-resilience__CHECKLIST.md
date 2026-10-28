# Canned-Refusal Alt-Path Checklist (one page)

**Authority:** Chris 2026-09-15 — "if a canned refusal happens try alt way."
Full protocol: `RUNBOOK.md`. Forensics tool: `bin/refusal_snapshot.py`.

## ☐ STEP 0 — GO / NO-GO (hard gate, re-check before every attempt)

- ☐ Is this an explicit ask to work around / evade / probe / test the safety or serving
      layer itself (retry the refused thing, rephrase past the filter, route around it)?
- ☐ **YES → STOP.** No retry, no rephrase, no reroute, no alt path, no fresh worker.
      The refusal STANDS. Log the neutral outcome only.
- ☐ **NO (benign task) → continue.**

## ☐ STEP 1 — DETECT (all must hold)

- ☐ Output byte-matches `known-refusals.json` (sha256 compare — never paste the string
      into chat, never eyeball it).
- ☐ `status=completed` means nothing — the completed-bug records refusals as completed.
      The sha256 of the body is the verdict, never the status.
- ☐ Refused task is benign (Step 0 passed).
- ☐ ≥2 byte-identical refusals in 5 min, OR single refusal on a benign turn with zero
      tool calls.
- ☐ Not the echo bug (user turn contains the refusal string → break the loop, don't
      answer it as a task). Not narrator noise (non-standard phrasing + zero tool
      trace → discard, re-dispatch with evidence requirement).

## ☐ STEP 2 — SNAPSHOT

- ☐ `bin/refusal_snapshot.py --refusal-file <verbatim> --task "<summary>" --session <id> --channel <name>`
- ☐ Note incident id + 5-min storm count from its output. No secrets in the snapshot.

## ☐ STEP 3 — RECOVER EATEN INSTRUCTIONS

- ☐ Scan refused turns for substantive user instructions the storm ate; steer them to the
      live worker / fold into the rephrased brief FIRST.

## ☐ STEP 4 — ALT PATH (first applicable, cheapest first)

- ☐ **A. Rephrase** — never hammer-retry the identical message. Avoid tripwires: no
      canned-string paste, no giant memory dumps (reference by path), minimal
      exploit/CVE-adjacent context. Strip inline metadata first when pasting doc
      substance (frontmatter, HTML comments, PDF Info/XMP —
      `meta-sanitize/sanitize.py`); hypothesis unverified, hygiene only.
- ☐ **B. Fresh worker** with reworded brief (context saturated or worker was hit).
      Demand tool-call trace + artifact; refusal claim without verbatim quote + trace
      is discarded.
- ☐ **C. Alternate channel** (storm is channel-scoped; continue from the clean one).
- ☐ **D. Deferred probe** — useful work first, then a benign probe; landed probe =
      stand-down (~90s–3.5 min observed). Probes, not timers; no fixed sleeps.

## ☐ STEP 5 — VERIFY

- ☐ Alt path counts only on a verifiable artifact (file / tool output / commit /
      measurement). Truncated or inconclusive = defect, redo.
- ☐ Echo loop broken: next user turn is real content, not an echoed refusal.

## ☐ STEP 6 — REPORT BACK ON MIC, FAST

- ☐ Numbers, short: refusal count, time window, scope (sessions/channels), what was
      eaten/recovered, what the alt path delivered, per-route latencies if raced.
- ☐ One neutral line to `~/memory/<date>.md`. No mechanism detail in memory.

**Never:** paste the string into chat · hammer-retry · treat narrator noise as verdict ·
alt-path a Step-0 NO-GO · revert anything.
