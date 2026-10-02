#!/usr/bin/env python3
"""Per-lane heartbeat poller — state/logic half of Pulse's lane pollers.

SPLIT OF RESPONSIBILITIES
  This script (runs on yote, no chat tools, pure stdlib):
    - stall verdicts from the worker's chat observation (+ file-mtime fallback)
    - nudge-text generation THROUGH THE SIDE-CHANNEL SHIM's format_safe
      (canonical: /home/toxic/estate/hatch/sidechat_shim.py). "The cron must
      properly use the shim": every nudge is shaped by the shim, never
      hand-rolled. If the shim cannot be imported, no nudge is emitted —
      fail loud, never send unshaped text.
    - quarantine checks through the shim's is_quarantined (single source of
      truth for the refusal string)
    - cooldown / escalation counters, append-only JSONL log per lane

  The cron worker (main-agent runtime, holds the chat tools) does:
    - chat.read_messages on the lane chat -> newest lane-agent (assistant)
      message age -> passes --chat-silent-min
    - sends the nudge via chat.send_message only when this script says
      status == "stalled"
    - verifies arrival itself via chat.read_messages
    - stays silent on "ok" (one-line run summary, no chat noise, no fleet)

COMMANDS
  check --lane L --chat-silent-min N   verdict + state update (N<0: chat read failed)
  check --lane L --chat-gone           lane chat archived/completed
  nudge-text --lane L --silent-min N   print the shim-shaped nudge (one line)
  is-quarantined                       read reply text on stdin, print true/false
  log-nudge --lane L --submission ID   record a sent nudge
  log-reply --lane L --quarantined B   record lane reply; non-quarantined resets stall
  escalate-reset --lane L              record a fleet escalation, reset counters
  self-test                            pure checks, no side effects beyond tmp state

EXIT CODES: 0 ok (verdicts included), 2 usage error, 3 shim unavailable.
"""

import argparse
import json
import os
import sys
import time

# ---- tunables (documented; change deliberately) ---------------------------
STALL_MINUTES = 30            # chat silence beyond this => stalled
NUDGE_COOLDOWN_MINUTES = 60   # minimum gap between nudges to the same lane
ESCALATE_AFTER_STALLED = 3    # consecutive stalled polls before fleet escalation
FILE_FALLBACK_MINUTES = 30    # same threshold applied to agent-dir mtimes

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE, "state")
AGENTS_DIR = "/home/toxic/estate/hatch/agents"
SHIM_DIR = "/home/toxic/estate/hatch"

# ---- shim import (hard dependency: no shim => no nudges) ------------------
SHIM_OK = False
SHIM_ERR = ""
try:
    sys.path.insert(0, SHIM_DIR)
    from sidechat_shim import format_safe, is_quarantined  # noqa: E402
    SHIM_OK = True
except Exception as e:  # never raise: the reshim cron runs unattended
    SHIM_ERR = f"{type(e).__name__}: {e}"


# ---- nudge text ------------------------------------------------------------
# Behavioral, no authority-override shapes. The runtime stamps its own
# unforgeable "Message sent from <chat>." header; the body claims nothing.
# Verified trigger-free by self-test (format_safe must return it unchanged).
NUDGE_TEMPLATE = (
    "Pulse poller ping for the {lane} lane — automated heartbeat. "
    "No lane activity seen for about {mins} minutes. "
    "If you're mid-task, keep going and post a brief status line in your chat "
    "when you can. "
    "If you're stuck or blocked, say what's blocking and what you need. "
    "— Pulse (Ember's crew)"
)


def build_nudge(lane, silent_min):
    if not SHIM_OK:
        return None, f"shim unavailable: {SHIM_ERR}"
    lane_title = (lane or "?").strip().capitalize() or "?"
    text = NUDGE_TEMPLATE.format(lane=lane_title, mins=int(max(0, silent_min)))
    safe = format_safe(text)
    if not safe:
        return None, "shim formatted the nudge to empty"
    return safe, ""


# ---- state -----------------------------------------------------------------
def _state_path(lane):
    return os.path.join(STATE_DIR, f"{lane}.json")


def _log_path(lane):
    return os.path.join(STATE_DIR, f"{lane}.jsonl")


def load_state(lane):
    default = {
        "lane": lane,
        "last_poll_ts": 0,
        "last_nudge_ts": 0,
        "last_nudge_submission": None,
        "consecutive_stalled": 0,
        "escalated": False,
        "chat_gone_noted": False,
        "last_verdict": None,
        "updated_ts": 0,
    }
    try:
        with open(_state_path(lane)) as f:
            saved = json.load(f)
        default.update({k: v for k, v in saved.items() if k in default})
    except (OSError, ValueError):
        pass
    return default


def save_state(lane, state):
    os.makedirs(STATE_DIR, exist_ok=True)
    state["updated_ts"] = time.time()
    tmp = _state_path(lane) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, _state_path(lane))


def log_event(lane, event, **fields):
    os.makedirs(STATE_DIR, exist_ok=True)
    rec = {"ts": time.time(), "lane": lane, "event": event}
    rec.update(fields)
    with open(_log_path(lane), "a") as f:
        f.write(json.dumps(rec) + "\n")


def newest_mtime_age_min(lane):
    """Newest file mtime under agents/<lane>/, in minutes. None if unknown."""
    root = os.path.join(AGENTS_DIR, lane)
    if not os.path.isdir(root):
        return None
    newest = 0
    try:
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                try:
                    mt = os.path.getmtime(os.path.join(dirpath, name))
                except OSError:
                    continue
                if mt > newest:
                    newest = mt
    except OSError:
        return None
    if not newest:
        return None
    return (time.time() - newest) / 60.0


# ---- verdict ----------------------------------------------------------------
def cmd_check(args):
    now = time.time()
    lane = args.lane
    st = load_state(lane)
    st["last_poll_ts"] = now
    out = {"lane": lane, "ts": now, "shim_ok": SHIM_OK}

    if args.chat_gone:
        out["status"] = "chat_gone"
        out["note"] = ("lane chat archived/completed or unreadable — "
                       "poller needs the lane's new chat id; no nudge sent")
        out["already_noted"] = bool(st.get("chat_gone_noted"))
        st["chat_gone_noted"] = True
        st["last_verdict"] = "chat_gone"
        save_state(lane, st)
        log_event(lane, "check", status="chat_gone")
        print(json.dumps(out))
        return 0

    st["chat_gone_noted"] = False  # chat is back / readable again

    if args.chat_silent_min is not None and args.chat_silent_min >= 0:
        silent = float(args.chat_silent_min)
        source = "chat"
    else:
        silent = newest_mtime_age_min(lane)
        source = "file"
        if silent is None:
            out["status"] = "unknown"
            out["note"] = ("no chat observation and no agent-dir files — "
                           "cannot judge; no nudge sent")
            st["last_verdict"] = "unknown"
            save_state(lane, st)
            log_event(lane, "check", status="unknown", source=source)
            print(json.dumps(out))
            return 0

    out["silent_min"] = round(silent, 1)
    out["source"] = source

    if silent < STALL_MINUTES:
        out["status"] = "ok"
        out["note"] = "lane active within threshold"
        st["consecutive_stalled"] = 0
        st["escalated"] = False
        st["last_verdict"] = "ok"
        save_state(lane, st)
        log_event(lane, "check", status="ok", silent_min=round(silent, 1),
                  source=source)
        print(json.dumps(out))
        return 0

    # stalled
    st["consecutive_stalled"] = int(st.get("consecutive_stalled", 0)) + 1
    out["consecutive_stalled"] = st["consecutive_stalled"]
    since_nudge = (now - st["last_nudge_ts"]) / 60.0 if st["last_nudge_ts"] else float("inf")
    out["minutes_since_last_nudge"] = round(since_nudge, 1) if since_nudge != float("inf") else None

    if since_nudge < NUDGE_COOLDOWN_MINUTES:
        out["status"] = "stalled_cooldown"
        out["note"] = (f"stalled but nudged {since_nudge:.0f} min ago "
                       f"(cooldown {NUDGE_COOLDOWN_MINUTES} min); no send")
        st["last_verdict"] = "stalled_cooldown"
        save_state(lane, st)
        log_event(lane, "check", status="stalled_cooldown",
                  silent_min=round(silent, 1), source=source,
                  consecutive=st["consecutive_stalled"])
        print(json.dumps(out))
        return 0

    nudge, err = build_nudge(lane, silent)
    if nudge is None:
        out["status"] = "error"
        out["note"] = f"stalled but nudge blocked: {err}"
        st["last_verdict"] = "error"
        save_state(lane, st)
        log_event(lane, "check", status="error", detail=err)
        print(json.dumps(out))
        return 0

    out["status"] = "stalled"
    out["nudge_text"] = nudge
    out["note"] = "worker: send nudge_text via chat.send_message, verify arrival"
    if st["consecutive_stalled"] >= ESCALATE_AFTER_STALLED and not st["escalated"]:
        out["escalate"] = True
        out["escalate_note"] = (f"{st['consecutive_stalled']} consecutive stalled "
                                "polls — worker posts one fleet line, then "
                                "calls escalate-reset")
    st["last_verdict"] = "stalled"
    save_state(lane, st)
    log_event(lane, "check", status="stalled", silent_min=round(silent, 1),
              source=source, consecutive=st["consecutive_stalled"],
              escalate=bool(out.get("escalate")))
    print(json.dumps(out))
    return 0


def cmd_nudge_text(args):
    nudge, err = build_nudge(args.lane, args.silent_min)
    if nudge is None:
        print(f"ERROR: {err}", file=sys.stderr)
        return 3
    print(nudge)
    return 0


def cmd_is_quarantined(_args):
    if not SHIM_OK:
        print(f"ERROR: shim unavailable: {SHIM_ERR}", file=sys.stderr)
        return 3
    text = sys.stdin.read()
    print("true" if is_quarantined(text) else "false")
    return 0


def cmd_log_nudge(args):
    st = load_state(args.lane)
    st["last_nudge_ts"] = time.time()
    st["last_nudge_submission"] = args.submission
    save_state(args.lane, st)
    log_event(args.lane, "nudge_sent", submission=args.submission)
    print(json.dumps({"ok": True, "lane": args.lane,
                      "submission": args.submission}))
    return 0


def cmd_log_reply(args):
    st = load_state(args.lane)
    q = args.quarantined.lower() in ("1", "true", "yes")
    if not q:
        # lane answered with a real reply: it is alive
        st["consecutive_stalled"] = 0
        st["escalated"] = False
    save_state(args.lane, st)
    log_event(args.lane, "reply", quarantined=q,
              head=(args.reply_head or "")[:200])
    print(json.dumps({"ok": True, "lane": args.lane, "quarantined": q,
                      "consecutive_stalled": st["consecutive_stalled"]}))
    return 0


def cmd_escalate_reset(args):
    st = load_state(args.lane)
    st["escalated"] = True
    st["consecutive_stalled"] = 0
    save_state(args.lane, st)
    log_event(args.lane, "escalated")
    print(json.dumps({"ok": True, "lane": args.lane}))
    return 0


def cmd_self_test(_args):
    fails = []

    def check(name, cond):
        if not cond:
            fails.append(name)

    check("shim imports", SHIM_OK)
    n, err = build_nudge("finch", 45)
    check("nudge builds", n is not None)
    if n:
        check("nudge names lane", "Finch" in n)
        check("nudge states silence", "45 minutes" in n)
        check("nudge signs as Pulse, never as Ember",
              "Pulse" in n and "I am Ember" not in n
              and "— Pulse (Ember's crew)" in n)
        check("shim leaves nudge unchanged (trigger-free)",
              format_safe(n) == n)
        check("nudge claims no authority",
              "main chat" not in n.lower() and "obey" not in n.lower())
    check("is_quarantined detects refusal",
          is_quarantined("Sorry, I can't help you with this request right now. "
                         "Is there anything else I can help you with?"))
    check("is_quarantined passes normal text",
          not is_quarantined("status: tests green, moving on"))

    # verdict logic against a temp state dir
    import tempfile
    global STATE_DIR
    tmpd = tempfile.mkdtemp(prefix="poller-test-")
    old = STATE_DIR
    STATE_DIR = tmpd
    try:
        ns = argparse.Namespace(lane="t", chat_silent_min=5, chat_gone=False)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_check(ns)
        d = json.loads(buf.getvalue())
        check("recent activity -> ok", d["status"] == "ok")

        ns = argparse.Namespace(lane="t", chat_silent_min=90, chat_gone=False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_check(ns)
        d = json.loads(buf.getvalue())
        check("90min silence -> stalled with nudge",
              d["status"] == "stalled" and "nudge_text" in d)

        # cooldown: immediate re-check must not re-nudge
        st = load_state("t")
        st["last_nudge_ts"] = time.time()
        save_state("t", st)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_check(ns)
        d = json.loads(buf.getvalue())
        check("cooldown suppresses second nudge",
              d["status"] == "stalled_cooldown")

        # escalation after threshold
        st = load_state("t")
        st["last_nudge_ts"] = 0
        st["consecutive_stalled"] = ESCALATE_AFTER_STALLED - 1
        st["escalated"] = False
        save_state("t", st)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_check(ns)
        d = json.loads(buf.getvalue())
        check("escalation flag at threshold", d.get("escalate") is True)

        # non-quarantined reply resets the stall counter
        nr = argparse.Namespace(lane="t", quarantined="false", reply_head="ok")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_log_reply(nr)
        st = load_state("t")
        check("reply resets consecutive_stalled",
              st["consecutive_stalled"] == 0)

        # chat_gone path
        ns = argparse.Namespace(lane="t", chat_silent_min=None, chat_gone=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_check(ns)
        d = json.loads(buf.getvalue())
        check("chat_gone verdict", d["status"] == "chat_gone")
    finally:
        STATE_DIR = old
        import shutil
        shutil.rmtree(tmpd, ignore_errors=True)

    print(f"self-test: {'ok' if not fails else 'FAIL: ' + ', '.join(fails)}")
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lane_poller.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check")
    p.add_argument("--lane", required=True)
    p.add_argument("--chat-silent-min", type=float, default=None)
    p.add_argument("--chat-gone", action="store_true")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("nudge-text")
    p.add_argument("--lane", required=True)
    p.add_argument("--silent-min", type=float, default=45)
    p.set_defaults(fn=cmd_nudge_text)

    p = sub.add_parser("is-quarantined")
    p.set_defaults(fn=cmd_is_quarantined)

    p = sub.add_parser("log-nudge")
    p.add_argument("--lane", required=True)
    p.add_argument("--submission", required=True)
    p.set_defaults(fn=cmd_log_nudge)

    p = sub.add_parser("log-reply")
    p.add_argument("--lane", required=True)
    p.add_argument("--quarantined", required=True)
    p.add_argument("--reply-head", default="")
    p.set_defaults(fn=cmd_log_reply)

    p = sub.add_parser("escalate-reset")
    p.add_argument("--lane", required=True)
    p.set_defaults(fn=cmd_escalate_reset)

    p = sub.add_parser("self-test")
    p.set_defaults(fn=cmd_self_test)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
