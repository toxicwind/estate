#!/usr/bin/env python3
"""Nightjar cycle-5 P5 probe: ONE additive log line in herd_chat's
HTTPError branch (oracle_ask.py). Logs Retry-After on HTTP 429 to
stderr with a [nightjar-P5] tag. No behavior change: the exception
flow, dataclasses, and return structure are untouched.

Runs ON awrawr-pc (installed via xfer), never in this cell.
"""
import io
import shutil
import sys

P = '/home/toxic/sovereign/agents/oracle-market/bin/oracle_ask.py'
BAK = P + '.bak-nightjar-p5log'

shutil.copy2(P, BAK)

src = io.open(P, encoding='utf-8').read()
old = (
    '    except urllib.error.HTTPError as e:\n'
    '        try:\n'
    '            ebody = e.read().decode("utf-8", "replace")[:500]\n'
    '        except Exception:\n'
    '            ebody = ""\n'
    '        return {"ok": False,\n'
)
probe_line = (
    '        if e.code == 429: print("[nightjar-P5] herd_chat HTTP 429: '
    'Retry-After=%r" % (getattr(getattr(e, "headers", None), "get", '
    'lambda _h: None)("Retry-After")), file=sys.stderr, flush=True)\n'
)
new = old.replace('        return {"ok": False,\n',
                  probe_line + '        return {"ok": False,\n')

if src.count(old) != 1:
    print('ANCHOR COUNT %d - aborting, restoring from backup' % src.count(old),
          file=sys.stderr)
    shutil.copy2(BAK, P)
    sys.exit(1)

io.open(P, 'w', encoding='utf-8').write(src.replace(old, new))
print('edited OK; backup at %s' % BAK)
