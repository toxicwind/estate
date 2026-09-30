#!/usr/bin/env python3
"""Nightjar cycle-4, part 2: remaining anchors after the first script
applied 7/10 oracle_ask.py edits before hitting the indent mismatch."""
import sys

ASK = "/home/toxic/sovereign/agents/oracle-market/bin/oracle_ask.py"
TST = "/home/toxic/sovereign/agents/oracle-market/bin/test_oracle_reliability.py"


def replace_once(path, old, new, expect=1):
    with open(path) as f:
        text = f.read()
    n = text.count(old)
    if n != expect:
        print("MISMATCH in %s: anchor found %d times, expected %d:\n%r"
              % (path, n, expect, old[:120]))
        sys.exit(1)
    text = text.replace(old, new)
    with open(path, "w") as f:
        f.write(text)
    print("ok: applied anchor (%r...)" % old[:60].replace("\n", "\\n"))


# same-alias attempt-2, provider-class branch (16-space indent)
replace_once(ASK,
             "                jp = _call(model, t2, 2)\n",
             "                jp = _call_or_skip(model, t2, 2)\n")

# same-alias attempt-2, non-provider branch (12-space indent)
replace_once(ASK,
             "            jp = _call(model, t2, 2)\n",
             "            jp = _call_or_skip(model, t2, 2)\n")

# local fallback
replace_once(ASK,
             "            fb = _call(FALLBACK_JUDGE, 120.0, len(attempts) + 1)\n",
             "            fb = _call_or_skip(FALLBACK_JUDGE, 120.0, len(attempts) + 1)\n")

# slot_info additive key
replace_once(ASK,
             '            "attempts": len(attempts),\n            "budget_skips": budget_skips}\n',
             '            "attempts": len(attempts),\n'
             '            "budget_skips": budget_skips,\n'
             '            "breaker_skips": breaker_skips}\n')

# --- test file: breaker isolation in main() ---
old_main = """def main():
    fns = sorted([v for k, v in list(globals().items())
                  if k.startswith("test_") and callable(v)],
                 key=lambda f: f.__name__)
    for fn in fns:
        try:
            fn()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("FAIL %s raised %r" % (fn.__name__, e))
            FAILURES.append(fn.__name__)
    print("---")
"""
new_main = """def main():
    # P1 (Nightjar cycle-4): isolate the provider circuit breaker from the
    # production state file. This suite deliberately fails stub providers;
    # those failures must neither trip nor read the live breaker.
    _iso = tempfile.mkdtemp(prefix="oracle-breaker-")
    os.environ["JUDGE_BREAKER_PATH"] = os.path.join(
        _iso, "judge-breaker-state.json")
    try:
        fns = sorted([v for k, v in list(globals().items())
                      if k.startswith("test_") and callable(v)],
                     key=lambda f: f.__name__)
        for fn in fns:
            try:
                fn()
            except Exception as e:
                import traceback
                traceback.print_exc()
                print("FAIL %s raised %r" % (fn.__name__, e))
                FAILURES.append(fn.__name__)
    finally:
        shutil.rmtree(_iso, ignore_errors=True)
    print("---")
"""
replace_once(TST, old_main, new_main)

print("PART 2 APPLIED")
