#!/usr/bin/env python3
"""tern 2026-09-21: post_task.py --exec-mode support."""
P = "/home/toxic/sovereign/agents/oracle-market/bin/post_task.py"
src = open(P, encoding="utf-8").read()

old_args = '    ap.add_argument("--payload-file", required=True)\n    ap.add_argument("--from", dest="frm", default="ember")'
new_args = ('    ap.add_argument("--payload-file", required=True)\n'
            '    ap.add_argument("--from", dest="frm", default="ember")\n'
            '    ap.add_argument("--exec-mode", default="python",\n'
            '                    help="execution mode: python (default) or super-ralph")')
assert src.count(old_args) == 1, "args anchor"
src = src.replace(old_args, new_args)

old_body = ('        "bid_window_ms": args.bid_window_ms,\n'
            '        "timeout_ms": args.timeout_ms,\n'
            '        "posted_ts": time.time(),\n'
            '    }')
new_body = ('        "bid_window_ms": args.bid_window_ms,\n'
            '        "timeout_ms": args.timeout_ms,\n'
            '        "exec_mode": args.exec_mode,\n'
            '        "posted_ts": time.time(),\n'
            '    }')
assert src.count(old_body) == 1, "body anchor"
src = src.replace(old_body, new_body)

with open(P, "w", encoding="utf-8") as f:
    f.write(src)
print("post_task.py patched OK")
