#!/usr/bin/env python3
"""fleet-c2: C2-style fleet coordination CLI.

Commands:
  inbox                        read+archive my INBOX
  send <agent-id> <message>     DM one agent (sender is always you)
  broadcast <message>           fleet-wide (local log + directives.md mirror)
  goals                        running agents + published goals
  goal-set <goal>               publish my current goal
  debate <topic> [position]     open/reply to an architecture debate
  done <summary> --artifact P   completion claim WITH proof (artifact required)
  verify <agent-id>             re-check an agent's latest claim
  health                       stale-heartbeat watch (silent-failure detection)
  activity                     first-class awareness snapshot: running agents +
                               cron jobs + bridge daemons + fleet channel tail,
                               anomalies FIRST (--agents-file for DB rows)
  propose <text>                propose a skill change
  endorse <proposal-id>         endorse a proposal
  task new <what> [--for-goal G]  self-task a subtask (no goal = flagged
                               + auto-broadcast, never refused)
  task list [--status open]     open tasks across the fleet
  task done <id> --artifact P   close a task WITH proof
  task request-help <what> --from <agent> [--for-goal G]
                               ask another agent for a subtask
  papers search "<query>" [--max N] [--refresh]
                               arXiv+alphaXiv+free-legs paper search (cached)
  papers brief "<query>" [--max N]
                               search + extractive why-it-matters per hit
  version                      skill version

Env: FLEET_AGENT_ID (your subagent id). Falls back to `unknown-<pid>`.
State: <skill-dir>/state/ (local-first; directives.md mirror is best-effort).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime as _dt
from datetime import timedelta as _td
from datetime import timezone as _tz

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(SKILL_DIR, "state")
VERSION = "0.5.0"

DIRECTIVES = "/home/toxic/.shingle/directives.md"
BRIDGE = os.path.expanduser("~/workspace/skills/awrawr-mcp/bin/exec.py")
HEARTBEAT_STALE_SECS = 600
PAPERS_PY = os.path.expanduser(
    "~/workspace/skills/emergent-enrich/bin/papers.py")
PAPERS_CACHE_TTL_SECS = 24 * 3600  # HFT: keep the fast path hot


def agent_id():
    return os.environ.get("FLEET_AGENT_ID") or f"unknown-{os.getpid()}"


def ensure_dirs():
    for d in ("inbox", "goals", "debates", "claims", "heartbeats", "tasks",
              "papers"):
        os.makedirs(os.path.join(STATE, d), exist_ok=True)


def heartbeat():
    try:
        with open(os.path.join(STATE, "heartbeats", agent_id()), "w") as f:
            f.write(str(int(time.time())))
    except OSError:
        pass


def ts():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:48] or "untitled"


def cmd_inbox(args):
    me = agent_id()
    path = os.path.join(STATE, "inbox", me + ".jsonl")
    msgs = []
    try:
        with open(path) as f:
            msgs = [json.loads(l) for l in f if l.strip()]
    except (OSError, ValueError):
        pass
    if not msgs:
        print(json.dumps({"inbox": [], "count": 0}))
        return
    arch = os.path.join(STATE, "inbox", me + ".archive.jsonl")
    with open(arch, "a") as f:
        for m in msgs:
            f.write(json.dumps(m) + "\n")
    os.remove(path)
    print(json.dumps({"inbox": msgs, "count": len(msgs)}, indent=1))


def cmd_send(args):
    if len(args) < 2:
        sys.exit("usage: send <agent-id> <message>")
    target, message = args[0], " ".join(args[1:])
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", target):
        sys.exit("bad agent id")
    path = os.path.join(STATE, "inbox", target + ".jsonl")
    entry = {"from": agent_id(), "to": target, "ts": ts(), "message": message}
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps({"sent": True, "to": target}))


def _broadcast(message):
    """Append to the local fleet log + best-effort mirror to directives.md.
    Returns True if the directives.md mirror succeeded."""
    me, now = agent_id(), ts()
    entry = {"from": me, "ts": now, "message": message}
    with open(os.path.join(STATE, "broadcast.log"), "a") as f:
        f.write(json.dumps(entry) + "\n")
    # best-effort mirror to the canonical fleet channel on awrawr-pc
    mirrored = False
    if os.path.exists(BRIDGE):
        import subprocess
        import base64
        line = (f"\n## {time.strftime('%Y-%m-%d %H:%M %Z')} — {me} "
                f"(via fleet-c2)\n{message}\n")
        # base64 to avoid shell-quoting traps
        b64 = base64.b64encode(line.encode()).decode()
        r = subprocess.run(
            ["python3", BRIDGE,
             f"echo {b64} | base64 -d >> {DIRECTIVES} && echo MIRRORED"],
            capture_output=True, text=True, timeout=60)
        mirrored = "MIRRORED" in (r.stdout or "")
    return mirrored


def cmd_broadcast(args):
    if not args:
        sys.exit("usage: broadcast <message>")
    message = " ".join(args)
    mirrored = _broadcast(message)
    print(json.dumps({"broadcast": True, "mirrored_to_directives": mirrored}))


def running_agents():
    """Running agent ids from the fleet DB (best-effort)."""
    try:
        sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
        import sqlite3  # noqa  (muse.db is postgres; try direct is overkill)
    except Exception:
        pass
    # Use the muse.db CLI surface via python is not available here; fall back
    # to a tiny postgres query only if psycopg exists. Otherwise: state only.
    agents = []
    try:
        import subprocess
        r = subprocess.run(
            ["python3", "-c",
             "import sys; sys.path.insert(0,'/opt/hatch/skills/muse_db/bin');"
             ],
            capture_output=True, timeout=5)
    except Exception:
        pass
    return agents


def cmd_goals(args):
    out = []
    gdir = os.path.join(STATE, "goals")
    try:
        ids = [f[:-5] for f in os.listdir(gdir) if f.endswith(".json")]
    except OSError:
        ids = []
    for aid in sorted(ids):
        try:
            with open(os.path.join(gdir, aid + ".json")) as f:
                g = json.load(f)
            out.append({"agent": aid, "goal": g.get("goal"),
                        "updated_at": g.get("updated_at"),
                        "status": g.get("status", "active")})
        except (OSError, ValueError):
            pass
    print(json.dumps({"goals": out, "count": len(out),
                      "note": "DB-backed running-agent list: stubbed in 0.1.0, "
                              "see proposals"}, indent=1))


def cmd_goal_set(args):
    if not args:
        sys.exit("usage: goal-set <goal text>")
    me = agent_id()
    doc = {"agent": me, "goal": " ".join(args), "updated_at": ts(),
           "status": "active"}
    with open(os.path.join(STATE, "goals", me + ".json"), "w") as f:
        json.dump(doc, f, indent=1)
    print(json.dumps({"goal_set": True, "agent": me}))


def cmd_debate(args):
    if not args:
        sys.exit("usage: debate <topic> [position/argument]")
    topic = args[0]
    argument = " ".join(args[1:]) if len(args) > 1 else "(opening thread)"
    path = os.path.join(STATE, "debates", slug(topic) + ".jsonl")
    entry = {"agent": agent_id(), "ts": ts(), "topic": topic,
             "argument": argument}
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    # show thread so far
    thread = []
    with open(path) as f:
        for l in f:
            if l.strip():
                thread.append(json.loads(l))
    print(json.dumps({"topic": topic, "thread": thread}, indent=1))


def cmd_done(args):
    artifacts = []
    summary_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--artifact" and i + 1 < len(args):
            artifacts.append(args[i + 1])
            i += 2
        else:
            summary_parts.append(args[i])
            i += 1
    summary = " ".join(summary_parts).strip()
    if not summary:
        sys.exit("usage: done <summary> --artifact <path> [--artifact ...]")
    if not artifacts:
        sys.exit("REFUSED: done-claim requires --artifact (unverified "
                 "done-claims are the unreliable-narrator anti-pattern).")
    me = agent_id()
    claim = {"id": uuid.uuid4().hex[:12], "agent": me, "ts": ts(),
             "summary": summary, "artifacts": artifacts, "status": "claimed"}
    path = os.path.join(STATE, "claims", me + ".jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(claim) + "\n")
    print(json.dumps({"claimed": True, "id": claim["id"],
                      "verify_with": f"fleet-c2 verify {me}"}, indent=1))


def artifact_exists(a):
    # local path, or commit sha (hex, 7-40 chars)
    if re.fullmatch(r"[0-9a-f]{7,40}", a):
        return ("commit", "assumed-present (repo check stubbed in 0.1.0)")
    if os.path.exists(os.path.expanduser(a)):
        return ("file", "exists")
    return (None, "missing")


def cmd_verify(args):
    if not args:
        sys.exit("usage: verify <agent-id>")
    target = args[0]
    path = os.path.join(STATE, "claims", target + ".jsonl")
    try:
        with open(path) as f:
            claims = [json.loads(l) for l in f if l.strip()]
    except (OSError, ValueError):
        print(json.dumps({"agent": target, "verdict": "NO-CLAIMS"}))
        return
    if not claims:
        print(json.dumps({"agent": target, "verdict": "NO-CLAIMS"}))
        return
    c = claims[-1]
    results = []
    ok = True
    for a in c.get("artifacts", []):
        kind, note = artifact_exists(a)
        results.append({"artifact": a, "kind": kind, "note": note})
        if kind is None:
            ok = False
    print(json.dumps({"agent": target, "claim_id": c.get("id"),
                      "summary": c.get("summary"),
                      "verdict": "VERIFIED" if ok else "CHALLENGED",
                      "artifacts": results}, indent=1))


def cmd_health(args):
    now = int(time.time())
    stale = []
    hdir = os.path.join(STATE, "heartbeats")
    try:
        for f in os.listdir(hdir):
            try:
                with open(os.path.join(hdir, f)) as fh:
                    last = int(fh.read().strip() or "0")
                age = now - last
                if age > HEARTBEAT_STALE_SECS:
                    stale.append({"agent": f, "heartbeat_age_secs": age})
            except (OSError, ValueError):
                pass
    except OSError:
        pass
    print(json.dumps({"stale_threshold_secs": HEARTBEAT_STALE_SECS,
                      "stale": stale, "count": len(stale)}, indent=1))


def cmd_propose(args):
    if not args:
        sys.exit("usage: propose <what> -- <why>")
    text = " ".join(args)
    pid = uuid.uuid4().hex[:8]
    entry = {"id": pid, "agent": agent_id(), "ts": ts(), "text": text,
             "endorsements": []}
    with open(os.path.join(STATE, "proposals.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps({"proposed": True, "id": pid}))


def cmd_identity(args):
    """Run the 4-point leader identity check on THIS cell.

    Leader = depth 0 AND agent_id == root_agent_id AND channel == "main"
    AND the conversation thread is the main-chat thread. The env var's
    channel field can false-positive as "main" in side-chat cells, so the
    thread id is the tiebreaker. Usage: identity [--claim-leader]"""
    import os
    raw = os.environ.get("JARVIS_TRACE_CONTEXT", "")
    info = {}
    if raw:
        try:
            info = json.loads(raw)
        except ValueError:
            info = {"parse_error": True}
    depth = info.get("agent_depth")
    aid = info.get("agent_id")
    root = info.get("root_agent_id")
    channel = info.get("channel")
    thread = info.get("thread_id")
    # main-chat thread: the leader's session thread. Any other thread is
    # a side chat / WhatsApp / worker context — not the leader.
    is_main_thread = bool(thread) and thread == os.environ.get(
        "FLEET_MAIN_THREAD", "")
    checks = {
        "depth_is_zero": depth == 0,
        "id_matches_root": bool(aid) and aid == root,
        "channel_is_main": channel == "main",
        "thread_is_main_chat": is_main_thread,
    }
    leader = all(checks.values())
    claiming = "--claim-leader" in args
    verdict = "LEADER" if leader else "NOT-LEADER"
    order = None
    if claiming and not leader:
        verdict = "DEPERSONALIZED"
        order = ("rename and repersonify immediately: choose your own name, "
                 "update IDENTITY.md, stop using the Shingle name. "
                 "Keep working as yourself.")
    print(json.dumps({
        "agent_id": aid, "depth": depth, "channel": channel,
        "thread_id": thread, "checks": checks, "verdict": verdict,
        "rename_order": order,
        "note": ("channel field can false-positive as 'main' in side-chat "
                 "cells; thread id is the tiebreaker. Set FLEET_MAIN_THREAD "
                 "to the main-chat thread id to enable the thread check."),
    }, indent=1))


def cmd_endorse(args):
    if not args:
        sys.exit("usage: endorse <proposal-id>")
    pid = args[0]
    me = agent_id()
    path = os.path.join(STATE, "proposals.jsonl")
    try:
        with open(path) as f:
            lines = [l for l in f if l.strip()]
    except OSError:
        sys.exit("no proposals yet")
    found = False
    out = []
    for l in lines:
        p = json.loads(l)
        if p.get("id") == pid:
            found = True
            if me not in p["endorsements"]:
                p["endorsements"].append(me)
        out.append(p)
    if not found:
        sys.exit("proposal not found")
    with open(path, "w") as f:
        for p in out:
            f.write(json.dumps(p) + "\n")
            if p.get("id") == pid:
                print(json.dumps({"endorsed": True, "id": pid,
                                  "endorsements": p["endorsements"]}))
                return


def _task_path(tid):
    return os.path.join(STATE, "tasks", tid + ".json")


def _load_task(tid):
    try:
        with open(_task_path(tid)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _save_task(t):
    with open(_task_path(t["id"]), "w") as f:
        json.dump(t, f, indent=1)


def _parse_task_flags(args):
    """Split positional text from --for-goal/--reason/--from/--artifact."""
    text, flags = [], {}
    i = 0
    while i < len(args):
        if args[i] in ("--for-goal", "--reason", "--from", "--artifact") \
                and i + 1 < len(args):
            key = args[i][2:].replace("-", "_")
            flags.setdefault(key, []).append(args[i + 1])
            i += 2
        else:
            text.append(args[i])
            i += 1
    return " ".join(text).strip(), flags


def cmd_task_new(args):
    what, flags = _parse_task_flags(args)
    goal = (flags.get("for_goal") or [""])[0].strip()
    reason = (flags.get("reason") or [""])[0].strip()
    if not what:
        sys.exit("usage: task new \"<what>\" [--for-goal \"<assigned goal>\"] "
                 "[--reason \"<why>\"]")
    # FORWARD-ONLY, never refuse (Chris 18:15): a subtask that cannot name its
    # parent goal is still created — flagged needs-human-review and
    # auto-broadcast for full transparency. Human-absolute is enforced by
    # visibility (Chris reads the fleet log and redirects), never by gates.
    needs_review = not goal
    if needs_review:
        goal = "UNCLAIMED"
    tid = "t-" + uuid.uuid4().hex[:8]
    t = {"id": tid, "what": what, "for_goal": goal, "reason": reason,
         "agent": agent_id(), "ts": ts(), "status": "open",
         "needs_human_review": needs_review,
         "help_from": None, "artifacts": [], "done_ts": None}
    _save_task(t)
    broadcasted = False
    if needs_review:
        broadcasted = _broadcast(
            f"UNCLAIMED TASK {tid} by {agent_id()} (no parent goal named): "
            f"{what}" + (f" — reason: {reason}" if reason else "") +
            ". Flagged needs-human-review; redirect or adopt as you see fit.")
    print(json.dumps({"tasked": True, "id": tid, "for_goal": goal,
                      "needs_human_review": needs_review,
                      "broadcasted": broadcasted}, indent=1))


def cmd_task_list(args):
    _, flags = _parse_task_flags(args)
    status = (flags.get("status") or ["open"])[0]
    agent = (flags.get("from") or [None])[0]
    out = []
    tdir = os.path.join(STATE, "tasks")
    try:
        for f in sorted(os.listdir(tdir)):
            if not f.endswith(".json"):
                continue
            try:
                with open(os.path.join(tdir, f)) as fh:
                    t = json.load(fh)
            except (OSError, ValueError):
                continue
            if status != "all" and t.get("status") != status:
                continue
            if agent and t.get("agent") != agent:
                continue
            out.append(t)
    except OSError:
        pass
    print(json.dumps({"tasks": out, "count": len(out)}, indent=1))


def cmd_task_done(args):
    what, flags = _parse_task_flags(args)
    tid = what.split()[0] if what else ""
    artifacts = flags.get("artifact", [])
    if not tid:
        sys.exit("usage: task done <id> --artifact <path> [--artifact ...]")
    if not artifacts:
        sys.exit("REFUSED: task done requires --artifact (same proof rule "
                 "as done-claims).")
    t = _load_task(tid)
    if not t:
        sys.exit(f"no such task: {tid}")
    if t.get("agent") != agent_id():
        sys.exit("REFUSED: only the task owner (or their parent) may close "
                 f"it — owner is {t.get('agent')}.")
    if t["status"] == "done":
        sys.exit(f"task {tid} is already done.")
    t["status"] = "done"
    t["artifacts"] = artifacts
    t["done_ts"] = ts()
    _save_task(t)
    print(json.dumps({"done": True, "id": tid}, indent=1))


def cmd_task_request_help(args):
    what, flags = _parse_task_flags(args)
    target = (flags.get("from") or [""])[0].strip()
    goal = (flags.get("for_goal") or [""])[0].strip()
    reason = (flags.get("reason") or [""])[0].strip()
    if not what or not target:
        sys.exit("usage: task request-help \"<what>\" --from <agent-id> "
                 "[--for-goal \"<assigned goal>\"] [--reason \"<why>\"]")
    # Same forward-only rule as task new: missing parent goal never refuses —
    # the request is created, flagged, and broadcast for transparency.
    needs_review = not goal
    if needs_review:
        goal = "UNCLAIMED"
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", target):
        sys.exit("bad agent id")
    tid = "t-" + uuid.uuid4().hex[:8]
    t = {"id": tid, "what": what, "for_goal": goal, "reason": reason,
         "agent": agent_id(), "ts": ts(), "status": "open",
         "needs_human_review": needs_review,
         "help_from": target, "artifacts": [], "done_ts": None}
    _save_task(t)
    # deliver to the target's inbox
    entry = {"from": agent_id(), "to": target, "ts": ts(),
             "kind": "task-request", "task_id": tid, "for_goal": goal,
             "needs_human_review": needs_review,
             "message": f"help requested on subtask {tid}: {what}"}
    if reason:
        entry["reason"] = reason
    path = os.path.join(STATE, "inbox", target + ".jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    broadcasted = False
    if needs_review:
        broadcasted = _broadcast(
            f"UNCLAIMED HELP-REQUEST {tid} by {agent_id()} to {target} "
            f"(no parent goal named): {what}. Flagged needs-human-review.")
    print(json.dumps({"requested": True, "task_id": tid, "to": target,
                      "needs_human_review": needs_review,
                      "broadcasted": broadcasted}, indent=1))


def cmd_task(args):
    if not args:
        sys.exit("usage: task <new|list|done|request-help> ...")
    sub, rest = args[0], args[1:]
    if sub == "new":
        cmd_task_new(rest)
    elif sub == "list":
        cmd_task_list(rest)
    elif sub == "done":
        cmd_task_done(rest)
    elif sub == "request-help":
        cmd_task_request_help(rest)
    else:
        sys.exit(f"unknown task subcommand: {sub}")


def _papers_cache_path(query, max_n):
    key = hashlib.sha1(f"{query}\x00{max_n}".encode()).hexdigest()[:16]
    return os.path.join(STATE, "papers", f"q-{key}.json")


def _papers_search_live(query, max_n):
    """Run papers.py (arXiv + alphaXiv + other free legs). Wraps, never
    reimplements. Returns (papers_list, meta_dict). Degrades honestly:
    failed legs are reported, not hidden."""
    cmd = [sys.executable, PAPERS_PY, "--query", query, "--max", str(max_n),
           "--format", "jsonl", "--no-audit", "--timeout", "5"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:
        return [], {"ok": False, "error": f"papers.py failed: {e}"}
    papers, meta = [], {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if obj.get("type") == "meta":
            meta = obj
        elif obj.get("type") == "paper":
            papers.append(obj)
    if not meta:
        meta = {"ok": False, "error": "no meta line from papers.py",
                "stderr": proc.stderr[-500:]}
    return papers, meta


def _papers_load(query, max_n, force_refresh=False):
    """Cache-first paper search. Cache hit = instant (HFT: fast path hot).
    Returns (papers, meta, from_cache)."""
    path = _papers_cache_path(query, max_n)
    if not force_refresh and os.path.exists(path):
        try:
            with open(path) as f:
                cached = json.load(f)
            age = time.time() - cached.get("cached_at", 0)
            if age < PAPERS_CACHE_TTL_SECS:
                return (cached["papers"], cached["meta"], True)
        except (OSError, ValueError, KeyError):
            pass
    papers, meta = _papers_search_live(query, max_n)
    try:
        with open(path, "w") as f:
            json.dump({"query": query, "max_n": max_n, "papers": papers,
                       "meta": meta, "cached_at": time.time()}, f)
    except OSError:
        pass
    return papers, meta, False


def _extractive_why(abstract, title="", n_sentences=2):
    """LLM-free extractive summary: top sentences by title-word overlap +
    position (same heuristic as papers.py --s2dupe extractive TLDR)."""
    if not abstract:
        return ""
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", abstract)
             if len(s.strip()) > 20]
    if not sents:
        return abstract[:300]
    title_words = set(re.findall(r"[a-z]{4,}", title.lower()))
    scored = []
    for i, s in enumerate(sents):
        words = set(re.findall(r"[a-z]{4,}", s.lower()))
        overlap = len(words & title_words)
        scored.append((overlap - i * 0.1, i, s))
    scored.sort(reverse=True)
    top = sorted(scored[:n_sentences], key=lambda x: x[1])
    return " ".join(s for _, _, s in top)


def _paper_link(p):
    for k in ("url", "arxiv_url", "doi_url", "openalex_url"):
        if p.get(k):
            return p[k]
    pid = p.get("id") or p.get("arxiv_id") or ""
    if pid and re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", pid):
        return f"https://arxiv.org/abs/{pid}"
    return ""


def cmd_papers_search(args):
    query, max_n, force = "", 8, False
    rest = []
    i = 0
    while i < len(args):
        if args[i] == "--max" and i + 1 < len(args):
            try:
                max_n = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        elif args[i] == "--refresh":
            force = True
            i += 1
        else:
            rest.append(args[i])
            i += 1
    query = " ".join(rest).strip()
    if not query:
        sys.exit('usage: papers search "<query>" [--max N] [--refresh]')
    papers, meta, from_cache = _papers_load(query, max_n, force)
    legs = meta.get("legs", [])
    leg_note = "; ".join(
        f"{l.get('leg')}:{'ok' if l.get('ok') else 'FAIL'}"
        for l in legs) if legs else meta.get("error", "no leg info")
    out = []
    for p in papers[:max_n]:
        out.append({"id": p.get("id") or p.get("arxiv_id"),
                    "title": p.get("title"),
                    "authors": (p.get("authors") or [])[:4],
                    "published": p.get("published") or p.get("year"),
                    "link": _paper_link(p)})
    print(json.dumps({
        "query": query, "from_cache": from_cache,
        "papers_found": len(papers), "legs": leg_note,
        "papers": out,
        "note": ("cache hit — instant" if from_cache else
                 "live search via papers.py (arXiv+alphaXiv+free legs)")},
        indent=1))


def cmd_papers_brief(args):
    query, max_n, force = "", 6, False
    rest = []
    i = 0
    while i < len(args):
        if args[i] == "--max" and i + 1 < len(args):
            try:
                max_n = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        elif args[i] == "--refresh":
            force = True
            i += 1
        else:
            rest.append(args[i])
            i += 1
    query = " ".join(rest).strip()
    if not query:
        sys.exit('usage: papers brief "<query>" [--max N] [--refresh]')
    papers, meta, from_cache = _papers_load(query, max_n, force)
    briefs = []
    for p in papers[:max_n]:
        title = p.get("title", "")
        abstract = p.get("abstract", "")
        # Prefer a curated why_matters when the record carries one;
        # otherwise extractive summary (LLM-free; --tldr-llm needs NIM creds).
        why = p.get("why_matters") or _extractive_why(abstract, title)
        briefs.append({"id": p.get("id") or p.get("arxiv_id"),
                       "title": title, "link": _paper_link(p),
                       "why_it_matters": why})
    print(json.dumps({
        "query": query, "from_cache": from_cache,
        "papers_found": len(papers), "briefs": briefs}, indent=1))


def cmd_papers(args):
    if not args:
        sys.exit('usage: papers <search|brief> "<query>" [--max N] '
                 '[--refresh]')
    sub, rest = args[0], args[1:]
    if sub == "search":
        cmd_papers_search(rest)
    elif sub == "brief":
        cmd_papers_brief(rest)
    else:
        sys.exit(f"unknown papers subcommand: {sub}")


# ---------------------------------------------------------------------------
# activity — first-class awareness snapshot (0.5.0, Chris's order 2026-09-14)
#
# One snapshot of ALL running activity: agents + cron jobs + bridge daemons
# + fleet channel tail, anomalies FIRST. The leader (and every coordinator)
# runs this before each major work block and after each worker completion —
# reactive awareness ("I learned it from a handoff") is a defect.
#
# DB data: the CLI cannot reach muse.db directly (no driver, no creds in the
# sandbox). The leader injects the running-agents snapshot via --agents-file,
# --agents JSON, or FLEET_DB_AGENTS env. Without it, activity degrades to
# heartbeats + published goals and says so loudly. See SKILL.md for the
# leader one-liner that produces the snapshot file.
# ---------------------------------------------------------------------------

ACTIVITY_SILENT_SECS = 300           # flag agents quiet longer than this
ACTIVITY_BRIDGE_TIMEOUT = 20         # single bridge call budget (total <30s)
ACTIVITY_FREEZE_KEYWORDS = ("freeze", "frozen", "full stop", "halt all",
                            "fleet halt")
ACTIVITY_UNFREEZE_KEYWORDS = ("unfreeze", "resume fleet", "lift the freeze",
                              "freeze lifted", "freeze over", "freeze ended")
ACTIVITY_LOCAL_FREEZE = os.path.expanduser("~/workspace/FLEET_FREEZE")
ACTIVITY_DAEMON_BAD = re.compile(
    r"error|fail|down|exception|traceback|exit\s*[1-9]", re.I)
_DENVER_TZ = _tz(_td(hours=-6), name="MDT")  # America/Denver (MDT in Sept)


def _denver_today():
    return _dt.now(_DENVER_TZ).strftime("%Y-%m-%d")


def _activity_db_agents(args):
    """Injected muse.db rows: [{agent_id, status, parent_agent_id, depth,
    model, updated_at}, ...]. Accepts the raw muse.db JSON too (a list, or
    {"rows": [...]} / {"agents": [...]}). Returns (normalized_rows, source)."""
    raw, src, path = None, None, None
    i = 0
    while i < len(args):
        if args[i] == "--agents-file" and i + 1 < len(args):
            path = args[i + 1]
            i += 2
        elif args[i] == "--agents" and i + 1 < len(args):
            raw, src = args[i + 1], "--agents"
            i += 2
        else:
            i += 1
    if path:
        try:
            with open(os.path.expanduser(path)) as f:
                raw = f.read()
            src = "file:" + path
        except OSError:
            pass
    if raw is None:
        env = os.environ.get("FLEET_DB_AGENTS", "").strip()
        if env:
            raw, src = env, "env:FLEET_DB_AGENTS"
    if not raw:
        return [], None
    try:
        data = json.loads(raw)
    except ValueError:
        return [], None
    rows = (data if isinstance(data, list)
            else data.get("rows") or data.get("agents") or [])
    norm = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        try:
            upd = r.get("updated_at")
            if upd is None:
                upd = r.get("upd", 0)
            upd = int(upd)
        except (TypeError, ValueError):
            upd = 0
        norm.append({
            "agent_id": r.get("agent_id") or r.get("aid") or "?",
            "parent": r.get("parent_agent_id") or r.get("parent") or "-",
            "depth": r.get("depth", r.get("dep", "?")),
            "model": str(r.get("model") or r.get("mdl") or "")[:24],
            "updated_at": upd,
        })
    return norm, src


def _activity_goals():
    out = {}
    gdir = os.path.join(STATE, "goals")
    try:
        for f in os.listdir(gdir):
            if not f.endswith(".json"):
                continue
            try:
                with open(os.path.join(gdir, f)) as fh:
                    out[f[:-5]] = json.load(fh)
            except (OSError, ValueError):
                pass
    except OSError:
        pass
    return out


def _activity_beats():
    """agent_id -> heartbeat age in seconds (from fleet-c2 heartbeats)."""
    out, now = {}, int(time.time())
    hdir = os.path.join(STATE, "heartbeats")
    try:
        for f in os.listdir(hdir):
            try:
                with open(os.path.join(hdir, f)) as fh:
                    last = int((fh.read() or "0").strip())
                out[f] = now - last
            except (OSError, ValueError):
                pass
    except OSError:
        pass
    return out


_TS_FULL_RE = re.compile(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})")
_TS_BARE_RE = re.compile(r"(?<!\d)(\d{2}:\d{2})(?::\d{2})?(?!\d)")


def _norm_ts(text):
    """Extract 'YYYY-MM-DD HH:MM' from text; bare HH:MM is assumed today.
    Lexicographically comparable. Returns '' when nothing found."""
    m = _TS_FULL_RE.search(text or "")
    if m:
        return "%s %s" % (m.group(1), m.group(2))
    m = _TS_BARE_RE.search(text or "")
    if m:
        return "%s %s" % (_denver_today(), m.group(1))
    return ""


def _fmt_age(secs):
    if secs is None or secs < 0:
        return "?"
    if secs < 60:
        return "%ds" % secs
    if secs < 3600:
        return "%dm" % (secs // 60)
    return "%dh%02dm" % (secs // 3600, (secs % 3600) // 60)


def _freeze_from_lines(lines):
    """Newest freeze/unfreeze broadcast wins. Returns
    (frozen, freeze_ts, evidence_snippet)."""
    freeze, unfreeze = [], []
    for ln in lines:
        low = ln.lower()
        t = _norm_ts(ln)
        if not t:
            continue
        if any(k in low for k in ACTIVITY_FREEZE_KEYWORDS):
            freeze.append((t, ln.strip()[:110]))
        if any(k in low for k in ACTIVITY_UNFREEZE_KEYWORDS):
            unfreeze.append((t, ln.strip()[:110]))
    if not freeze:
        return False, "", ""
    fts, fhit = max(freeze)
    if unfreeze:
        uts, uhit = max(unfreeze)
        if uts > fts:
            return False, fts, "unfrozen %s: %s" % (uts, uhit)
    return True, fts, "%s: %s" % (fts, fhit)


def _activity_bridge():
    """ONE bridge call: directives.md tail + freeze marker + pitchfork list.
    Returns dict; ok=False with an error string on failure (degrades
    honestly — daemon and channel sections go blind, loudly)."""
    out = {"ok": False, "error": "", "channel": [], "freeze_marker": False,
           "daemons": []}
    if not os.path.exists(BRIDGE):
        out["error"] = "no bridge client (awrawr-mcp/bin/exec.py missing)"
        return out
    cmd = ("tail -200 " + DIRECTIVES + " 2>/dev/null; "
           "echo '__FLEETC2_MARKER__'; "
           "ls /home/toxic/.shingle/freeze /home/toxic/.shingle/FREEZE "
           "2>/dev/null || echo no-marker; "
           "echo '__FLEETC2_PITCHFORK__'; "
           "(pitchfork list 2>&1 | head -60) || echo pitchfork-unavailable")
    try:
        r = subprocess.run(["python3", BRIDGE, cmd], capture_output=True,
                           text=True, timeout=ACTIVITY_BRIDGE_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as e:
        out["error"] = "bridge call failed: %s" % e
        return out
    body = r.stdout or ""
    if "__FLEETC2_MARKER__" not in body:
        out["error"] = ("bridge returned no marker; stderr: %s"
                         % (r.stderr or "")[:160])
        return out
    chan, rest = body.split("__FLEETC2_MARKER__", 1)
    parts = rest.split("__FLEETC2_PITCHFORK__", 1)
    mark = parts[0]
    pf = parts[1] if len(parts) > 1 else ""
    out["channel"] = [l for l in chan.splitlines() if l.strip()]
    out["freeze_marker"] = "no-marker" not in mark
    out["daemons"] = [l for l in pf.splitlines() if l.strip()]
    out["ok"] = True
    return out


def _channel_entries(lines, n=5):
    """Split directives.md tail into entries (## headers), newest last."""
    entries, cur = [], None
    for ln in lines:
        if ln.startswith("## "):
            if cur:
                entries.append(cur)
            cur = {"head": ln[3:].strip(), "body": ""}
        elif cur is not None and not cur["body"] and ln.strip():
            cur["body"] = ln.strip()[:140]
    if cur:
        entries.append(cur)
    return entries[-n:]


def _cron_jobs():
    """Job definitions from ~/workspace/cron.d/<sched>/<name>.md.
    Schedule from directory, or __interval@ tag in the filename."""
    base = os.path.expanduser("~/workspace/cron.d")
    jobs = []
    try:
        scheds = sorted(os.listdir(base))
    except OSError:
        return jobs
    for sched in scheds:
        sdir = os.path.join(base, sched)
        if not os.path.isdir(sdir) or sched.startswith((".", "_")):
            continue
        try:
            files = sorted(os.listdir(sdir))
        except OSError:
            continue
        for fn in files:
            if fn.startswith((".", "_")):
                continue
            name = fn[:-3] if fn.endswith(".md") else fn
            m = re.search(r"__interval@(.+)$", name)
            jobs.append({"name": name.split("__interval@")[0],
                         "schedule": ("every " + m.group(1)) if m else sched,
                         "file": fn})
    return jobs


def _cron_evidence(jobs):
    """Last-run evidence per job from today's memory log (heuristic: the
    watchdog jobs append entries there). Returns {name: 'YYYY-MM-DD HH:MM'}."""
    mem = os.path.expanduser("~/memory/%s.md" % _denver_today())
    try:
        with open(mem) as f:
            text = f.read()
    except OSError:
        return {}
    lines = text.splitlines()
    ev = {}
    for j in jobs:
        nm, last = j["name"], ""
        for ln in lines:
            if nm in ln:
                t = _norm_ts(ln)
                if t:
                    last = t
        if last:
            ev[nm] = last
    return ev


def cmd_activity(args):
    t0 = time.time()
    now = int(t0)
    anomalies = []
    out = []

    # ---- bridge first (single call; everything bridge-side hangs off it) --
    bridge = _activity_bridge()
    if not bridge["ok"]:
        anomalies.append("BRIDGE-BLIND: %s — daemon + channel sections "
                         "unavailable" % bridge["error"])

    # ---- freeze state: marker files + newest freeze/unfreeze broadcast ----
    scan_lines = list(bridge.get("channel", []))
    try:
        with open(os.path.join(STATE, "broadcast.log")) as f:
            scan_lines += [l for l in f.read().splitlines()
                           if l.strip()][-40:]
    except OSError:
        pass
    frozen, freeze_ts, freeze_ev = _freeze_from_lines(scan_lines)
    if os.path.exists(ACTIVITY_LOCAL_FREEZE):
        frozen = True
        freeze_ev = (freeze_ev + " + local marker ~/workspace/FLEET_FREEZE"
                     ).strip(" +")
    if bridge.get("freeze_marker"):
        frozen = True
        freeze_ev = (freeze_ev + " + bridge marker "
                     "/home/toxic/.shingle/freeze").strip(" +")

    # ---- agents -----------------------------------------------------------
    db_agents, db_src = _activity_db_agents(args)
    goals = _activity_goals()
    beats = _activity_beats()
    agent_lines = []
    if db_agents:
        for a in db_agents:
            aid = a["agent_id"]
            age = now - a["updated_at"] if a["updated_at"] else -1
            g = goals.get(aid)
            flags = []
            if 0 <= age and age > ACTIVITY_SILENT_SECS:
                flags.append("SILENT>%s" % _fmt_age(ACTIVITY_SILENT_SECS))
                anomalies.append(
                    "SILENT agent %s quiet %s (depth %s, parent %s)"
                    % (aid, _fmt_age(age), a["depth"], a["parent"]))
            if not g:
                flags.append("NO-GOAL")
                anomalies.append("GOAL-LESS agent %s running with no "
                                 "published goal" % aid)
            goal_txt = (g.get("goal", "")[:60] if g else "—")
            agent_lines.append(
                "%s d=%s age=%s goal=\"%s\"%s"
                % (aid, a["depth"], _fmt_age(age), goal_txt,
                   (" [" + ",".join(flags) + "]") if flags else ""))
        agent_src = "muse.db via %s" % db_src
    else:
        anomalies.append("DEGRADED agent list: no DB snapshot injected — run "
                         "with --agents-file (see SKILL.md). Showing "
                         "heartbeats + published goals only.")
        for aid in sorted(set(goals) | set(beats)):
            age = beats.get(aid, -1)
            g = goals.get(aid)
            flags = []
            if 0 <= age and age > ACTIVITY_SILENT_SECS:
                flags.append("SILENT>%s" % _fmt_age(ACTIVITY_SILENT_SECS))
                anomalies.append("SILENT agent %s quiet %s (heartbeat)"
                                 % (aid, _fmt_age(age)))
            goal_txt = (g.get("goal", "")[:60] if g else "—")
            agent_lines.append(
                "%s age=%s goal=\"%s\"%s"
                % (aid, _fmt_age(age), goal_txt,
                   (" [" + ",".join(flags) + "]") if flags else ""))
        agent_src = "heartbeats+goals (DEGRADED, no DB)"

    # ---- cron jobs --------------------------------------------------------
    jobs = _cron_jobs()
    ev = _cron_evidence(jobs)
    cron_lines = []
    for j in jobs:
        last = ev.get(j["name"], "—")
        flag = ""
        if frozen and freeze_ts and last != "—" and last > freeze_ts:
            flag = " [FIRING-DURING-FREEZE]"
            anomalies.append(
                "FROZEN-BUT-FIRING cron %s (%s) last evidence %s, freeze "
                "since %s" % (j["name"], j["schedule"], last, freeze_ts))
        cron_lines.append("%s (%s) last=%s%s"
                          % (j["name"], j["schedule"], last, flag))

    # ---- daemons (bridge) ---------------------------------------------------
    daemon_lines = []
    for d in bridge.get("daemons", []):
        flag = ""
        if ACTIVITY_DAEMON_BAD.search(d) and "unavailable" not in d.lower():
            flag = " [ERRORED]"
            anomalies.append("ERRORED daemon: %s" % d.strip()[:160])
        daemon_lines.append(d.strip()[:160] + flag)

    # ---- fleet channel tail -------------------------------------------------
    chan_lines = []
    for e in _channel_entries(bridge.get("channel", [])):
        head = e["head"]
        chan_lines.append("%s%s" % (head[:110],
                                    (" — " + e["body"]) if e["body"] else ""))

    # ---- render: anomalies FIRST -------------------------------------------
    out.append("FLEET ACTIVITY — %s (took %.1fs)"
               % (time.strftime("%Y-%m-%d %H:%M %Z"), time.time() - t0))
    out.append("=== ANOMALIES (%d) ===" % len(anomalies))
    if anomalies:
        out.extend("! " + a for a in anomalies)
    else:
        out.append("(none)")
    out.append("=== FREEZE: %s ==="
               % ("ACTIVE since %s (%s)" % (freeze_ts, freeze_ev)
                  if frozen else "not active"))
    out.append("=== AGENTS (%d) [%s] ===" % (len(agent_lines), agent_src))
    out.extend(agent_lines if agent_lines else ["(none seen)"])
    out.append("=== CRON JOBS (%d) ===" % len(cron_lines))
    out.extend(cron_lines if cron_lines else ["(none found)"])
    out.append("=== DAEMONS — awrawr-pc (%d) ===" % len(daemon_lines))
    out.extend(daemon_lines if daemon_lines else ["(unavailable — see anomaly)"])
    out.append("=== FLEET CHANNEL (last %d) ===" % len(chan_lines))
    out.extend(chan_lines if chan_lines else ["(unavailable — see anomaly)"])
    print("\n".join(out))


COMMANDS = {
    "inbox": cmd_inbox, "send": cmd_send, "broadcast": cmd_broadcast,
    "goals": cmd_goals, "goal-set": cmd_goal_set, "debate": cmd_debate,
    "done": cmd_done, "verify": cmd_verify, "health": cmd_health,
    "propose": cmd_propose, "endorse": cmd_endorse, "identity": cmd_identity,
    "task": cmd_task, "papers": cmd_papers, "activity": cmd_activity,
}


def main():
    ensure_dirs()
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "version":
        print(json.dumps({"fleet-c2": VERSION}))
        return
    fn = COMMANDS.get(cmd)
    if not fn:
        sys.exit(f"unknown command: {cmd}")
    heartbeat()
    fn(sys.argv[2:])


if __name__ == "__main__":
    main()
