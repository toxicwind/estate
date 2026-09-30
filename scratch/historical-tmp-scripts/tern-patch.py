#!/usr/bin/env python3
"""tern 2026-09-21: oracle-market bidder.py timeout-evidence fix.

1. _run_super_ralph() TimeoutExpired handler: preserve bounded, redacted
   partial output (stdout/stderr carried by the exception + node-state
   summary from the workflow DB) into partial-output.txt; record in
   ralph-invocation.txt; return the partial summary (clearly marked) as
   `out` instead of empty output. success stays False -- a timeout is not
   a result, but it is no longer silent.
2. Honest narration: the bidder's local success is not the oracle's
   verdict -- stop saying "verified clean".
Run on yote: /usr/bin/python3 tern-patch.py
"""
import re
import sys

P = "/home/toxic/sovereign/agents/oracle-market/bin/bidder.py"
src = open(P, encoding="utf-8").read()

def rep(old, new, expect=1):
    global src
    n = src.count(old)
    assert n == expect, "expected %d of %r, found %d" % (expect, old[:60], n)
    src = src.replace(old, new)

# --- 1. module helpers, inserted after ERR_CAP -----------------------------
helpers = '''OUT_CAP = 8000
ERR_CAP = 2000
PARTIAL_CAP = 65536  # bound for the on-disk partial-output evidence file


# ---- timeout evidence preservation (2026-09-21: tern) ----
# A super-ralph timeout used to discard everything: the TimeoutExpired
# handler returned empty output, so finished nodes' work vanished and the
# task settled "no-result / empty-output". Preserve bounded, redacted
# partial evidence instead -- graceful degradation, never silent loss.
def _redact_text(s):
    """Redact credential-shaped values. Conservative: value replaced,
    key name kept so the shape of the output stays readable."""
    if not s:
        return s
    pats = [
        (r"(?i)(api[_-]?key|apikey)\\s*[:=]\\s*[\\"']?([^\\s\\"\\n]+)",
         r"\\1=[REDACTED]"),
        (r"(?i)\\b(bearer)\\s+([A-Za-z0-9\\-._~+/=]{8,})",
         r"\\1 [REDACTED]"),
        (r"(?i)(token|secret|password|passwd|pwd)\\s*[:=]\\s*[\\"']?"
         r"([^\\s\\"\\n]+)", r"\\1=[REDACTED]"),
        (r"\\bsk-[A-Za-z0-9]{16,}", "sk-[REDACTED]"),
        (r"\\bhf_[A-Za-z0-9]{16,}", "hf-[REDACTED]"),
    ]
    for pat, sub in pats:
        s = re.sub(pat, sub, s)
    return s


def _canon_ralph_text(s):
    """Super Ralph's headless stdout may carry literal "\\n" escapes
    instead of real newlines. Canonicalize before hash/sign/post so the
    acceptance parser (and humans) see real text. Only when no real
    newlines exist, to avoid corrupting mixed or legitimately-backslashed
    output."""
    if "\\\\n" in s and "\\n" not in s:
        s = (s.replace("\\\\r\\\\n", "\\n").replace("\\\\n", "\\n")
              .replace("\\\\t", "\\t"))
    return s


def _summarize_ralph_nodes(workdir):
    """Best-effort node-state summary from the super-ralph workflow DB.
    Returns e.g. 'nodes: 12 finished / 2 pending / 1 in-progress (15
    total)' or '' when the DB is absent/unreadable. Never raises."""
    try:
        import sqlite3
        from pathlib import Path
        db = None
        for cand in Path(workdir).glob(".super-ralph/**/workflow.db"):
            db = cand
            break
        if db is None:
            return ""
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        try:
            rows = con.execute(
                "SELECT state, COUNT(*) FROM _smithers_nodes GROUP BY state"
            ).fetchall()
        finally:
            con.close()
        if not rows:
            return ""
        states = {r[0]: r[1] for r in rows}
        total = sum(states.values())
        parts = ["%d %s" % (states[k], k)
                 for k in ("finished", "in-progress", "pending") if k in states]
        extra = [k for k in states if k not in ("finished", "in-progress",
                                                "pending")]
        parts += ["%d %s" % (states[k], k) for k in extra]
        return "nodes at timeout: %s (%d total)" % (", ".join(parts), total)
    except Exception:
        return ""

'''
rep("OUT_CAP = 8000\nERR_CAP = 2000\n", helpers)

# --- 2. use the canonicalizer in the normal path (dedup) -------------------
old_norm = '''            out = (p.stdout or "")[-OUT_CAP:]
            # Super Ralph's headless stdout may carry literal "\\n"
            # escapes instead of real newlines. Canonicalize before
            # hash/sign/post so the acceptance parser (and humans) see
            # real text. Only when no real newlines exist, to avoid
            # corrupting mixed or legitimately-backslashed output.
            if "\\\\n" in out and "\\n" not in out:
                out = (out.replace("\\\\r\\\\n", "\\n").replace("\\\\n", "\\n")
                          .replace("\\\\t", "\\t"))
            err = (p.stderr or "")[-ERR_CAP:]'''
new_norm = '''            out = _canon_ralph_text((p.stdout or "")[-OUT_CAP:])
            err = (p.stderr or "")[-ERR_CAP:]'''
rep(old_norm, new_norm)

# --- 3. timeout handler: preserve evidence ----------------------------------
old_to = '''        except subprocess.TimeoutExpired:
            dur = (time.time() - t0) * 1000
            out, success = "", False
            err = "super-ralph timeout after %.0fs" % ceiling'''
new_to = '''        except subprocess.TimeoutExpired as te:
            # 2026-09-21 (tern): NEVER discard partial evidence on timeout.
            # TimeoutExpired carries the output captured before the kill;
            # finished nodes' progress also lives in the workflow DB.
            # Preserve it bounded + redacted instead of returning empty.
            dur = (time.time() - t0) * 1000
            success = False
            timed_out = True
            part_out = _redact_text((te.stdout or "") or "")
            part_err = _redact_text((te.stderr or "") or "")
            node_summary = _summarize_ralph_nodes(workdir)
            chunks = []
            if node_summary:
                chunks.append(node_summary)
            if part_out.strip():
                chunks.append("--- partial stdout (last %d bytes) ---\\n%s"
                              % (PARTIAL_CAP, part_out[-PARTIAL_CAP:]))
            if part_err.strip():
                chunks.append("--- partial stderr (truncated) ---\\n%s"
                              % part_err[-ERR_CAP:])
            (workdir / "partial-output.txt").write_text(
                "\\n\\n".join(chunks) if chunks
                else "(no partial output captured before timeout)",
                encoding="utf-8")
            # The no-result path carries the partial summary -- clearly
            # marked so nobody mistakes it for a completed result.
            out_full = ("[PARTIAL - super-ralph timed out after %.0fs; "
                        "full evidence in partial-output.txt]\\n" % ceiling)
            if node_summary:
                out_full += node_summary + "\\n"
            out = _canon_ralph_text(out_full + part_out)[-OUT_CAP:]
            err = ("super-ralph timeout after %.0fs; partial evidence "
                   "preserved in partial-output.txt" % ceiling)
            if part_err.strip():
                err = (err + "\\n" + part_err)[-ERR_CAP:]'''
rep(old_to, new_to)

# --- 4. ralph-invocation.txt records timeout + evidence ---------------------
old_inv = '''        # Invocation evidence for the audit trail (also a result artifact).
        (workdir / "ralph-invocation.txt").write_text(
            "bin: %s\\nmodel: %s\\nbase_url: %s\\nceiling_s: %.0f\\n"
            "exit: %s\\nduration_ms: %.1f\\n"
            % (RALPH_BIN, ralph_model, RALPH_BASE_URL, ceiling,
               rc, dur),
            encoding="utf-8")'''
new_inv = '''        # Invocation evidence for the audit trail (also a result artifact).
        (workdir / "ralph-invocation.txt").write_text(
            "bin: %s\\nmodel: %s\\nbase_url: %s\\nceiling_s: %.0f\\n"
            "exit: %s\\nduration_ms: %.1f\\ntimed_out: %s\\n"
            "partial_evidence: %s\\n"
            % (RALPH_BIN, ralph_model, RALPH_BASE_URL, ceiling,
               rc, dur, timed_out,
               "partial-output.txt" if timed_out else "n/a"),
            encoding="utf-8")'''
rep(old_inv, new_inv)

# timed_out must exist on the non-timeout paths too
old_rc = '''        tid = task["task_id"]
        prompt = task.get("payload", "") or ""
        (workdir / "prompt.md").write_text(prompt, encoding="utf-8")
        rc = None'''
new_rc = '''        tid = task["task_id"]
        prompt = task.get("payload", "") or ""
        (workdir / "prompt.md").write_text(prompt, encoding="utf-8")
        rc = None
        timed_out = False'''
rep(old_rc, new_rc)

# --- 5. honest narration: local success is not the oracle's verdict ---------
rep("verified clean. Another one for the wall.",
    "output posted, awaiting oracle verdict.")
# generic voice: drop the bare "verified" claim
n_generic = src.count('done in {d:.0f}s — verified. ')
assert n_generic == 1, "generic done_ok count %d" % n_generic
src = src.replace('done in {d:.0f}s — verified. ',
                  'done in {d:.0f}s — output posted, awaiting oracle verdict. ')

with open(P, "w", encoding="utf-8") as f:
    f.write(src)
print("bidder.py patched OK")
