# --- bridge-max: multitask + background dispatch ---------------------------
# Added 2026-09-20 by bridge-max. Canonical source:
# projects/bridge/yote/awrawr_mcp.py in toxicwind/sovereign-projects
# (live file /home/toxic/awrawr_mcp.py is deployed from there).
import threading as _threading
import uuid as _uuid

MCP_BG_BASE = os.path.expanduser("~/.cache/mcp-bg")
_MCP_BG_HANDLE_RX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_MCP_BG_TAIL = 4000


def _mcp_write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def _mcp_run_one(cmd, workdir, timeout=90):
    """Single command through the same policy/audit path as exec."""
    t0 = time.monotonic()
    orig_cmd = cmd
    yolo = cmd.startswith("#yolo ")
    if yolo:
        cmd = cmd[len("#yolo "):].lstrip()
    base = {"cmd": orig_cmd[:500], "workdir": workdir, "yolo": yolo}
    denied = None if yolo else _policy_check(cmd)
    if denied:
        _audit(**base, status="denied", reason=denied,
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return "POLICY DENIED: %s" % denied
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=workdir or "/home/toxic")
        out = (p.stdout or "") + (p.stderr or "")
        truncated = len(out) > 20000
        _audit(**base, status="ok", exit=p.returncode, out_chars=len(out),
               truncated=truncated,
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        rc = "[exit=%d] " % p.returncode
        return rc + out[:20000] if out else rc + "(no output)"
    except subprocess.TimeoutExpired:
        _audit(**base, status="timeout",
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return "TIMEOUT after %ss" % timeout
    except Exception as e:
        _audit(**base, status="error", reason=str(e)[:200],
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return "error: %s" % e


@mcp.tool()
def exec_multi(cmds: str, workdir: str = "/home/toxic",
               timeout: int = 90) -> str:
    """Run multiple shell commands concurrently on awrawr-pc.

    cmds: JSON array of command strings (max 32). Each command goes through
    the same command policy and audit trail as exec. Returns tagged results.
    """
    try:
        items = json.loads(cmds)
    except ValueError as e:
        return "invalid cmds JSON: %s" % e
    if not isinstance(items, list) or not items:
        return "cmds must be a non-empty JSON array of command strings"
    items = [str(c) for c in items[:32]]
    results = {}

    def run(c):
        return _mcp_run_one(c, workdir, timeout)

    with ThreadPoolExecutor(max_workers=min(8, len(items))) as ex:
        futs = {ex.submit(run, c): c for c in items}
        for fut in as_completed(futs):
            c = futs[fut]
            try:
                results[c] = fut.result()
            except Exception as e:
                results[c] = "error: %s" % e
    return "\n".join("=== [%s] ===\n%s" % (c[:80], results[c])
                     for c in items)


def _mcp_bg_reap(handle, proc, cmd):
    code = proc.wait()
    d = os.path.join(MCP_BG_BASE, handle)
    _mcp_write_json_atomic(
        os.path.join(d, "status.json"),
        {"state": "done", "code": code, "pid": proc.pid,
         "finished": time.time(), "cmd": cmd[:500]})
    _audit(tool="exec_bg", handle=handle, status="done", exit=code,
           cmd=cmd[:500])


@mcp.tool()
def exec_bg(cmd: str, workdir: str = "/home/toxic") -> str:
    """Launch a shell command fully detached on awrawr-pc.

    Returns a handle immediately; the command keeps running after this call
    returns. Check it later with bg_status. Subject to the command policy
    (prefix '#yolo ' to bypass, audited). Output goes to the handle's
    stdout.log / stderr.log under ~/.cache/mcp-bg/<handle>/.
    """
    handle = _uuid.uuid4().hex[:12]
    d = os.path.join(MCP_BG_BASE, handle)
    os.makedirs(d, exist_ok=True)
    yolo = cmd.startswith("#yolo ")
    denied = None if yolo else _policy_check(cmd)
    if denied:
        _audit(tool="exec_bg", status="denied", reason=denied,
               cmd=cmd[:500])
        return "POLICY DENIED: %s" % denied
    with open(os.path.join(d, "cmd.txt"), "w") as f:
        f.write(cmd)
    out = open(os.path.join(d, "stdout.log"), "wb")
    err = open(os.path.join(d, "stderr.log"), "wb")
    try:
        proc = subprocess.Popen(
            cmd, shell=True, cwd=workdir or "/home/toxic",
            stdout=out, stderr=err, stdin=subprocess.DEVNULL,
            start_new_session=True)
    except Exception as e:
        _audit(tool="exec_bg", status="error", reason=str(e)[:200],
               cmd=cmd[:500])
        return "error: %s" % e
    finally:
        out.close()
        err.close()
    _mcp_write_json_atomic(
        os.path.join(d, "status.json"),
        {"state": "running", "pid": proc.pid, "started": time.time(),
         "cmd": cmd[:500]})
    t = _threading.Thread(target=_mcp_bg_reap, args=(handle, proc, cmd),
                          daemon=True)
    t.start()
    _audit(tool="exec_bg", status="dispatched", handle=handle, pid=proc.pid,
           cmd=cmd[:500])
    return "handle: %s (check with bg_status)" % handle


@mcp.tool()
def bg_status(handle: str) -> str:
    """Status of a background command launched with exec_bg: state, exit
    code, and tails of stdout/stderr."""
    if not _MCP_BG_HANDLE_RX.match(handle or ""):
        return "bad handle"
    d = os.path.join(MCP_BG_BASE, handle)
    sp = os.path.join(d, "status.json")
    if not os.path.exists(sp):
        return "unknown handle: %s" % handle
    with open(sp) as f:
        st = json.load(f)
    pid = st.get("pid")
    if st.get("state") == "running" and pid:
        try:
            os.kill(pid, 0)
            st["alive"] = True
        except Exception:
            st["alive"] = False
            st["state"] = "orphaned"
            st["note"] = "pid gone; mcp likely restarted mid-task"
    lines = ["handle: %s" % handle,
             "state: %s" % st.get("state")]
    if st.get("code") is not None:
        lines.append("exit: %s" % st.get("code"))
    if st.get("cmd"):
        lines.append("cmd: %s" % st.get("cmd"))
    for name in ("stdout.log", "stderr.log"):
        p = os.path.join(d, name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - _MCP_BG_TAIL))
                tail = f.read().decode("utf-8", "replace")
            lines.append("--- %s (tail) ---\n%s" % (name, tail))
    return "\n".join(lines)

# --- end bridge-max ----------------------------------------------------------
