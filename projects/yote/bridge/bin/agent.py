#!/usr/bin/env python3
"""agent.py — first-class subagents over the awrawr-mcp bridge (PERMANENT).

Wraps /home/toxic/fleet/jobs/bin/job on awrawr-pc: multiple parallel,
backgrounded, queryable, detached workers that survive cell death.

  agent.py submit --name NAME -- cmd [args...]   submit a detached worker
  agent.py submit --join-frame frame.md -- cmd   submit with a Join Frame v1
           in $JOIN_FRAME (rendered by chatctx.py at submit time: chat echo
           + last-5 verbatim + join directive + capabilities)
  agent.py submit --summoner ID --join-cursor SEQ [--cold-boot] -- cmd
           boot-annotate the worker: summoner identity, join cursor
           (null = cold boot). The worker announces itself on boot to the
           remote C2 record /home/toxic/fleet/c2/agents.jsonl (--no-announce
           to skip).
  agent.py list                                  list bridge workers
  agent.py status <id>                           worker status
  agent.py log <id> [--stderr] [--tail N]        worker output
  agent.py result <id>                           worker result/exit
  agent.py kill <id>                             stop a worker
  agent.py roster                                C2 roster: every tracked subagent

C2 tracking: every lifecycle event is appended to
~/workspace/c2/agents.jsonl (one JSON object per line). `roster` merges the
ledger with live `job list` output. This is the command-and-control record
for ALL subagents spawned through this MCP — platform spawns are tracked in
the refusal-hunt parquet; bridge workers are tracked here.
"""
import json
import os
import subprocess
import sys
import time

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXEC_PY = os.path.join(SKILL_DIR, "bin", "exec.py")
XFER_PY = os.path.join(SKILL_DIR, "bin", "xfer.py")
CHATCTX_PY = os.path.join(SKILL_DIR, "bin", "chatctx.py")
JOB = "/home/toxic/fleet/jobs/bin/job"
JOIN_FRAME_VERSION = "v1"
C2_DIR = os.path.expanduser("~/workspace/c2")
LEDGER = os.path.join(C2_DIR, "agents.jsonl")
# Join-chat on-box locations (Join Frame v1, seq=4 synthesis, Chris-confirmed
# 2026-09-18). Frames are scratch (per-submit uuid names); specs are the
# staged job-spec snapshots the bridge submits.
REMOTE_FRAMES_DIR = "/home/toxic/fleet/frames"
REMOTE_SPECS_DIR = "/home/toxic/fleet/specs"
REMOTE_CHATCTX = "/home/toxic/fleet/c2/chatctx.py"


def ledger_append(event):
    os.makedirs(C2_DIR, exist_ok=True)
    event = dict(event)
    event.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    event.setdefault("surface", "bridge")
    with open(LEDGER, "a") as f:
        f.write(json.dumps(event) + "\n")


def bridge(*args):
    """Run `job ...` on awrawr-pc via exec.py; return (rc, stdout)."""
    p = subprocess.run(
        [sys.executable, EXEC_PY, "--argv", JOB] + list(args),
        capture_output=True, text=True, timeout=120)
    if p.returncode != 0 and "refusing HTTPS fallback" in (p.stderr or ""):
        # permanent fallback: argv -> safely quoted shell for the HTTPS path
        import shlex
        cmd = " ".join(shlex.quote(a) for a in [JOB] + list(args))
        p = subprocess.run(
            [sys.executable, EXEC_PY, cmd],
            capture_output=True, text=True, timeout=120)
    out = (p.stdout or "").strip()
    # exec.py prints "[exit=N] ..." wrapper lines; strip the wrapper
    if out.startswith("[exit="):
        out = out.split("]", 1)[1].strip() if "]" in out else out
    return p.returncode, out, (p.stderr or "").strip()


def xfer_put(local, remote):
    """Ship a file to awrawr-pc; return True on success."""
    p = subprocess.run([sys.executable, XFER_PY, "put", local, remote],
                       capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        sys.stderr.write("agent.py: xfer put %s -> %s failed: %s\n"
                         % (local, remote, (p.stderr or p.stdout).strip()[:300]))
        return False
    return True


def minimal_frame(chat):
    """Fail-open minimal join frame (no fetched messages): header + chat
    echo + join directive + capabilities. Rendered via chatctx; never
    raises — worst case a static skeleton."""
    try:
        p = subprocess.run(
            [sys.executable, CHATCTX_PY, "render", "--chat", chat],
            input=b"[]", capture_output=True, timeout=30)
        if p.returncode == 0 and p.stdout:
            return p.stdout
    except Exception as e:
        sys.stderr.write("agent.py: chatctx minimal render failed: %s\n" % e)
    return ("[JOIN-FRAME v1 chat=%s n=0 (renderer unavailable — fail-open)]\n"
            "You are joining this chat. Report results here.\n" % chat).encode()


def c2_announce_prefix(name, summoner, join_cursor, cold_boot):
    """Build the fail-open C2 boot-announcement shell prefix.

    Returns '<C2 env> python3 /home/toxic/fleet/c2/announce.py || true; '
    — the caller appends 'exec "$@"' inside `bash -c`. The announce never
    fails the worker's real command (|| true guard).
    """
    import shlex
    env = ("C2_WORKER_NAME=%s C2_SUMMONER=%s C2_JOIN_CURSOR=%s "
           "C2_COLD_BOOT=%s") % (
               shlex.quote(name), shlex.quote(summoner),
               shlex.quote(join_cursor or ""),
               "true" if cold_boot else "false")
    return ("%s python3 /home/toxic/fleet/c2/announce.py "
            "|| true; ") % env


def submit_with_join(name, join_chat, join_frame_file, timeout, cmd,
                     summoner, join_cursor, cold_boot, announce):
    """Join-chat submit (Join Frame v1, seq=4 synthesis, Chris-confirmed).

    The job spec carries ONLY the chat id (spec.env.JOIN_CHAT) — zero
    transcript text baked into anything durable. The frame is delivered
    as the worker's step-0: a scratch file on awrawr-pc, printed to stderr
    before the real command via a `cat; exec` wrapper (exec keeps the
    process tree and signal behavior identical to an unwrapped worker).
    Frame source: --join-frame-file for a full pre-rendered frame,
    otherwise minimal_frame() rendered cell-side (fail-open, never
    depends on the box having chatctx). If the frame xfer fails, the
    on-box chatctx renders the minimal frame; chatctx missing on-box ->
    worker still boots. The C2 boot-announcement is composed into the
    wrapper unless --no-announce.
    """
    import uuid
    fid = uuid.uuid4().hex[:12]
    remote_frame = "%s/%s.md" % (REMOTE_FRAMES_DIR, fid)
    if "'" in remote_frame:
        sys.exit("agent.py: unsafe frame path")
    if join_frame_file:
        try:
            with open(join_frame_file, "rb") as f:
                frame_bytes = f.read()
        except OSError as e:
            sys.exit("agent.py: cannot read --join-frame-file %s: %s"
                     % (join_frame_file, e))
        frame_kind = "full"
    else:
        frame_bytes = minimal_frame(join_chat)
        frame_kind = "minimal"
    local = "/tmp/agent-join-frame-%s.md" % fid
    with open(local, "wb") as f:
        f.write(frame_bytes)
    frame_ok = xfer_put(local, remote_frame)
    os.unlink(local)
    # step-0: print the frame (xfer'd, or minimal rendered on-box as
    # fallback) to stderr so the worker's stdout stays parseable; the
    # join frame is briefing, not program output.
    step0 = ("{ cat '%s' 2>/dev/null || "
             "python3 %s render --chat \"$JOIN_CHAT\" </dev/null 2>/dev/null"
             " || true; echo; } >&2; " % (remote_frame, REMOTE_CHATCTX))
    if announce:
        step0 += c2_announce_prefix(name, summoner, join_cursor,
                                    cold_boot)
    wrapped = ["bash", "-c", step0 + 'exec "$@"',
               "c2-announce-wrapper"] + cmd
    spec = {"name": name, "cmd": wrapped, "env": {"JOIN_CHAT": join_chat}}
    if timeout:
        spec["timeout"] = timeout
    sid = uuid.uuid4().hex[:12]
    local_spec = "/tmp/agent-join-spec-%s.json" % sid
    remote_spec = "%s/%s.json" % (REMOTE_SPECS_DIR, sid)
    with open(local_spec, "w") as f:
        json.dump(spec, f)
    try:
        if not xfer_put(local_spec, remote_spec):
            sys.exit("agent.py: cannot stage job spec on awrawr-pc")
        rc, out, err = bridge("submit", remote_spec)
    finally:
        os.unlink(local_spec)
    agent_id = out.split()[-1] if out else "unknown"
    if rc != 0:
        sys.stderr.write((err or out) + "\n")
        sys.exit(1)
    # Bidirectional join: the worker announces itself into the C2 ledger,
    # so the chat echo stays live after boot.
    ledger_append({"event": "join", "agent_id": agent_id, "name": name,
                   "chat": join_chat, "frame": frame_kind,
                   "frame_ok": frame_ok, "announce": announce,
                   "summoner": summoner, "join_cursor": join_cursor,
                   "cold_boot": cold_boot, "cmd": cmd, "rc": rc})
    sys.stderr.write("agent.py: worker %s joined chat '%s' (%s frame)\n"
                     % (agent_id, join_chat, frame_kind))
    return agent_id


def cmd_submit(argv):
    # argv: [--name NAME] [--join-frame FILE] [--join-chat CHAT]
    #       [--join-frame-file FILE] [--timeout S] [--summoner ID]
    #       [--join-cursor SEQ] [--cold-boot|--no-cold-boot] [--no-announce]
    #       -- cmd [args...]
    # --join-frame: prepend a pre-rendered Join Frame v1 (chatctx.py render)
    # to the worker's environment as $JOIN_FRAME. Rendered at submit time,
    # so it is fresh by construction; fail-open (no frame = plain submit).
    # --join-chat: Join Frame v1 join-chat path (seq=4 synthesis). The job
    # spec carries ONLY the chat id (spec.env.JOIN_CHAT); the frame is
    # xfer'd to awrawr-pc and printed as the worker's step-0 (stderr,
    # fail-open). --join-frame-file supplies a full pre-rendered frame;
    # without it, minimal_frame() renders the fail-open minimal frame
    # cell-side. Mutually exclusive with --join-frame.
    # Boot announcement (default on): the worker's spawn command is wrapped
    # so its first step runs /home/toxic/fleet/c2/announce.py, appending an
    # `announce` line (worker id, name, summoner, join cursor, cold-boot
    # flag, ts) to the remote C2 record /home/toxic/fleet/c2/agents.jsonl.
    # The announce never fails the worker's real command (|| true guard).
    name = "unnamed"
    frame_file = None
    join_chat = None
    join_frame_file = None
    timeout = 0
    summoner = os.environ.get("C2_SUMMONER", "unknown")
    join_cursor = None
    cold_boot = None  # resolved below: true when no join cursor
    announce = True
    rest = list(argv)
    while rest[:1] == ["--name"] and len(rest) >= 2:
        name = rest[1]
        rest = rest[2:]
    while rest[:1] == ["--join-frame"] and len(rest) >= 2:
        frame_file = rest[1]
        rest = rest[2:]
    while True:
        if rest[:1] == ["--join-chat"] and len(rest) >= 2:
            join_chat = rest[1]
            rest = rest[2:]
        elif rest[:1] == ["--join-frame-file"] and len(rest) >= 2:
            join_frame_file = rest[1]
            rest = rest[2:]
        elif rest[:1] == ["--timeout"] and len(rest) >= 2:
            timeout = int(rest[1])
            rest = rest[2:]
        elif rest[:1] == ["--summoner"] and len(rest) >= 2:
            summoner = rest[1]
            rest = rest[2:]
        elif rest[:1] == ["--join-cursor"] and len(rest) >= 2:
            join_cursor = rest[1]
            rest = rest[2:]
        elif rest[:1] == ["--cold-boot"]:
            cold_boot = True
            rest = rest[1:]
        elif rest[:1] == ["--no-cold-boot"]:
            cold_boot = False
            rest = rest[1:]
        elif rest[:1] == ["--no-announce"]:
            announce = False
            rest = rest[1:]
        else:
            break
    if rest[:1] == ["--"]:
        rest = rest[1:]
    if not rest:
        sys.exit("usage: agent.py submit [--name NAME] [--join-frame FILE] "
                 "[--join-chat CHAT] [--join-frame-file FILE] [--timeout S] "
                 "[--summoner ID] [--join-cursor SEQ] "
                 "[--cold-boot|--no-cold-boot] [--no-announce] "
                 "-- cmd [args...]")
    if cold_boot is None:
        cold_boot = join_cursor is None
    if join_chat and frame_file:
        sys.exit("agent.py: --join-frame and --join-chat are exclusive "
                 "(--join-chat takes --join-frame-file)")
    if (join_frame_file or timeout) and not join_chat:
        sys.exit("agent.py: --join-frame-file/--timeout need --join-chat")
    if join_chat:
        agent_id = submit_with_join(name, join_chat, join_frame_file,
                                    timeout, rest, summoner, join_cursor,
                                    cold_boot, announce)
        print(agent_id)
        return
    if announce:
        prefix = (c2_announce_prefix(name, summoner, join_cursor,
                                     cold_boot)
                  + 'exec "$@"')
        rest = ["bash", "-c", prefix, "c2-announce-wrapper"] + rest
    if frame_file:
        agent_id = submit_with_frame(name, frame_file, rest)
    else:
        rc, out, err = bridge("submit", "--", *rest)
        # job submit prints the id on stdout (last token)
        agent_id = out.split()[-1] if out else "unknown"
        if rc != 0:
            sys.stderr.write((err or out) + "\n")
            sys.exit(1)
    ledger_append({"event": "submit", "agent_id": agent_id,
                   "name": name, "cmd": rest, "rc": 0,
                   "join_frame": bool(frame_file),
                   "announce": announce, "summoner": summoner,
                   "join_cursor": join_cursor, "cold_boot": cold_boot})
    print(agent_id)


def submit_with_frame(name, frame_file, cmd):
    """Submit via a spec file carrying the join frame in spec.env.

    The worker reads $JOIN_FRAME at boot — zero worker changes, works for
    every shell worker. Frame is inert for workers that ignore it.
    """
    import tempfile
    try:
        with open(frame_file) as f:
            frame = f.read()
    except OSError as e:
        sys.exit("agent.py: cannot read --join-frame %s: %s" % (frame_file, e))
    spec = {"cmd": cmd, "name": name,
            "env": {"JOIN_FRAME": frame,
                    "JOIN_FRAME_VERSION": JOIN_FRAME_VERSION}}
    local = tempfile.mktemp(prefix="join-spec-", suffix=".json")
    remote = "/tmp/" + os.path.basename(local)
    with open(local, "w") as f:
        json.dump(spec, f)
    p = subprocess.run([sys.executable, XFER_PY, "put", local, remote],
                       capture_output=True, text=True, timeout=120)
    os.unlink(local)
    if p.returncode != 0:
        sys.exit("agent.py: xfer put failed: %s" % (p.stderr or p.stdout))
    rc, out, err = bridge("submit", remote)
    agent_id = out.split()[-1] if out else "unknown"
    if rc != 0:
        sys.stderr.write((err or out) + "\n")
        sys.exit(1)
    return agent_id


def cmd_passthrough(event_name, argv):
    rc, out, err = bridge(*argv)
    agent_id = argv[1] if len(argv) > 1 else ""
    if event_name and agent_id:
        ledger_append({"event": event_name, "agent_id": agent_id,
                       "rc": rc, "detail": out[:500]})
    print(out)
    if err and rc != 0:
        sys.stderr.write(err + "\n")


def cmd_roster():
    rc, out, err = bridge("list")
    live = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0][0].isdigit():
            live[parts[0]] = {"status": parts[2],
                              "name": parts[1] if len(parts) > 1 else ""}
    # merge with ledger: latest event per agent
    latest = {}
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                latest[e.get("agent_id", "")] = e
    print(f"{'AGENT_ID':<26} {'NAME':<24} {'LEDGER':<10} {'LIVE':<10} CMD")
    for aid, e in sorted(latest.items()):
        lv = live.get(aid, {})
        cmd = " ".join(e.get("cmd", [])[:4])
        print(f"{aid:<26} {e.get('name',''):<24} "
              f"{e.get('event',''):<10} {lv.get('status','?'):<10} {cmd}")
    orphans = [a for a in live if a not in latest]
    for aid in orphans:
        print(f"{aid:<26} {'':<24} {'':<10} "
              f"{live[aid]['status']:<10} (not in ledger)")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    verb = sys.argv[1]
    rest = sys.argv[2:]
    if verb == "submit":
        cmd_submit(rest)
    elif verb == "roster":
        cmd_roster()
    elif verb in ("list", "status", "log", "result", "kill"):
        cmd_passthrough(verb if verb in ("status", "kill") else "", [verb] + rest)
    else:
        sys.exit("unknown verb: %s\n%s" % (verb, __doc__))


if __name__ == "__main__":
    main()
