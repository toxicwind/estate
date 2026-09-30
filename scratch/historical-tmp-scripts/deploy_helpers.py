def _proc_exe_name(pid: int) -> str:
    """Executable basename of a process, from /proc/<pid>/comm."""
    try:
        with open(f"/proc/{pid}/comm") as f:
            return f.read().strip()
    except OSError:
        return ""

def _proc_cmdline(pid: int) -> str:
    """Full argv of a process, NULs replaced by spaces."""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\0", b" ").decode(errors="replace")
    except OSError:
        return ""

def _proc_cwd(pid: int) -> str:
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return ""

def _proc_ppid(pid: int) -> int:
    try:
        with open(f"/proc/{pid}/stat") as f:
            # comm is parenthesized and may contain spaces/parens; ppid is the
            # field right after the closing paren.
            stat = f.read()
            after = stat.rsplit(")", 1)[1].split()
            return int(after[1])
    except (OSError, IndexError, ValueError):
        return 0

def verified_connector_pid() -> int:
    """Return the PID from connector.pid only if it is really our connector.

    Exact-PID discipline: the pid file is trusted ONLY when
    /proc/<pid>/cmdline names connector.py AND /proc/<pid>/cwd is the
    connector dir. No pkill, no pgrep, no loose patterns — a stale or
    recycled pid file must never kill an innocent process.
    """
    conn_dir = os.path.expanduser("~/workspace/yote-connector")
    pid_file = os.path.join(conn_dir, "connector.pid")
    try:
        with open(pid_file) as f:
            pid = int(f.read().strip().split()[0])
    except (OSError, ValueError):
        return 0
    if pid <= 1:
        return 0
    cmdline = _proc_cmdline(pid)
    if "connector.py" not in cmdline:
        print(f"  connector.pid={pid} but cmdline is not our connector ({cmdline[:80]}...); refusing to signal", file=sys.stderr)
        return 0
    if _proc_cwd(pid) != conn_dir:
        print(f"  connector.pid={pid} but cwd={_proc_cwd(pid)} != {conn_dir}; refusing to signal", file=sys.stderr)
        return 0
    return pid

def stop_connector_exact(timeout: int = 8):
    """SIGTERM the verified connector child and its verified supervisor parent.

    Exact PIDs only. If verification fails, nothing is signaled.
    """
    pid = verified_connector_pid()
    if not pid:
        print("  No verified connector process; nothing to stop.")
        return
    parent = _proc_ppid(pid)
    parent_ok = (
        parent > 1
        and "supervise-connector.py" in _proc_cmdline(parent)
        and _proc_cwd(parent) == os.path.expanduser("~/workspace/yote-connector")
    )
    print(f"  Stopping connector pid={pid}" + (f" (supervisor pid={parent})" if parent_ok else " (no verified supervisor parent)"))
    try:
        os.kill(pid, 15)
    except OSError as e:
        print(f"  SIGTERM to {pid} failed: {e}", file=sys.stderr)
        return
    # Wait for the child to exit, then SIGKILL if it lingers.
    import time
    for _ in range(timeout * 2):
        if not _proc_cmdline(pid):
            break
        time.sleep(0.5)
    else:
        print(f"  pid={pid} ignored SIGTERM; SIGKILL", file=sys.stderr)
        try:
            os.kill(pid, 9)
        except OSError:
            pass
    if parent_ok and _proc_cmdline(parent):
        # The supervisor exits on its own once the child dies; nudge it.
        try:
            os.kill(parent, 15)
        except OSError:
            pass

