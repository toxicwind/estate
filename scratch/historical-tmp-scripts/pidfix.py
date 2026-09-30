import os, sys
p = "/home/toxic/sovereign/projects/bridge/hatch/connector.py"
old = '''def main():
    # Self-maintained pidfile: launcher $! capture is unreliable across
    # subshell/setsid boundaries (goes stale, watchdogs then kill the wrong
    # pid or none). The daemon always knows its own pid.
    try:
        with open(os.path.join(HERE, "connector.pid"), "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    srv.daemon_threads = True
    log("listening on 127.0.0.1:%d (pid %d)" % (PORT, os.getpid()))'''
new = '''def main():
    # Self-maintained pidfile: launcher $! capture is unreliable across
    # subshell/setsid boundaries (goes stale, watchdogs then kill the wrong
    # pid or none). The daemon always knows its own pid.
    # NOTE: pidfile is written only AFTER the socket bind succeeds. A child
    # that loses the bind race (EADDRINUSE) must not leave its pid behind,
    # or watchdogs will pid-check a dead process and miss the live daemon.
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    srv.daemon_threads = True
    pidfile = os.path.join(HERE, "connector.pid")
    try:
        tmp = pidfile + ".tmp"
        with open(tmp, "w") as f:
            f.write(str(os.getpid()))
        os.replace(tmp, pidfile)
    except OSError:
        pass
    log("listening on 127.0.0.1:%d (pid %d)" % (PORT, os.getpid()))'''
s = open(p).read()
n = s.count(old)
assert n == 1, "anchor count=%d, aborting" % n
open(p, "w").write(s.replace(old, new))
print("PATCHED-OK")
