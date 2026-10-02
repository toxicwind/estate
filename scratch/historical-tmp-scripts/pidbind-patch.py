import re
p = '/tmp/mcp-wt/projects/bridge/yote/awrawr_mcp.py'
s = open(p).read()

# 1. Add imports (socket, fcntl, errno, atexit) after "import urllib.request"
old_imports = """import subprocess
import time
import urllib.request"""
new_imports = """import subprocess
import time
import urllib.request
import socket
import fcntl
import errno
import atexit"""
assert old_imports in s
s = s.replace(old_imports, new_imports, 1)

# 2. Add singleton constants after _PORT definition
old_port = '_PORT = int(os.environ.get("AWR_MCP_PORT", "25198"))'
new_port = '''_PORT = int(os.environ.get("AWR_MCP_PORT", "25198"))

# --- pitchfork supervision: bind-owned singleton ---------------------------
# A duplicate process must NEVER steal the port or clobber the PID file.
# Protocol:
#   1. Take an exclusive non-blocking flock on the lock file. If another
#      live process holds it, exit quietly (code 0) -- the fleet is healthy.
#   2. Pre-bind(2) the TCP listener ourselves. EADDRINUSE here means a
#      foreign process owns the port; exit without touching the PID file.
#   3. Only after the bind succeeds, atomically write our PID file.
#   4. Hand the already-bound socket to uvicorn (sockets=[...]) so there is
#      exactly one bind in the whole startup path -- no double-spawn race.
#   5. On owned shutdown, remove the PID file iff it still names our PID.
_PID_FILE = os.path.expanduser("~/.local/state/awrawr-mcp.pid")
_LOCK_FILE = os.path.expanduser("~/.local/state/awrawr-mcp.lock")
_singleton_lock_fd = None


def _acquire_singleton():
    """Return True if this process owns the singleton, else False.

    Never raises for contention: contention means the fleet is healthy and
    this duplicate must exit quietly."""
    global _singleton_lock_fd
    os.makedirs(os.path.dirname(_LOCK_FILE), exist_ok=True)
    fd = os.open(_LOCK_FILE, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return False
    _singleton_lock_fd = fd  # held for process lifetime; released on exit
    return True


def _write_pid_file():
    os.makedirs(os.path.dirname(_PID_FILE), exist_ok=True)
    tmp = "%s.%d.tmp" % (_PID_FILE, os.getpid())
    with open(tmp, "w") as f:
        f.write("%d\\n" % os.getpid())
    os.replace(tmp, _PID_FILE)


def _remove_pid_file_if_owned():
    try:
        with open(_PID_FILE) as f:
            if f.read().strip() == str(os.getpid()):
                os.unlink(_PID_FILE)
    except OSError:
        pass


def _prebind_listener(port):
    """Bind+listen the MCP port ourselves. Raises OSError on failure."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", port))
        sock.listen(128)
        return sock
    except OSError:
        sock.close()
        raise'''
assert old_port in s
s = s.replace(old_port, new_port, 1)

# 3. Replace _serve() with bind-owned version
old_serve = '''async def _serve() -> None:
    app = mcp.streamable_http_app()
    app.add_middleware(HeaderTokenAuth)
    await uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=_PORT, log_level="info")
    ).serve()


if __name__ == "__main__":
    anyio.run(_serve)'''
new_serve = '''async def _serve() -> None:
    # Singleton first: a duplicate exits quietly, never touching port/PID.
    if not _acquire_singleton():
        print("[awrawr-mcp] another instance holds the singleton lock; exiting",
              flush=True)
        return
    try:
        listener = _prebind_listener(_PORT)
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            print("[awrawr-mcp] port %d already bound by a foreign process; "
                  "exiting without touching PID file" % _PORT, flush=True)
            return
        raise
    # Bind succeeded: we own the port. Publish the PID file atomically.
    _write_pid_file()
    atexit.register(_remove_pid_file_if_owned)
    app = mcp.streamable_http_app()
    app.add_middleware(HeaderTokenAuth)
    try:
        await uvicorn.Server(
            uvicorn.Config(app, log_level="info")
        ).serve(sockets=[listener])
    finally:
        _remove_pid_file_if_owned()


if __name__ == "__main__":
    anyio.run(_serve)'''
assert old_serve in s
s = s.replace(old_serve, new_serve, 1)

open(p, 'w').write(s)
print("PATCH-APPLIED")
