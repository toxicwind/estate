#!/usr/bin/env python3
"""awrawr-pc MCP exec bridge (tailscale funnel) — hardened.

Security layers (outermost first):
 1. Tailscale funnel: TLS, outbound-only, no firewall ports opened.
 2. HeaderTokenAuth: X-MCP-Token must equal ~/.awrawr_mcp_token (else 401).
 3. DNS-rebinding protection: Host allowlist (localhost + funnel host).
 4. Command policy: denylist of catastrophic patterns; optional allowlist
    via MCP_ALLOW_PATTERNS (one regex per line — if set, the command must
    match at least one). Denylist overridable via MCP_DENY_PATTERNS.
 5. Audit: every decision appended as JSONL to ~/.awrawr_mcp_audit.jsonl
    (5 MB rotation, one backup). The token is never logged.
 6. Limits: 90 s timeout, 20 000-char output cap.

NOTE: the denylist mitigates accidents and casual injection, it is NOT a
sandbox — shell=True can express anything. A valid token still means full
shell on the box. The token is the real security boundary.
YOLO: prefix a command with '#yolo ' to bypass the command policy entirely
(still authenticated, still audited - flagged yolo:true).
"""
import anyio
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import re
import subprocess
import time
import urllib.request
from datetime import datetime, timezone

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

TOKEN = open(os.path.expanduser("~/.awrawr_mcp_token")).read().strip()
AUDIT_LOG = os.path.expanduser("~/.awrawr_mcp_audit.jsonl")

FUNNEL_HOST = os.environ.get("MCP_FUNNEL_HOST", "github-mcp-host.tailc9ac71.ts.net").strip()
_allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
if FUNNEL_HOST:
    _allowed_hosts += [FUNNEL_HOST, FUNNEL_HOST + ":*"]


class HeaderTokenAuth(BaseHTTPMiddleware):
    """Reject any request whose X-MCP-Token header != the token file."""

    async def dispatch(self, request, call_next):
        if request.headers.get("x-mcp-token") != TOKEN:
            return PlainTextResponse("unauthorized", status_code=401)
        return await call_next(request)


# --- command policy -------------------------------------------------------
_DEFAULT_DENY = [
    # rm -rf against / or ~ ($HOME)
    r"\brm\s+(-[a-z]*r[a-z]*\s+|--recursive\s+)(/($|\s)|~($|\s|\*|/)|/\*|\$HOME(\s|/\*|$|/))",
    r":\(\)\s*\{\s*:\|\s*:\s*&\s*\}\s*;",          # fork bomb
    r"\bdd\b.*\bof=/dev/(sd|hd|nvme|vd)[a-z]*",   # dd onto raw disk
    r"\bmkfs(\.|$|\s)",                           # format a filesystem
    r">\s*/dev/(sd|hd|nvme|vd)[a-z]*",            # redirect onto raw disk
    r"\b(shutdown|reboot|halt|poweroff)\b",       # power actions (use SSH for these)
]

_deny_src = os.environ.get("MCP_DENY_PATTERNS")
_DENY = [re.compile(p, re.IGNORECASE)
         for p in (_deny_src.splitlines() if _deny_src else _DEFAULT_DENY)
         if p.strip()]

_allow_src = os.environ.get("MCP_ALLOW_PATTERNS", "")
_ALLOW = [re.compile(p, re.IGNORECASE) for p in _allow_src.splitlines() if p.strip()]


def _policy_check(cmd: str) -> str | None:
    """Return None if the command is allowed, else a deny reason."""
    for rx in _DENY:
        if rx.search(cmd):
            return f"denied by pattern: {rx.pattern[:80]}"
    if _ALLOW and not any(rx.search(cmd) for rx in _ALLOW):
        return "not matched by MCP_ALLOW_PATTERNS allowlist"
    return None


def _audit(**fields) -> None:
    """Append one JSONL audit record. Must never break exec."""
    try:
        if os.path.exists(AUDIT_LOG) and os.path.getsize(AUDIT_LOG) > 5 * 1024 * 1024:
            os.replace(AUDIT_LOG, AUDIT_LOG + ".1")
        rec = {"ts": datetime.now(timezone.utc).isoformat(), **fields}
        with open(AUDIT_LOG, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


# Port is environment-driven (pitchfork daemons.awrawr-mcp sets AWR_MCP_PORT).
_PORT = int(os.environ.get("AWR_MCP_PORT", "25198"))

mcp = FastMCP(
    "awrawr-exec",
    host="127.0.0.1",
    port=_PORT,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_allowed_hosts,
    ),
)


# --- canonical spawn environment -------------------------------------------
# The bridge is a single-user lane for the toxic user on yote. This function
# normalizes the environment for EVERY spawned user command, in protocol
# code, so no caller ever needs to export PATH/HOME by hand:
#   - HOME/USER/LOGNAME are pinned to the toxic user. A supervisor started
#     from a foreign session (or with a scrubbed env) can never leak its
#     HOME into remote commands again.
#   - PATH is rebuilt with the canonical yote dirs first (mise shims must
#     win over system binaries), then the supervisor's surviving entries
#     (minus unexpanded shell placeholders like fish's literal "%h/..."),
#     then the core system dirs.
# bridge/awrawr_ws_exec.py carries the same canonical definition for the WS
# lane — keep the two in sync.
_CANON_HOME = "/home/toxic"
_CANON_USER = "toxic"
_CANON_PATH_FIRST = ("/home/toxic/.local/share/mise/shims",
                     "/home/toxic/.local/bin")
_CANON_CORE_PATH_DIRS = ("/usr/local/sbin", "/usr/local/bin", "/usr/sbin",
                         "/usr/bin", "/sbin", "/bin")


def _canonical_spawn_env():
    seen, parts = set(), []
    for d in _CANON_PATH_FIRST:
        seen.add(d)
        parts.append(d)
    raw = os.environ.get("PATH", "") or ""
    for seg in raw.split(os.pathsep):
        seg = seg.strip()
        if not seg or "%" in seg:  # unexpanded placeholder, unusable
            continue
        seg = os.path.expanduser(seg)
        if seg and seg not in seen:
            seen.add(seg)
            parts.append(seg)
    for d in _CANON_CORE_PATH_DIRS:
        if d not in seen:
            seen.add(d)
            parts.append(d)
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join(parts)
    env["HOME"] = _CANON_HOME
    env["USER"] = _CANON_USER
    env["LOGNAME"] = _CANON_USER
    return env


@mcp.tool()
def exec(cmd: str, workdir: str = "/home/toxic") -> str:
    """Run a shell command on awrawr-pc (subject to command policy).

    Prefix with '#yolo ' to bypass the policy entirely - only when you
    really mean it. YOLO calls are flagged in the audit log.
    """
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
        return f"POLICY DENIED: {denied}"
    try:
        p = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=90,
            cwd=workdir or "/home/toxic",
            env=_canonical_spawn_env(),
        )
        out = (p.stdout or "") + (p.stderr or "")
        truncated = len(out) > 20000
        _audit(**base, status="ok", exit=p.returncode, out_chars=len(out),
               truncated=truncated,
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        rc = f"[exit={p.returncode}] "
        return rc + out[:20000] if out else rc + "(no output)"
    except subprocess.TimeoutExpired:
        _audit(**base, status="timeout",
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return "TIMEOUT after 90s"
    except Exception as e:
        _audit(**base, status="error", reason=str(e)[:200],
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return f"error: {e}"



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
                           timeout=timeout, cwd=workdir or "/home/toxic",
                           env=_canonical_spawn_env())
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
            start_new_session=True, env=_canonical_spawn_env())
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
    # title lands in YAML frontmatter: strip anything that could forge a
    # frontmatter key (newlines, quotes, colons) — same slug rule as sender.
    title_safe = re.sub(r"[^A-Za-z0-9 _.,!?()-]", "", title or "msg")[:80] or "msg"
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
               f"ts: {ts}\nstatus: discussion\ntitle: {title_safe}\n---\n{text}")
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
    # Resolve like bin/pitchfork-restart does: `mise which` first, then the
    # installs dir. Never the mise shim (it tries to reinstall and fails).
    try:
        p = subprocess.run(["mise", "which", "pitchfork"], capture_output=True,
                           text=True, timeout=15)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    except Exception:
        pass
    fb = "/home/toxic/.local/share/mise/installs/pitchfork/latest/pitchfork"
    if os.path.isfile(fb) and os.access(fb, os.X_OK):
        return fb
    found = _shutil.which("pitchfork")
    return found if found else "pitchfork"


@mcp.tool()
def pitchfork_daemon(name: str = "", action: str = "list") -> str:
    """Inspect or restart pitchfork daemons on yote.

    action=list (all daemons), status (one daemon, needs name), restart
    (needs name; goes through pitchfork-restart with its ground-truth port
    checks). The live transport lanes (awrawr-ws-exec, awrawr-mcp) are never
    restarted here: restarting your own session's transport would SIGTERM it
    mid-request, so the caller never gets a result.
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
        if name.split("/")[-1] in ("awrawr-ws-exec", "awrawr-mcp"):
            return ("error: refusing to restart a live transport lane "
                    "(awrawr-ws-exec/awrawr-mcp)")
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


# --- buildsrv tools -----------------------------------------------------------
# Added 2026-09-21. Native MCP surface for buildsrv, the fleet build server
# on 127.0.0.1:25148. Wraps /home/toxic/bin/buildsrv via argv lists only
# (never shell=True, never raw interpolation). Submit returns immediately
# after queueing; the build itself runs async in buildsrvd.

_BUILDSRV_BIN = "/home/toxic/bin/buildsrv"
_BUILDSRV_JOB_RX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_BUILDSRV_MAX_CMD = 4000
_BUILDSRV_OUT_CAP = 8000


def _buildsrv_run(argv):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return "TIMEOUT after 90s"
    except Exception as e:
        return "error: %s" % e
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    if not out:
        return "[exit=%d] (no output)" % p.returncode
    return out[:_BUILDSRV_OUT_CAP]


def _buildsrv_check_id(job_id):
    if not _BUILDSRV_JOB_RX.match(job_id or ""):
        return "bad job_id: must match ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"
    return None


_BUILDSRV_DEFAULT_REPO = "/home/toxic/sovereign/tools/buildsrv"


@mcp.tool()
def buildsrv_submit(name: str, cmd: str, toolchain: str,
                    repo: str = _BUILDSRV_DEFAULT_REPO,
                    workdir: str = "", timeout: int = 1200) -> str:
    """Submit a build job to buildsrv (fleet build server on :25148).

    Queues the job and returns immediately with the job id; the build runs
    async in buildsrvd. Poll with buildsrv_status / buildsrv_logs.
    cmd is capped at 4000 chars. repo defaults to the buildsrv tool dir;
    toolchain is required (rust|cargo|go|bun|node|python|python3|tsc|java|gradle).
    """
    if not (name or "").strip():
        return "error: name required"
    if not (cmd or "").strip():
        return "error: cmd required"
    if not (toolchain or "").strip():
        return "error: toolchain required"
    if len(cmd) > _BUILDSRV_MAX_CMD:
        return "error: cmd too long (%d > %d)" % (len(cmd), _BUILDSRV_MAX_CMD)
    repo = (repo or _BUILDSRV_DEFAULT_REPO).strip()
    if not repo.startswith("/"):
        return "error: repo must be an absolute path"
    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        return "error: timeout must be an integer"
    timeout = max(30, min(timeout, 7200))
    argv = [_BUILDSRV_BIN, "submit", "--name", name, "--repo", repo,
            "--toolchain", toolchain.strip(), "--cmd", cmd,
            "--timeout", str(timeout)]
    if (workdir or "").strip():
        argv += ["--workdir", workdir.strip()]
    return _buildsrv_run(argv)


@mcp.tool()
def buildsrv_status(job_id: str) -> str:
    """Show buildsrv job status (queued/running/succeeded/failed, exit code)."""
    err = _buildsrv_check_id(job_id)
    if err:
        return err
    return _buildsrv_run([_BUILDSRV_BIN, "status", job_id])


@mcp.tool()
def buildsrv_logs(job_id: str, tail: int = 50) -> str:
    """Show the last N lines of a buildsrv job's log (default 50, max 500)."""
    err = _buildsrv_check_id(job_id)
    if err:
        return err
    try:
        n = int(tail)
    except (TypeError, ValueError):
        return "error: tail must be an integer"
    n = max(1, min(n, 500))
    return _buildsrv_run([_BUILDSRV_BIN, "logs", "-n", str(n), job_id])


@mcp.tool()
def buildsrv_list(limit: int = 10) -> str:
    """List recent buildsrv jobs (default 10, max 50)."""
    try:
        n = int(limit)
    except (TypeError, ValueError):
        return "error: limit must be an integer"
    n = max(1, min(n, 50))
    return _buildsrv_run([_BUILDSRV_BIN, "list", "-n", str(n)])


@mcp.tool()
def buildsrv_health() -> str:
    """Health probe for the buildsrv daemon (:25148): uptime, workers, queue."""
    return _buildsrv_run([_BUILDSRV_BIN, "health"])


# --- end buildsrv tools -------------------------------------------------------
# --- hft race tool ----------------------------------------------------------
RACE_WINNERS_LOG = os.path.expanduser('~/.cache/shingle/hft_race_winners.jsonl')

def _race_one(strategy, timeout):
    name = strategy['name']
    cmd = strategy['cmd']
    match = strategy.get('match')
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, env=_canonical_spawn_env())
        out = p.stdout or ''
        valid = p.returncode == 0 and (match is None or re.search(match, out) is not None)
        r = {'name': name, 'ok': True, 'valid': valid, 'rc': p.returncode, 'error': None, 'output': out if valid else ''}
    except subprocess.TimeoutExpired:
        r = {'name': name, 'ok': False, 'valid': False, 'rc': None, 'error': 'timeout>%ss' % timeout, 'output': ''}
    except Exception as e:
        r = {'name': name, 'ok': False, 'valid': False, 'rc': None, 'error': '%s: %s' % (type(e).__name__, e), 'output': ''}
    r['latency_s'] = round(time.monotonic() - t0, 6)
    return r

def _race_log_winners(tag, winner, latency):
    try:
        os.makedirs(os.path.dirname(RACE_WINNERS_LOG), exist_ok=True)
        with open(RACE_WINNERS_LOG, 'a') as f:
            f.write(json.dumps({'ts': time.time(), 'tag': tag, 'winner': winner, 'latency': latency}) + chr(10))
    except OSError:
        pass

@mcp.tool()
def race(strategies: str, tag: str = 'default', timeout: float = 10) -> str:
    '''Race shell commands concurrently - fastest VALID wins (hft pattern).'''
    t0 = time.monotonic()
    try:
        strats = json.loads(strategies)
    except Exception as e:
        return json.dumps({'error': 'bad strategies JSON: %s' % e})
    if not isinstance(strats, list) or not strats:
        return json.dumps({'error': 'strategies must be a non-empty JSON array'})
    # duplicate strategy names collide in the results dict — suffix them
    seen = {}
    for s in strats:
        n = s.get('name') or 'strategy'
        if n in seen:
            seen[n] += 1
            n = '%s#%d' % (n, seen[n])
        else:
            seen[n] = 1
        s['name'] = n
    results = {}
    with ThreadPoolExecutor(max_workers=min(8, len(strats))) as ex:
        futs = {ex.submit(_race_one, s, timeout): s['name'] for s in strats}
        for fut in as_completed(futs):
            r = fut.result()
            results[r['name']] = r
    latency = {n: {'ok': r['ok'], 'valid': r['valid'], 'latency_s': r['latency_s'], 'error': r['error']} for n, r in results.items()}
    winner = min((n for n, r in results.items() if r['valid']), key=lambda n: results[n]['latency_s'], default=None)
    wout = results[winner]['output'][:20000] if winner else ''
    _race_log_winners(tag, winner, latency)
    return json.dumps({'tag': tag, 'winner': winner, 'strategy_latency': latency, 'output': wout})

# --- ffs tools --------------------------------------------------------------
# Wrappers around the global ffs binary (/home/toxic/.local/bin/ffs, v0.1.30).
# Safe: subprocess.run with an argv list (no shell), roots validated to stay
# under /home/toxic, output capped at 20k chars. These mirror `ffs mcp`
# (stdio) as authenticated HTTP MCP tools on the existing token boundary.
FFS_BIN = "/home/toxic/.local/bin/ffs"
FFS_ALLOWED_ROOT = "/home/toxic"
FFS_OUT_CAP = 20000


def _ffs_root(root: str) -> str | None:
    """Validate root stays under /home/toxic. Return realpath or None."""
    try:
        rp = os.path.realpath(root or FFS_ALLOWED_ROOT)
        if rp == FFS_ALLOWED_ROOT or rp.startswith(FFS_ALLOWED_ROOT + os.sep):
            return rp
    except Exception:
        pass
    return None


def _ffs_run(sub: str, args: list, root: str, timeout: int = 60) -> str:
    """Run `ffs <sub> ... --root <root>` safely (argv list, no shell)."""
    t0 = time.monotonic()
    base = {"tool": "ffs_" + sub, "root": root,
            "args": [str(a)[:80] for a in args[:6]]}
    rp = _ffs_root(root)
    if rp is None:
        _audit(**base, status="denied", reason="root outside /home/toxic",
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return "POLICY DENIED: root must be under /home/toxic"
    if not (os.path.isfile(FFS_BIN) and os.access(FFS_BIN, os.X_OK)):
        return "error: ffs binary not found at " + FFS_BIN
    try:
        p = subprocess.run(
            [FFS_BIN, sub] + [str(a) for a in args] + ["--root", rp],
            capture_output=True, text=True, timeout=timeout,
        )
        out = (p.stdout or "") + (p.stderr or "")
        truncated = len(out) > FFS_OUT_CAP
        _audit(**base, status="ok", exit=p.returncode, out_chars=len(out),
               truncated=truncated,
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        rc = "[exit=%d] " % p.returncode
        return rc + out[:FFS_OUT_CAP] if out else rc + "(no output)"
    except subprocess.TimeoutExpired:
        _audit(**base, status="timeout",
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return "TIMEOUT after %ds" % timeout
    except Exception as e:
        _audit(**base, status="error", reason=str(e)[:200],
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return "error: %s" % e


@mcp.tool()
def ffs_grep(pattern: str, root: str = "/home/toxic", limit: int = 100,
             literal: bool = True) -> str:
    """Search file contents with ffs (replaces grep/rg). literal=True forces
    fixed-string match; set literal=False for regex patterns."""
    args = [pattern, "--limit", str(max(1, min(limit, 500)))]
    if literal:
        args.append("--fixed-strings")
    return _ffs_run("grep", args, root)


@mcp.tool()
def ffs_find(name: str, root: str = "/home/toxic") -> str:
    """Find files by name with ffs (replaces find/fd)."""
    return _ffs_run("find", [name], root)


@mcp.tool()
def ffs_glob(pattern: str, root: str = "/home/toxic") -> str:
    """Match files by glob pattern with ffs."""
    return _ffs_run("glob", [pattern], root)


@mcp.tool()
def ffs_read(path: str, root: str = "/home/toxic", full: bool = False) -> str:
    """Read a file with ffs (token-budget aware; full=True returns raw
    contents). path may be 'file:line' to focus a span."""
    args = [path] + (["--full"] if full else [])
    return _ffs_run("read", args, root)


@mcp.tool()
def ffs_outline(path: str, root: str = "/home/toxic") -> str:
    """Render a file's structural outline (functions, classes, ...) with ffs."""
    return _ffs_run("outline", [path], root)


@mcp.tool()
def ffs_symbol(name: str, root: str = "/home/toxic") -> str:
    """Look up symbol definitions with ffs (tree-sitter AST powered)."""
    return _ffs_run("symbol", [name], root)


@mcp.tool()
def ffs_refs(name: str, root: str = "/home/toxic") -> str:
    """List definitions and usages of a symbol with ffs."""
    return _ffs_run("refs", [name], root)


@mcp.tool()
def ffs_flow(name: str, root: str = "/home/toxic") -> str:
    """Drill-down envelope per definition (def + body + callees + callers)."""
    return _ffs_run("flow", [name], root, timeout=300)


@mcp.tool()
def ffs_overview(root: str = "/home/toxic") -> str:
    """High-signal summary of the workspace (languages, top symbols, ...)."""
    return _ffs_run("overview", [], root, timeout=90)


# --- exa agent tools ----------------------------------------------------------
# NOTE on credentials: yote has no credential broker (no authd), so the
# hatch-vault custom.exa credential cannot be consumed here. The working vault
# path is the hatch-side exa skill. These tools read a provisioned key file:
#   install -m 600 /dev/null ~/.config/exa/api_key   # then paste the key
EXA_API_KEY_FILE = os.path.expanduser('~/.config/exa/api_key')

def _exa_key():
    try:
        with open(EXA_API_KEY_FILE) as f:
            key = f.read().strip()
        return key or None
    except OSError:
        return None

def _exa_post(path, payload, timeout=60):
    key = _exa_key()
    if not key:
        return json.dumps({'error': 'exa not provisioned on yote: write the API key to ~/.config/exa/api_key (mode 600). The hatch-side exa skill uses the vault credential and works now.'})
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(
            'https://api.exa.ai' + path,
            data=json.dumps(payload).encode('utf-8'), method='POST',
            headers={'Content-Type': 'application/json',
                     'x-api-key': key,
                     'User-Agent': 'awrawr-mcp-exa/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        data['_elapsed_ms'] = int((time.monotonic() - t0) * 1000)
        return json.dumps(data)[:20000]
    except Exception as e:
        return json.dumps({'error': '%s: %s' % (type(e).__name__, str(e)[:300])})

@mcp.tool()
def exa_search(query: str, num_results: int = 5, search_type: str = 'auto') -> str:
    """Exa neural web search. Returns results with id/url/title."""
    return _exa_post('/search', {'query': query,
        'numResults': max(1, min(int(num_results), 25)),
        'type': search_type, 'livecrawl': 'fallback'})

@mcp.tool()
def exa_contents(urls: str, max_chars: int = 8000) -> str:
    """Fetch page contents as text via Exa. urls: JSON array of URL strings."""
    try:
        url_list = json.loads(urls)
    except Exception as e:
        return json.dumps({'error': 'urls must be a JSON array: %s' % e})
    if not isinstance(url_list, list) or not url_list:
        return json.dumps({'error': 'urls must be a non-empty JSON array'})
    return _exa_post('/contents', {'urls': url_list,
        'text': {'maxCharacters': int(max_chars)}})

@mcp.tool()
def exa_find_similar(url: str, num_results: int = 5) -> str:
    """Find pages similar to a URL via Exa."""
    return _exa_post('/findSimilar', {'url': url,
        'numResults': max(1, min(int(num_results), 25))})

@mcp.tool()
def exa_answer(query: str) -> str:
    """Ask Exa for a direct answer with citations."""
    return _exa_post('/answer', {'query': query}, timeout=90)


"""Mesh (mcpproxy/shep) connector tools — insert into /home/toxic/awrawr_mcp.py
before `async def _serve()`.

Exposes ALL mcpproxy upstream endpoints (33 MCP servers behind the live shep
daemon at 127.0.0.1:25127) through the awrawr connector. The daemon runs in
`retrieve_tools` routing mode: a small set of meta-tools fans out to every
upstream server's tools (namespaced `server:tool`).

Lane: HTTP JSON-RPC to the live daemon (warm upstream connections, no
per-call process spawn). Each connector call does initialize -> session ->
tools/call over localhost.
"""

# --- mesh (mcpproxy/shep) proxy -------------------------------------------
MESH_MCP_URL = os.environ.get("MESH_MCP_URL", "http://127.0.0.1:25127/mcp")
MESH_SHEP_BIN = os.environ.get(
    "MESH_SHEP_BIN", "/home/toxic/sovereign/projects/mesh/bin/shep")
MESH_SHEP_CONFIG = os.environ.get(
    "MESH_SHEP_CONFIG",
    "/home/toxic/sovereign/projects/mesh/gateway/mcp_config.json")
MESH_OUT_CAP = 20000
_MESH_INTENTS = {"read": "call_tool_read", "write": "call_tool_write",
                 "destructive": "call_tool_destructive"}


def _mesh_session(timeout: int = 15) -> str | None:
    """Open an MCP session against the live shep daemon. Returns session id."""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "awrawr-connector", "version": "1"}}}
    ).encode()
    req = urllib.request.Request(
        MESH_MCP_URL, data=body,
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        sid = r.headers.get("Mcp-Session-Id")
        r.read()
    if not sid:
        return None
    # notifications/initialized (id 2, notification)
    note = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized",
                       "params": {}}).encode()
    req2 = urllib.request.Request(
        MESH_MCP_URL, data=note,
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream",
                 "mcp-session-id": sid})
    try:
        with urllib.request.urlopen(req2, timeout=timeout) as r2:
            r2.read()
    except Exception:
        pass
    return sid


def _mesh_unwrap(raw: str) -> dict:
    """Unwrap a possible SSE envelope into the JSON-RPC dict."""
    raw = raw.strip()
    if raw.startswith("event:"):
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip()
                break
    return json.loads(raw)


def _mesh_call(tool_name: str, arguments: dict, timeout: int = 90) -> str:
    """Call one mcpproxy meta-tool; returns pretty JSON or an error string."""
    t0 = time.monotonic()
    base = {"tool": "mesh_" + tool_name, "args_keys": list(arguments or {})[:8]}
    try:
        sid = _mesh_session(timeout=min(15, timeout))
        if not sid:
            _audit(**base, status="error", reason="no mcp session",
                   elapsed_ms=int((time.monotonic() - t0) * 1000))
            return "error: mcpproxy daemon did not issue a session (is shep serve running on 25127?)"
        body = json.dumps({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}}},
        ).encode()
        req = urllib.request.Request(
            MESH_MCP_URL, data=body,
            headers={"Content-Type": "application/json",
                     "Accept": "application/json, text/event-stream",
                     "mcp-session-id": sid})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = _mesh_unwrap(r.read().decode("utf-8", "replace"))
        result = payload.get("result", {})
        if payload.get("error"):
            out = "MCP ERROR: " + json.dumps(payload["error"])[:2000]
        else:
            content = result.get("content", [])
            texts = [c.get("text", "") for c in content
                     if isinstance(c, dict) and c.get("type") == "text"]
            out = "\n".join(texts) if texts else json.dumps(result)[:MESH_OUT_CAP]
        truncated = len(out) > MESH_OUT_CAP
        _audit(**base, status="ok", out_chars=len(out), truncated=truncated,
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return out[:MESH_OUT_CAP] + ("…[truncated]" if truncated else "")
    except Exception as e:
        _audit(**base, status="error", reason=str(e)[:200],
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return "error: %s" % e


@mcp.tool()
def mesh_upstream_servers() -> str:
    """List all MCP servers proxied by the mesh gateway (shep/mcpproxy):
    name, connection status, health for each of the ~33 upstreams."""
    t0 = time.monotonic()
    base = {"tool": "mesh_upstream_servers"}
    try:
        p = subprocess.run(
            [MESH_SHEP_BIN, "upstream", "list", "-c", MESH_SHEP_CONFIG,
             "-o", "json", "--log-level", "error"],
            capture_output=True, text=True, timeout=60)
        out = (p.stdout or "") + (p.stderr or "")
        try:
            servers = json.loads(p.stdout or "[]")
            rows = ["%s | connected=%s | enabled=%s | health=%s" % (
                s.get("name"), s.get("connected"), s.get("enabled"),
                (s.get("health") or {}).get("level", "?")) for s in servers]
            out = "%d upstream servers:\n" % len(rows) + "\n".join(rows)
        except Exception:
            pass
        _audit(**base, status="ok", exit=p.returncode,
               out_chars=len(out),
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return ("[exit=%d] " % p.returncode + out[:MESH_OUT_CAP]) if out \
            else "[exit=%d] (no output)" % p.returncode
    except Exception as e:
        _audit(**base, status="error", reason=str(e)[:200],
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        return "error: %s" % e


@mcp.tool()
def mesh_retrieve_tools(query: str, limit: int = 10) -> str:
    """Search every tool on every mesh-proxied MCP server by natural-language
    query. Returns matching tools as server:tool with signatures. This is how
    you discover the full endpoint surface of the mesh."""
    return _mesh_call("retrieve_tools",
                      {"query": query, "limit": max(1, min(limit, 50))})


@mcp.tool()
def mesh_describe_tool(tool_names: str) -> str:
    """Fetch the full input schema for mesh tools (comma-separated
    'server:tool' names from mesh_retrieve_tools, e.g.
    "github:search_repositories,exa:web_search") before calling them."""
    ids = [t.strip() for t in (tool_names or "").split(",") if t.strip()]
    if not ids:
        return "error: give at least one server:tool name"
    return _mesh_call("describe_tool", {"tool_ids": ids[:20]})


@mcp.tool()
def mesh_call_tool(tool_name: str, arguments_json: str = "{}",
                   intent: str = "read", timeout: int = 90) -> str:
    """Call any tool on any mesh-proxied MCP server. tool_name is
    'server:tool' (from mesh_retrieve_tools). intent is read (default),
    write, or destructive — destructive intent runs the destructive-gated
    path. arguments_json is the tool's JSON arguments object."""
    key = (intent or "read").strip().lower()
    meta = _MESH_INTENTS.get(key)
    if meta is None:
        return "error: intent must be one of read, write, destructive"
    try:
        args = json.loads(arguments_json or "{}")
        if not isinstance(args, dict):
            return "error: arguments_json must decode to a JSON object"
    except Exception as e:
        return "error: arguments_json is not valid JSON: %s" % e
    return _mesh_call(meta,
                      {"name": tool_name, "args": args,
                       "intent_reason": "awrawr connector mesh_call_tool"},
                      timeout=max(10, min(timeout, 300)))


async def _serve() -> None:
    app = mcp.streamable_http_app()
    app.add_middleware(HeaderTokenAuth)
    await uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=_PORT, log_level="info")
    ).serve()


if __name__ == "__main__":
    anyio.run(_serve)
