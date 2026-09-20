# --- mcp-smith: fleet / introspection / bg tools -------------------------------
# Added 2026-09-20 by mcp-smith. Extends the bridge-max bg registry
# (~/.cache/mcp-bg) with bg_list/bg_kill; adds native fleet (squawk),
# yote_load, port_map, pitchfork_daemon tools so the fleet stops shelling
# out for them. Canonical source: projects/bridge/yote/ in
# toxicwind/sovereign-projects (deployed to /home/toxic/awrawr_mcp.py via
# apply_mcp_patch_mcp_smith.py — same idempotent pattern as bridge-max).
import signal as _signal
import shutil as _shutil

# --- fleet / squawk tools ----------------------------------------------------
# The fleet shells out to `squawk send/read` constantly; native tools cut a
# subprocess per call. Message format mirrors ~/workspace/bin/squawk:
# YAML frontmatter between --- markers; the squawk server assigns the global
# seq on inotify pickup.
SQUAWK_ROOT = os.environ.get("SQUAWK_CHAT_ROOT", "/home/toxic/.shingle/squawk-root")
_CHANNEL_RE = re.compile(r"[A-Za-z0-9_-]{1,32}")


def _squawk_channel_dir(channel: str) -> str | None:
    name = (channel or "").strip()
    if not _CHANNEL_RE.fullmatch(name):
        return None
    d = os.path.join(SQUAWK_ROOT, name)
    return d if os.path.isdir(d) else None


def _squawk_parse(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    fm: dict = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        if ":" in lines[i]:
            k, v = lines[i].split(":", 1)
            fm[k.strip().lower()] = v.strip()
        i += 1
    body = "\n".join(lines[i + 1:]).strip()
    seq = fm.get("seq", "")
    if not seq.isdigit():
        m = re.match(r"(\d+)-", os.path.basename(path))
        seq = m.group(1) if m else "?"
    return {"seq": seq, "from": fm.get("from", "?"), "ts": fm.get("ts", ""),
            "title": fm.get("title", ""), "body": body}


@mcp.tool()
def fleet_send(channel: str, text: str, title: str = "msg",
               sender: str = "mcp") -> str:
    """Publish a message to a squawk channel (fleet, leads, ...).

    Native replacement for shelling out to `squawk send`. The squawk server
    picks the file up via inotify and assigns the global seq.
    """
    t0 = time.monotonic()
    d = _squawk_channel_dir(channel)
    if d is None:
        return "error: unknown or invalid channel"
    sender_slug = re.sub(r"[^A-Za-z0-9_-]", "", sender or "mcp")[:24] or "mcp"
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:24] or "msg"
    seq = 1
    try:
        for f in os.listdir(d):
            m = re.match(r"(\d+)-", f)
            if m:
                seq = max(seq, int(m.group(1)) + 1)
    except OSError as e:
        return f"error: {e}"
    ts = datetime.now(timezone.utc).isoformat()
    content = ("---\n"
               f"seq: {seq}\nfrom: {sender_slug}\nto: all\nchannel: {channel}\n"
               f"ts: {ts}\nstatus: discussion\ntitle: {title[:80]}\n---\n{text}")
    for _ in range(3):  # tolerate a concurrent writer winning the seq race
        fname = f"{seq}-{sender_slug}-{slug}.md"
        path = os.path.join(d, fname)
        try:
            with open(path, "x", encoding="utf-8") as f:
                f.write(content)
            break
        except FileExistsError:
            seq += 1
    else:
        return "error: seq race, retry"
    _audit(tool="fleet_send", channel=channel, seq=seq, sender=sender_slug,
           elapsed_ms=int((time.monotonic() - t0) * 1000))
    return f"published seq={seq} ({fname})"


@mcp.tool()
def fleet_read(channel: str, limit: int = 20, since_seq: int = 0) -> str:
    """Read recent messages from a squawk channel.

    Native replacement for `squawk read`. Returns oldest-first, capped at
    `limit` (max 100). `since_seq` filters to messages newer than that seq.
    """
    d = _squawk_channel_dir(channel)
    if d is None:
        return "error: unknown or invalid channel"
    limit = max(1, min(limit, 100))
    pairs = []
    try:
        for f in os.listdir(d):
            if not f.endswith(".md"):
                continue
            m = _squawk_parse(os.path.join(d, f))
            if not m or not m["seq"].isdigit() or int(m["seq"]) <= since_seq:
                continue
            pairs.append((int(m["seq"]), m))
    except OSError as e:
        return f"error: {e}"
    pairs.sort(key=lambda p: p[0])
    out = []
    for _, m in pairs[-limit:]:
        body = m["body"]
        if len(body) > 600:
            body = body[:600] + "..."
        out.append(f"[{m['seq']}] {m['from']} @ {m['ts']}: {m['title']}\n{body}")
    return "\n---\n".join(out) if out else "(no messages)"


# --- estate introspection ----------------------------------------------------
@mcp.tool()
def yote_load() -> str:
    """Yote load average vs CPU cores, memory, and top CPU processes.

    Native replacement for shelling out to load-audit for the yote side.
    """
    try:
        with open("/proc/loadavg") as f:
            la = f.read().split()[:3]
        cores = os.cpu_count() or 1
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                if k in ("MemTotal", "MemAvailable"):
                    mem[k] = int(v.split()[0]) // 1024
        p = subprocess.run(["ps", "-eo", "pid,pcpu,comm", "--sort=-pcpu"],
                           capture_output=True, text=True, timeout=10)
        top = "\n".join(p.stdout.splitlines()[1:6])
        used = mem.get("MemTotal", 0) - mem.get("MemAvailable", 0)
        return (f"load1/5/15: {' '.join(la)} on {cores} cores "
                f"({float(la[0]) / cores:.1f}x)\n"
                f"mem: {used}M / {mem.get('MemTotal', 0)}M used\n"
                f"top CPU:\n{top}")
    except Exception as e:
        return f"error: {e}"


@mcp.tool()
def port_map() -> str:
    """Listening TCP ports on yote with owning process name/pid.

    Native replacement for `ss -tlnp` shell-outs during bind-conflict hunts.
    """
    try:
        p = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True,
                           timeout=10)
    except Exception as e:
        return f"error: {e}"
    rows = []
    for line in p.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        local = parts[3]
        proc = ""
        m = re.search(r'\("([^"]+)",pid=(\d+)', line)
        if m:
            proc = f"{m.group(1)}:{m.group(2)}"
        rows.append(f"{local:>22}  {proc}")
    return "\n".join(rows) if rows else "(no listeners)"


def _pitchfork_bin() -> str:
    found = _shutil.which("pitchfork")
    if found:
        return found
    fb = "/home/toxic/.local/share/mise/installs/pitchfork/2.27.0/pitchfork"
    return fb if os.path.exists(fb) else "pitchfork"


@mcp.tool()
def pitchfork_daemon(name: str = "", action: str = "list") -> str:
    """Inspect or restart pitchfork daemons on yote.

    action=list (all daemons), status (one daemon, needs name), restart
    (needs name; goes through pitchfork-restart with its ground-truth port
    checks). The live bridge (awrawr-ws-exec, :8379) is never restarted here.
    """
    action = (action or "list").lower()
    pf = _pitchfork_bin()
    if action == "list":
        cmd = [pf, "list"]
    elif action == "status":
        if not name:
            return "error: name required for status"
        cmd = [pf, "status", name]
    elif action == "restart":
        if not name:
            return "error: name required for restart"
        if name.split("/")[-1] in ("awrawr-ws-exec",):
            return "error: refusing to restart the live bridge (awrawr-ws-exec)"
        cmd = ["/home/toxic/sovereign/bin/pitchfork-restart", name]
    else:
        return "error: action must be list|status|restart"
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=180,
                           cwd="/home/toxic/sovereign")
        out = (p.stdout or "") + (p.stderr or "")
        return f"[exit={p.returncode}]\n{out[:8000]}" if out else \
            f"[exit={p.returncode}] (no output)"
    except subprocess.TimeoutExpired:
        return "TIMEOUT after 180s"
    except Exception as e:
        return f"error: {e}"


# --- bridge-max bg registry extensions ---------------------------------------
# exec_bg/bg_status own ~/.cache/mcp-bg/<handle>/. These two complete the
# set: list every handle, and kill a running one (their reaper thread still
# finalizes status.json afterwards).


@mcp.tool()
def bg_list() -> str:
    """List every background handle from exec_bg (bridge-max registry).

    Shows handle, state, exit code, pid, and the command.
    """
    base = MCP_BG_BASE
    if not os.path.isdir(base):
        return "(no background jobs)"
    rows = []
    for h in sorted(os.listdir(base)):
        if not _MCP_BG_HANDLE_RX.match(h):
            continue
        sp = os.path.join(base, h, "status.json")
        try:
            with open(sp) as f:
                st = json.load(f)
        except Exception:
            rows.append(f"{h}  (unreadable)")
            continue
        code = st.get("code")
        ec = f" exit={code}" if code is not None else ""
        rows.append(f"{h}  {st.get('state', '?')}{ec} "
                    f"pid={st.get('pid', '?')} {(st.get('cmd') or '')[:60]}")
    return "\n".join(rows) if rows else "(no background jobs)"


@mcp.tool()
def bg_kill(handle: str) -> str:
    """SIGTERM (then SIGKILL after 3s) a background command from exec_bg.

    Kills the whole process group. The registry's reaper finalizes the
    handle's status afterwards.
    """
    if not _MCP_BG_HANDLE_RX.match(handle or ""):
        return "bad handle"
    d = os.path.join(MCP_BG_BASE, handle)
    sp = os.path.join(d, "status.json")
    if not os.path.exists(sp):
        return "unknown handle: %s" % handle
    try:
        with open(sp) as f:
            st = json.load(f)
    except Exception as e:
        return f"error: {e}"
    pid = st.get("pid")
    if not pid:
        return f"no pid recorded for {handle}"
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return f"handle {handle} already finished (pid {pid} gone)"
    except PermissionError:
        return f"cannot signal pid {pid}: permission denied"
    try:
        os.killpg(os.getpgid(pid), _signal.SIGTERM)
    except Exception as e:
        return f"error signalling pgid: {e}"
    deadline = time.monotonic() + 3
    alive = True
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            alive = False
            break
        except PermissionError:
            break
        time.sleep(0.2)
    if alive:
        try:
            os.killpg(os.getpgid(pid), _signal.SIGKILL)
        except Exception:
            pass
    _audit(tool="bg_kill", handle=handle, pid=pid,
           final="killed" if alive else "terminated")
    return "handle %s %s" % (handle, "killed" if alive else "terminated")


# --- end mcp-smith ------------------------------------------------------------
