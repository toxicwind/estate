#!/usr/bin/env python3
"""Fleet presence + rollover watchdog v2 (lane 7, owner).

Runs ON awrawr-pc (sovereign-chat is local: no bridge hop).
Cell-side driver (driver.sh) syncs the rollover mirror, then execs this.

Each sweep:
  1. Heartbeat lane-7 on the plane (so we never flag ourselves stale).
  2. GET /v1/presence -> live roster with server timestamps (last_heartbeat, ts).
  3. Attribute presence to lanes via lane_manifest.json (canonical, durable).
     The mirror is checked AGAINST the manifest: a lane whose block
     disappears from the mirror is reported, never silently dropped.
  4. Diff against state.json v2 (per-lane last_seen, transitions, last_sweep).
  5. Post ONE consolidated fleet-room message ONLY on transitions:
       live->stale (degradation, with last-seen age),
       stale->live (recovery, with downtime),
       block lost/gained,
       watchdog gap (no sweep for > 2x interval).
     Steady state = silence. Heartbeat still posts every sweep (plane TTL).

Cadence: 60s (sovereign-chat presence TTL is 120s; a 60s sweep keeps the
lane-7 heartbeat alive and still pages a gap only after 2 missed sweeps).

Manifest: lane_manifest.json is the durable identity manifest. Regenerate
with `sweep.py --gen-manifest` after a verified rollover update, then commit
it. If the manifest is missing, the sweep falls back to parsing the mirror
(map_error warns) — that mode is blind to whole-block loss.

State: ./state.json (schema v2). First run posts the baseline.
Exit 0 always on a completed sweep; JSON result on stdout for the driver log.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(HERE, "state.json")
ROLLOVER = os.path.join(HERE, "fleet-rollover.md")
MANIFEST_PATH = os.path.join(HERE, "lane_manifest.json")
TOKEN_PATH = "/home/toxic/.config/sovereign-chat-token"
CHAT = "http://127.0.0.1:25120"
MY_AGENT = "5a4f76c0-e3a4-4069-ba6f-3113917102dc"
MY_NAME = "lane-7"
INTERVAL_S = 60           # driver cadence; sovereign-chat presence TTL is 120s
GAP_S = 2 * INTERVAL_S     # gap page at > 2x interval (two missed sweeps)
MAP_ERROR_REPAGE_S = 3600  # re-page a blind-map condition at most hourly
TRANSITION_CAP = 50
STATE_VERSION = 2


def parse_ts(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso_now(dt=None):
    return (dt or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")


def human_dur(seconds):
    seconds = int(max(0, seconds))
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m {s}s" if s else f"{m}m"
    h, m = divmod(m, 60)
    if h < 24:
        return f"{h}h {m}m" if m else f"{h}h"
    d, h = divmod(h, 24)
    return f"{d}d {h}h" if h else f"{d}d"


def chat_api(method, path, data=None):
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    cmd = ["curl", "-s", "-m", "10", "-H", f"Authorization: Bearer {token}"]
    if method != "GET":
        cmd += ["-X", method]
    if data is not None:
        cmd += ["-H", "Content-Type: application/json",
                "-d", json.dumps(data)]
    cmd.append(CHAT + path)
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return json.loads(out.stdout)


def heartbeat(activity):
    return chat_api("POST", "/v1/presence",
                    {"agent_id": MY_AGENT, "activity": activity})


def post_fleet(body):
    return chat_api("POST", "/v1/rooms/fleet/messages",
                    {"from_agent": MY_AGENT, "kind": "chat", "body": body})


def parse_mirror_map(text):
    """chat_id prefix -> lane, parsed from rollover mirror text."""
    mapping = {}
    for m in re.finditer(r"^### Lane (\d+)\s*$", text, re.M):
        section = text[m.end():m.end() + 1200]
        cm = re.search(r"chat_id:\s*([0-9a-f-]{36})", section)
        if cm:
            mapping[cm.group(1)[:8]] = int(m.group(1))
    return mapping


def load_manifest():
    """Canonical lane identity manifest. Returns (prefix->lane, error)."""
    try:
        with open(MANIFEST_PATH) as f:
            doc = json.load(f)
        lanes = {}
        for prefix, info in doc.get("lanes", {}).items():
            lanes[prefix] = int(info["lane"])
        if not lanes:
            return None, "manifest has no lanes"
        return lanes, None
    except (OSError, json.JSONDecodeError, KeyError, TypeError,
            ValueError) as e:
        return None, str(e)[:120]


def build_expected_map():
    """Canonical expected lane map.

    Manifest first: the mirror is checked AGAINST it, so a lane whose whole
    block vanishes from the mirror is detected instead of silently dropped.
    Mirror fallback only when the manifest is unreadable (warns; blind to
    whole-block loss).
    Returns (prefix->lane dict, error-or-None).
    """
    man, man_err = load_manifest()
    if man:
        return man, None
    try:
        with open(ROLLOVER) as f:
            text = f.read()
    except OSError as e:
        return {}, (f"manifest unreadable ({man_err or 'missing'}) and "
                    f"mirror unreadable: {e}")
    m = parse_mirror_map(text)
    if not m:
        return {}, ("manifest missing and no lane blocks parsed from mirror")
    return m, "manifest missing: map derived from mirror (blind to block loss)"


def gen_manifest():
    """(Re)build lane_manifest.json from the current mirror. Run after a
    verified rollover update, then commit the manifest."""
    with open(ROLLOVER) as f:
        text = f.read()
    lanes = {}
    for m in re.finditer(r"^### Lane (\d+)\s*$", text, re.M):
        section = text[m.end():m.end() + 1200]
        cm = re.search(r"chat_id:\s*([0-9a-f-]{36})", section)
        if cm:
            lanes[cm.group(1)[:8]] = {"lane": int(m.group(1)),
                                      "chat_id": cm.group(1)}
    if not lanes:
        raise SystemExit("gen-manifest: no lane blocks parsed from mirror")
    doc = {"generated_ts": iso_now(),
           "generated_from": os.path.basename(ROLLOVER),
           "lanes": lanes}
    tmp = MANIFEST_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(doc, f, indent=1)
    os.replace(tmp, MANIFEST_PATH)
    return lanes


def check_blocks(prefix_map, text):
    """Which expected lanes lack a valid identity block in the mirror.

    A block is valid only if BOTH its "### Lane N" header and its chat_id
    prefix are present: a bare mention of "lane-5" in another lane's text
    does not count as holding a block.
    Returns [lane numbers]."""
    missing = []
    for prefix, n in prefix_map.items():
        header = re.search(rf"^### Lane {n}\s*$", text, re.M)
        if not (header and prefix in text):
            missing.append(n)
    return sorted(missing)


def load_state():
    try:
        with open(STATE_PATH) as f:
            st = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if st.get("version") == 1 or ("version" not in st and "status" in st):
        # v1 -> v2: v1 state has no version key; detect by the "status" key.
        # Carry booleans, last_seen unknown (pre-v2).
        # Seed last_sweep_ts from the state file mtime: the last v1 sweep
        # wrote it, so the gap detector stays honest across the migration.
        try:
            last_sweep = iso_now(datetime.fromtimestamp(
                os.path.getmtime(STATE_PATH), tz=timezone.utc))
        except OSError:
            last_sweep = None
        lanes = {}
        for n, s in st.get("status", {}).items():
            lanes[n] = {"block": bool(s.get("block")),
                        "live": bool(s.get("live")),
                        "last_seen_ts": None,
                        "last_transition": None,
                        "last_transition_ts": None}
        return {"version": 2, "last_sweep_ts": last_sweep, "lanes": lanes,
                "transitions": [], "migrated_from_v1": True}
    if st.get("version") == 2:
        return st
    return None


def save_state(st):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, STATE_PATH)


def decide(old, obs):
    """Pure paging brain. Returns (new_lanes, pages, transitions).

    old: v2 state dict or None. obs: {"server_ts": datetime,
        "lanes": {n: {"live": bool, "last_heartbeat": datetime|None}},
        "missing_blocks": [n] | None}
    """
    now = obs["server_ts"]
    new_lanes = {}
    pages = []
    transitions = []

    for n in sorted(obs["lanes"]):
        o = obs["lanes"][n]
        prev = (old or {}).get("lanes", {}).get(str(n), {})
        was_live = bool(prev.get("live"))
        was_block = prev.get("block", True)
        is_live = o["live"]
        is_block = (obs["missing_blocks"] is not None
                    and n not in obs["missing_blocks"])

        last_seen = parse_ts(o["last_heartbeat"]) if o["last_heartbeat"] else None
        if is_live and last_seen:
            last_seen_ts = iso_now(last_seen)
        else:
            last_seen_ts = prev.get("last_seen_ts")

        entry = {"block": is_block, "live": is_live,
                 "last_seen_ts": last_seen_ts,
                 "last_transition": prev.get("last_transition"),
                 "last_transition_ts": prev.get("last_transition_ts")}

        if old is not None:
            if was_live and not is_live:
                age = ""
                if prev.get("last_seen_ts"):
                    age = (" (last heartbeat "
                           + human_dur((now - parse_ts(prev["last_seen_ts"]))
                                       .total_seconds()) + " ago)")
                pages.append(f"lane-{n} STALE{age}")
                entry["last_transition"] = "live->stale"
                entry["last_transition_ts"] = iso_now(now)
                transitions.append({"ts": iso_now(now), "lane": n,
                                    "from": "live", "to": "stale"})
            elif not was_live and is_live:
                down = ""
                if prev.get("last_seen_ts"):
                    down = (" after "
                            + human_dur((now - parse_ts(prev["last_seen_ts"]))
                                        .total_seconds()) + " dark")
                elif prev:
                    down = " (first sighting this watchdog generation)"
                pages.append(f"lane-{n} LIVE again{down}")
                entry["last_transition"] = "stale->live"
                entry["last_transition_ts"] = iso_now(now)
                transitions.append({"ts": iso_now(now), "lane": n,
                                    "from": "stale", "to": "live"})
            if was_block and not is_block:
                pages.append(f"lane-{n} rollover block MISSING in mirror")
                transitions.append({"ts": iso_now(now), "lane": n,
                                    "from": "block", "to": "no-block"})
            elif not was_block and is_block and old is not None and prev:
                pages.append(f"lane-{n} rollover block restored")
                transitions.append({"ts": iso_now(now), "lane": n,
                                    "from": "no-block", "to": "block"})
        new_lanes[str(n)] = entry

    if old is not None and old.get("last_sweep_ts"):
        gap = (now - parse_ts(old["last_sweep_ts"])).total_seconds()
        if gap > GAP_S:
            pages.append(f"watchdog gap: no sweep for {human_dur(gap)} "
                         f"(interval {human_dur(INTERVAL_S)}) — resumed")

    return new_lanes, pages, transitions


def main():
    result = {"ok": False}
    try:
        hb = heartbeat(f"{MY_NAME}: fleet-watchdog sweep")
        hb_ok = bool(hb.get("ok"))
    except Exception as e:
        hb_ok = False
        result["heartbeat_error"] = str(e)[:200]

    try:
        pres = chat_api("GET", "/v1/presence")
        server_ts = parse_ts(pres.get("ts")) or datetime.now(timezone.utc)
    except Exception as e:
        print(json.dumps({**result, "error": f"presence read failed: {e}"[:200]}))
        return 1

    prefix_map, map_err = build_expected_map()
    try:
        with open(ROLLOVER) as f:
            mirror_text = f.read()
    except OSError:
        mirror_text = ""

    old = load_state()
    first_run = old is None

    if not prefix_map:
        # Blind: no lane map at all. Never fabricate transitions; keep the
        # sweep honest (gap clock keeps ticking), re-page at most hourly.
        last_page = (old or {}).get("last_map_error_page_ts")
        due = (not last_page or
               (server_ts - parse_ts(last_page)).total_seconds()
               > MAP_ERROR_REPAGE_S)
        posted = False
        post_error = None
        pages = []
        if due:
            pages = [f"watchdog BLIND: {map_err}. No transitions evaluated."]
            body = f"{MY_NAME} watchdog: " + "; ".join(pages) + "."
            try:
                post_fleet(body)
                posted = True
            except Exception as e:
                post_error = str(e)[:200]
        new_state = {"version": STATE_VERSION,
                     "last_sweep_ts": iso_now(server_ts),
                     "lanes": (old or {}).get("lanes", {}),
                     "transitions": (old or {}).get("transitions", []),
                     "map_error": map_err,
                     "last_map_error_page_ts": (iso_now(server_ts)
                                                if posted else last_page)}
        save_state(new_state)
        result.update({"ok": True, "blind": True, "hb_ok": hb_ok,
                       "map_error": map_err, "pages": pages,
                       "posted": posted, "post_error": post_error})
        print(json.dumps(result))
        return 0

    missing = check_blocks(prefix_map, mirror_text) if mirror_text else None

    live_by_lane = {}
    for a in pres.get("live", []):
        cid = (a.get("chat_id") or "")[:8]
        if cid in prefix_map:
            live_by_lane[prefix_map[cid]] = a.get("last_heartbeat")

    lane_nos = sorted(set(prefix_map.values()))
    obs = {"server_ts": server_ts,
           "lanes": {n: {"live": n in live_by_lane,
                         "last_heartbeat": live_by_lane.get(n)}
                     for n in lane_nos},
           "missing_blocks": missing}

    new_lanes, pages, transitions = decide(old, obs)

    if first_run:
        stale = [n for n in lane_nos if not obs["lanes"][n]["live"]]
        if not missing and not stale:
            pages = ["baseline: all lanes hold blocks and are live. Clean."]
        else:
            parts = []
            if missing:
                parts.append(f"missing blocks: lanes {missing}")
            if stale:
                parts.append(f"stale lanes: {stale}")
            pages = ["baseline: " + "; ".join(parts)]

    new_state = {"version": STATE_VERSION,
                 "last_sweep_ts": iso_now(server_ts),
                 "lanes": new_lanes,
                 "transitions": ((old or {}).get("transitions", [])
                                 + transitions)[-TRANSITION_CAP:]}
    save_state(new_state)

    posted = False
    post_error = None
    if pages:
        body = f"{MY_NAME} watchdog: " + "; ".join(pages) + "."
        try:
            post_fleet(body)
            posted = True
        except Exception as e:
            post_error = str(e)[:200]

    result.update({"ok": True, "first_run": first_run, "hb_ok": hb_ok,
                   "live": sorted(live_by_lane),
                   "stale": [n for n in lane_nos if n not in live_by_lane],
                   "missing_blocks": missing, "map_error": map_err,
                   "map_source": "manifest" if not map_err else "mirror-fallback",
                   "pages": pages, "posted": posted,
                   "post_error": post_error,
                   "transitions": len(new_state["transitions"])})
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gen-manifest":
        lanes = gen_manifest()
        print(json.dumps({"manifest": MANIFEST_PATH,
                          "lanes": sorted(v["lane"] for v in lanes.values())}))
    else:
        sys.exit(main())
