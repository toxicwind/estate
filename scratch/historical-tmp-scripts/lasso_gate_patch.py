import sys

path = "/storage/.kodi/addons/plugin.video.redlight/resources/lib/service.py"
with open(path) as f:
    src = f.read()

# Already patched?
if "_meta_account_active" in src:
    print("ALREADY PATCHED")
    sys.exit(0)

# Backup
with open(path + ".pre-lasso-gate.bak", "w") as f:
    f.write(src)
print("backup written")

# 1. Insert the gate functions before "class RedLightMonitor(Monitor):"
gate_code = '''def _meta_account_active(provider):
\t"""Fail-open gate: True unless we can prove no account is configured."""
\ttry:
\t\tfrom modules.settings import (
\t\t\ttrakt_user_active, simkl_user_active,
\t\t\tmdblist_user_active, punchplay_user_active,
\t\t)
\t\tchecks = {
\t\t\t"trakt": trakt_user_active,
\t\t\t"simkl": simkl_user_active,
\t\t\t"mdblist": mdblist_user_active,
\t\t\t"punchplay": punchplay_user_active,
\t\t}
\t\treturn bool(checks[provider]())
\texcept Exception:
\t\treturn True

def _start_meta_monitor(provider, monitor_cls, monitor):
\tif _meta_account_active(provider):
\t\t_start_daemon(lambda: monitor_cls().run(monitor))
\telse:
\t\tkodi_utils.logger("Red Light", "%s Service Skipped - no account configured" % monitor_cls.__name__)


class RedLightMonitor(Monitor):'''

old_class = "class RedLightMonitor(Monitor):"
assert src.count(old_class) == 1, "class anchor not unique"
src = src.replace(old_class, gate_code, 1)

# 2. Swap the four unconditional monitor starts for gated ones
swaps = [
    ("\t\t_start_daemon(lambda: TraktMonitor().run(self))",
     "\t\t_start_meta_monitor(\"trakt\", TraktMonitor, self)"),
    ("\t\t_start_daemon(lambda: SimklMonitor().run(self))",
     "\t\t_start_meta_monitor(\"simkl\", SimklMonitor, self)"),
    ("\t\t_start_daemon(lambda: MdblistMonitor().run(self))",
     "\t\t_start_meta_monitor(\"mdblist\", MdblistMonitor, self)"),
    ("\t\t_start_daemon(lambda: PunchPlayMonitor().run(self))",
     "\t\t_start_meta_monitor(\"punchplay\", PunchPlayMonitor, self)"),
]
for old, new in swaps:
    assert src.count(old) == 1, "swap anchor not unique: %r" % old[:40]
    src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

# Syntax check
import py_compile
py_compile.compile(path, doraise=True)
print("PATCHED OK + syntax valid")
