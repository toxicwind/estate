"""Port exact-PID supervised restart into yote's deploy-cell.py (v2: span replace)."""
import sys

p = "/home/toxic/sovereign/projects/bridge/hatch/deploy-cell.py"
s = open(p).read()

if "def stop_connector_exact" not in s:
    helpers = open("/tmp/deploy_helpers.py").read()
    assert "def stop_connector_exact" in helpers
    anchor = "def main():\n    no_restart ="
    assert s.count(anchor) == 1, "main anchor"
    s = s.replace(anchor, helpers + "\n\n" + anchor)
    print("helpers inserted")
else:
    print("helpers already present")

# Replace the whole span from the old print to the start-block comment.
start = s.find('print("Restarting connector...")')
end = s.find("# Start new detached (PPID 1, own SID).")
assert start > 0 and end > start, "span anchors"
new_span = '''print("Restarting connector (supervised: supervise-connector.py wraps connector.py and classifies the next death)...")
        # Exact-PID stop only: no pkill -f, no loose pgrep. A loose pattern
        # once SIGTERMed the live production connector (2026-09-21); the pid
        # file is trusted only when /proc/<pid>/cmdline + cwd verify.
        stop_connector_exact()
        import time
        time.sleep(2)
        '''
s = s[:start] + new_span + s[end:]
assert 'bash", "-c", "pkill' not in s and 'bash", "-c", "pgrep' not in s, "loose kill patterns remain"

old_start = '''        # Start new detached (PPID 1, own SID).
        # Use Popen with start_new_session + all fds redirected; do NOT wait.
        # (bash '&' via subprocess.run hangs on pipe cleanup; see AGENTS.md.)'''
new_start = '''        # Start new detached (PPID 1, own SID) UNDER THE SUPERVISOR, so the
        # next silent death is classified (signal vs exit code) in supervisor.log.
        # Use Popen with start_new_session + all fds redirected; do NOT wait.
        # (bash '&' via subprocess.run hangs on pipe cleanup; see AGENTS.md.)'''
assert s.count(old_start) == 1, "start comment anchor"
s = s.replace(old_start, new_start)

old_cmd = '''            ["python3", "connector.py"],'''
new_cmd = '''            ["python3", "supervise-connector.py"],'''
assert s.count(old_cmd) == 1, "start cmd anchor"
s = s.replace(old_cmd, new_cmd)

open(p, "w").write(s)
import ast
ast.parse(s)
print("deploy-cell.py patched OK")
