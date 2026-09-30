#!/usr/bin/env python3
"""tern 2026-09-21: bidder.py bytes fix.

subprocess.TimeoutExpired.stdout/stderr are BYTES (not str) when the
subprocess was opened in binary mode. _redact_text used str regex on
them -> TypeError: cannot use a string pattern on a bytes-like object.
(Observed live on tern-proof-005.)

Fix: decode bytes to str (utf-8, replace errors) at the top of
_redact_text. Also make _canon_ralph_text and the timeout handler
robust: they already expect str, so the decode in _redact_text plus
decoding te.stdout/te.stderr before use covers it.
"""
P = "/home/toxic/sovereign/agents/oracle-market/bin/bidder.py"
src = open(P, encoding="utf-8").read()

old = '''def _redact_text(s):
    """Redact credential-shaped values. 2026-09-21 (tern): timeout
    evidence must never leak secrets into the ledger or workdir."""
    if not s:
        return s
    s = _REDACT_PATTERNS[0].sub(r"\\1[REDACTED]", s)'''
new = '''def _redact_text(s):
    """Redact credential-shaped values. 2026-09-21 (tern): timeout
    evidence must never leak secrets into the ledger or workdir."""
    if not s:
        return s
    if isinstance(s, bytes):
        # 2026-09-21 (tern): TimeoutExpired.stdout/stderr are bytes;
        # decode before regex (was TypeError on tern-proof-005).
        s = s.decode("utf-8", errors="replace")
    s = _REDACT_PATTERNS[0].sub(r"\\1[REDACTED]", s)'''
assert src.count(old) == 1, "redact anchor, got %d" % src.count(old)
src = src.replace(old, new)

with open(P, "w", encoding="utf-8") as f:
    f.write(src)
print("bytes fix OK")
