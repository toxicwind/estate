import re

p = '/home/toxic/sovereign/projects/mesh/squawk/nats/test_dual_publish.py'
s = open(p).read()

old = '''def squawk_send(text):
    """Publish via the canonical CLI path (unsigned file write)."""
    out = subprocess.run(
        [os.path.expanduser("/home/toxic/shingle/bin/squawk"), "--profile", "taps",
         "send", CHANNEL, text],
        capture_output=True, text=True, timeout=60)
    return out.stdout.strip() + out.stderr.strip()'''
new = '''SQUAWK_BIN = "/home/toxic/shingle/bin/squawk"  # yote-native chat.py wrapper

def squawk_send(text):
    """Publish via the yote-native CLI (post -> file sink). Returns CLI output."""
    out = subprocess.run(
        [SQUAWK_BIN, "post", CHANNEL, "--from", "taps",
         "--title", "taps-e2e", "--body", text],
        capture_output=True, text=True, timeout=60)
    return out.stdout.strip() + out.stderr.strip()'''
assert old in s, "squawk_send pattern"
s = s.replace(old, new, 1)

# callers check for the yote CLI's success marker
s = s.replace('if "published" not in res:', 'if "posted #" not in res:')
s = s.replace('check("T1 file sink: squawk send published", False, res[-200:])',
              'check("T1 file sink: squawk post accepted", False, res[-200:])')
s = s.replace('ok_send = "published" in res', 'ok_send = "posted #" in res')

open(p, "w").write(s)
import ast
ast.parse(s)
print("test patched, posted-marker count:", s.count('"posted #"'))
