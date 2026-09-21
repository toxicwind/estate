#!/usr/bin/env python3
"""Deploy yote-connector from canonical sources.

Cell-side deploy script. Pulls the canonical files from yote via the bridge,
installs them to the managed cell paths, verifies SHA256, and restarts the
connector.

Canonical sources (toxicwind/sovereign-projects on yote):
  projects/bridge/hatch/connector.py  -> ~/workspace/yote-connector/connector.py
  gear/awrawr-mcp/bin/exec.py          -> ~/workspace/awrawr-bridge/exec.py

The cell-side ~/workspace/awrawr-bridge/exec.py is a MANAGED DEPLOYED ARTIFACT.
Its canonical source is gear/awrawr-mcp/bin/exec.py. Do not edit it on the
cell directly — edit the source and re-run this script.

Usage: deploy-yote-connector.py [--no-restart]
"""

import hashlib
import os
import subprocess
import sys
import tempfile

YOTE_CONN = os.path.expanduser("~/workspace/bin/yote-conn")

# (yote source path, cell dest path)
FILES = [
    ("/home/toxic/sovereign/projects/bridge/hatch/connector.py",
     os.path.expanduser("~/workspace/yote-connector/connector.py")),
    ("/home/toxic/sovereign/gear/awrawr-mcp/bin/exec.py",
     os.path.expanduser("~/workspace/awrawr-bridge/exec.py")),
]

def yote_exec(cmd: str, timeout: int = 60) -> str:
    """Run a command on yote via the bridge, return stdout."""
    result = subprocess.run(
        [YOTE_CONN, "exec", cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"yote exec failed: {result.stderr[:500]}")
    out = result.stdout
    # Unwrap JSON envelope if present (bridge fallback shape)
    stripped = out.strip()
    if stripped.startswith("{"):
        try:
            import json
            data = json.loads(stripped)
            if isinstance(data, dict) and "stdout" in data:
                return data["stdout"]
        except:
            pass
    return out

def yote_fetch_b64(yote_path: str) -> bytes:
    """Fetch a file from yote via base64, in chunks (output truncates at ~20k chars)."""
    import base64
    # Get file size
    size_out = yote_exec(f"stat -c %s {yote_path}").strip()
    # Handle possible JSON envelope in size output
    if size_out.startswith("{"):
        import json
        size_out = json.loads(size_out).get("stdout", "").strip()
    file_size = int(size_out.split()[0])
    print(f"  File size: {file_size} bytes")

    # Fetch in 12KB chunks (16KB base64 < 20k limit)
    chunk_size = 12 * 1024
    chunks = []
    offset = 0
    while offset < file_size:
        # Use dd to extract chunk, then base64
        cmd = f"dd if={yote_path} bs=1 skip={offset} count={chunk_size} 2>/dev/null | base64 -w0"
        b64_chunk = yote_exec(cmd).strip()
        # Unwrap if needed (yote_exec already does, but be safe)
        if b64_chunk.startswith("{"):
            import json
            b64_chunk = json.loads(b64_chunk).get("stdout", "").strip()
        chunks.append(base64.b64decode(b64_chunk))
        offset += chunk_size
        print(f"  Fetched {min(offset, file_size)}/{file_size} bytes...", end="\r")
    print()
    return b"".join(chunks)

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



def main():
    no_restart = "--no-restart" in sys.argv

    for yote_src, cell_dst in FILES:
        print(f"Fetching {yote_src}...")
        data = yote_fetch_b64(yote_src)

        # Verify SHA against yote source
        yote_sha = yote_exec(f"sha256sum {yote_src}").split()[0]
        # Handle JSON envelope
        if yote_sha.startswith("{"):
            import json
            yote_sha = json.loads(yote_exec(f"sha256sum {yote_src}")).get("stdout", "").split()[0]
        local_sha = hashlib.sha256(data).hexdigest()
        if yote_sha != local_sha:
            print(f"SHA MISMATCH for {yote_src}: yote={yote_sha} local={local_sha}", file=sys.stderr)
            sys.exit(1)
        print(f"  SHA256 OK: {local_sha[:16]}...")

        # Install
        os.makedirs(os.path.dirname(cell_dst), exist_ok=True)
        # Write to temp then rename for atomicity
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(cell_dst))
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.rename(tmp, cell_dst)
        print(f"  Installed -> {cell_dst}")

    if not no_restart:
        print("Restarting connector (supervised: supervise-connector.py wraps connector.py and classifies the next death)...")
        # Exact-PID stop only: no pkill -f, no loose pgrep. A loose pattern
        # once SIGTERMed the live production connector (2026-09-21); the pid
        # file is trusted only when /proc/<pid>/cmdline + cwd verify.
        stop_connector_exact()
        import time
        time.sleep(2)
        # Start new detached (PPID 1, own SID) UNDER THE SUPERVISOR, so the
        # next silent death is classified (signal vs exit code) in supervisor.log.
        # Use Popen with start_new_session + all fds redirected; do NOT wait.
        # (bash '&' via subprocess.run hangs on pipe cleanup; see AGENTS.md.)
        conn_dir = os.path.expanduser("~/workspace/yote-connector")
        log_path = os.path.join(conn_dir, "connector.log")
        log_fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        devnull = os.open(os.devnull, os.O_RDONLY)
        subprocess.Popen(
            ["python3", "supervise-connector.py"],
            cwd=conn_dir,
            stdout=log_fd,
            stderr=log_fd,
            stdin=devnull,
            start_new_session=True,  # setsid: new SID, detached from our session
            close_fds=True,
        )
        # Close our copies; the daemon holds its own.
        os.close(log_fd)
        os.close(devnull)
        print("  Connector restart issued.")
        time.sleep(3)
        # Verify health
        result = subprocess.run([YOTE_CONN, "health"], capture_output=True, text=True, timeout=30)
        print(f"  Health: {result.stdout.strip()[:200]}")
        if result.returncode != 0:
            print(f"  WARNING: health check failed: {result.stderr[:300]}", file=sys.stderr)

    print("Deploy complete.")

if __name__ == "__main__":
    main()
