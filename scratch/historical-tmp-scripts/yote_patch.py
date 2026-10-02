import pathlib
p = pathlib.Path("/home/toxic/sovereign/bin/progress-watchdog.py")
t = p.read_text()
old = '    snap["intake_backlog"] = _bl\n    snap["intake_self_from"] = _sf'
new = ('    snap["ledger"]["intake_backlog"] = _bl  # was top-level: left ledger key None\n'
       '    snap["ledger"]["intake_self_from"] = _sf  # which crashed the hatch watchdog')
assert old in t, "anchor not found"
p.write_text(t.replace(old, new))
print("yote patched ok")
