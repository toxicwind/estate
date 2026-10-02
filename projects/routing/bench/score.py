#!/usr/bin/env python3
"""Score a bake-off results JSON. Auto-checks run mechanically; manual checks
are printed for rubric scoring by the referee. Usage: score.py <results.json>"""
import json, re, subprocess, sys, tempfile, os

def check_text(rule, text, check):
    t = (text or "").strip()
    if rule == "exact":
        return t == check["value"], f"exact=={check['value']!r}"
    if rule == "exact_ci":
        return t.lower() == check["value"].lower(), f"exact_ci=={check['value']!r}"
    if rule == "contains_any":
        hit = [v for v in check["values"] if v.lower() in t.lower()]
        return bool(hit), f"contains_any hit={hit[:2]}"
    if rule == "starts_with_ci":
        return t.lower().startswith(check["value"].lower()), f"starts_with_ci=={check['value']!r}"
    if rule == "python_fib":
        code = extract_python(t)
        if not code:
            return False, "no python code block found"
        has_doc = '"""' in code or "'''" in code
        ok, detail = run_fib(code)
        return ok and has_doc, f"fib10==55:{ok} docstring:{has_doc} {detail}"
    return None, "unknown rule"

def extract_python(t):
    m = re.search(r"```python\n(.*?)```", t, re.S)
    if m: return m.group(1)
    m = re.search(r"```\n(.*?)```", t, re.S)
    if m and "def " in m.group(1): return m.group(1)
    return t if "def " in t else ""

def run_fib(code):
    prog = code + "\nprint('FIBRESULT:'+str(fib(10) if 'fib' in dir() else fibonacci(10) if 'fibonacci' in dir() else 'NONAME'))\n"
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); path = f.name
        r = subprocess.run(["python3", path], capture_output=True, text=True, timeout=10)
        os.unlink(path)
        m = re.search(r"FIBRESULT:(\S+)", r.stdout)
        if not m: return False, f"no result marker rc={r.returncode} err={r.stderr[:80]}"
        return m.group(1) == "55", f"got {m.group(1)}"
    except Exception as e:
        return False, f"exec fail {str(e)[:80]}"

def main():
    res = json.load(open(sys.argv[1]))
    print(f"# {res['bakeoff']} — {res['startedAt']} → {res.get('finishedAt')}")
    rows = []
    for tr in res["trials"]:
        pid = tr["promptId"]; chk = tr["check"]
        for side in ("tau", "sovereign"):
            s = tr.get(side)
            if s is None: continue
            if side == "tau":
                text = s.get("text"); lat = s.get("serveMs"); extra = f"tier={s.get('tier')} model={s.get('targetModel')} heur={s.get('isHeuristic')} routeMs={s.get('routeMs')}"
                ok_note = s.get("serveError")
            else:
                f = s.get("final") or {}
                text = f.get("text"); lat = f.get("ms"); extra = f"http={f.get('http')} model={f.get('model')} attempts={len(s.get('attempts',[]))}"
                ok_note = f.get("errBody")
            if chk["type"] == "auto":
                passed, detail = check_text(chk["rule"], text, chk)
                status = "PASS" if passed else ("ERROR" if ok_note else "FAIL")
            else:
                status, detail = "MANUAL", chk["rubric"]
            rows.append((pid, side, status, lat, extra, detail, (text or "")[:160].replace("\n", " ")))
    print(f"\n{'prompt':<14}{'side':<10}{'verdict':<8}{'ms':>8}  extra")
    for pid, side, status, lat, extra, detail, _ in rows:
        print(f"{pid:<14}{side:<10}{status:<8}{lat if lat is not None else '-':>8}  {extra} | {detail}")
    print("\n## texts for manual review")
    for pid, side, status, lat, extra, detail, snippet in rows:
        if status in ("MANUAL", "FAIL"):
            print(f"\n### {pid}/{side} [{status}] {detail}\n{snippet}")

if __name__ == "__main__":
    main()
