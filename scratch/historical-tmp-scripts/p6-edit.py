import sys

p = '/home/toxic/sovereign/pitchfork.toml'
s = open(p).read()

# (old_inner, new_inner) — inner = the ready_cmd string content (without TOML quotes)
OLD_NEW = [
    ("pgrep -f inotifywait.*/home/toxic/refusal-hunt >/dev/null",
     "p=$(pgrep -f '[r]efusal-watchdog[.]py' | head -1); [ -n \"$p\" ] && pgrep -P \"$p\" -f 'inotifywait -m' >/dev/null"),
    ("pgrep -f sorry-watchdog.py >/dev/null",
     "p=$(pgrep -f '[s]orry-watchdog[.]py' | head -1); [ -n \"$p\" ] && pgrep -P \"$p\" -f 'inotifywait -m' >/dev/null"),
    ("pgrep -f 'bridge.ts --daemon --instance a' >/dev/null",
     "p=$(pgrep -f '[b]ridge[.]ts --daemon --instance a' | head -1); [ -n \"$p\" ] && ls -l /proc/$p/fd 2>/dev/null | grep -q inotify"),
    ("pgrep -f 'bridge.ts --daemon --instance b' >/dev/null",
     "p=$(pgrep -f '[b]ridge[.]ts --daemon --instance b' | head -1); [ -n \"$p\" ] && ls -l /proc/$p/fd 2>/dev/null | grep -q inotify"),
]

for old, new in OLD_NEW:
    needle = 'ready_cmd = "%s"' % old
    repl = 'ready_cmd = "%s"' % new.replace('"', '\\"')
    n = s.count(needle)
    if n != 1:
        print("ABORT: expected 1 occurrence, found %d for: %s" % (n, needle[:60]))
        sys.exit(1)
    s = s.replace(needle, repl)

open(p, 'w').write(s)
print("4 replacements OK")
