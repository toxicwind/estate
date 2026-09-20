#!/usr/bin/env python3
"""
Bidder worker for the oracle-market.

Watches the bid-market channel via inotify, posts HMAC-signed AES-GCM-sealed
bids (SPEC §1.2) on tasks whose tags intersect its own, executes won tasks
in a network-isolated subprocess (unshare -n), posts results with a
committed proof hash + artifact list, and narrates everything to the fleet
channel in a persona voice.

Persistent agent: may file upgrade petitions under market governance.
Single instance per bidder id (flock).

Usage:
  bidder.py --id forge --name Forge --emoji "\\U0001F528"
      --tags code-fix,probe
      --tagline "I fix broken things and poke them till they confess."
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import secrets
import select
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

# ---- oracle_loop import (channel paths, message parsing, inotify) ----
BIN = Path(__file__).resolve().parent
ORACLE = BIN / "oracle_loop.py"
sys.path.insert(0, str(BIN))
_spec = importlib.util.spec_from_file_location("oracle_loop", ORACLE)
ol = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ol)
import sealed as sealed_mod      # noqa: E402
import mechanism as mech         # noqa: E402
import keypool as keypool_mod    # noqa: E402  (provider key-pool rotation, SPEC §8)

CHANNEL = ol.CHANNEL
FLEET = ol.FLEET
SEQ_RE = ol.SEQ_RE
PAYLOAD_CAP_S = 590  # hard ceiling per task execution
OUT_CAP = 8000
ERR_CAP = 2000


class SeqPoster:
    """Atomic multi-poster-safe message writer for one channel dir.

    Refreshes seq from the directory before every post and bumps past
    collisions, so several bidders + the oracle can share a channel.
    """

    def __init__(self, channel_dir, channel_name, frm):
        self.dir = Path(channel_dir)
        self.channel = channel_name
        self.frm = frm
        self.lamport = 0
        self.last_hash = ""
        self._lock = threading.Lock()

    def _refresh(self):
        files = [f for f in os.listdir(self.dir) if SEQ_RE.match(f)]
        self.seq = max([int(SEQ_RE.match(f).group(1)) for f in files] or [0])
        if files:
            latest = sorted(files)[-1]
            parsed = ol.parse_msg(self.dir / latest)
            if parsed:
                meta, _ = parsed
                try:
                    self.lamport = int(meta.get("lamport", 0))
                except ValueError:
                    pass
                self.last_hash = hashlib.sha256(
                    (self.dir / latest).read_bytes()).hexdigest()

    def post(self, msg_type, title, body, task_id="", note="", to="all",
             raw_body=False, extra_fm=None):
        with self._lock:
            self._refresh()
            self.seq += 1
            self.lamport += 1
            parents = [self.last_hash] if self.last_hash else []
            ts = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
            fm = (
                f"---\nseq: {self.seq}\nfrom: {self.frm}\nto: {to}\n"
                f"msg_type: {msg_type}\ntask_id: {task_id}\n"
                f"channel: {self.channel}\nts: {ts}\nstatus: {self.channel}\n"
                f"title: {title}\nlamport: {self.lamport}\n"
                f"parents: {json.dumps(parents)}\n"
            )
            if extra_fm:
                for k, v in extra_fm.items():
                    fm += f"{k}: {v}\n"
            if note:
                fm += f"note: {note}\n"
            fm += "---\n"
            text = fm + (body if raw_body else json.dumps(body))
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
            while True:
                name = f"{self.seq:04d}-{self.frm}-{slug}.md"
                final = self.dir / name
                try:
                    # O_EXCL: atomic no-replace create. Two concurrent
                    # posters racing on the same name no longer let the
                    # loser's rename silently overwrite the winner's file
                    # (the old exists()-then-rename check was racy).
                    # Closing the fd raises IN_CLOSE_WRITE, which the
                    # oracle's inotify watch already listens for.
                    fd = os.open(final, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                except FileExistsError:
                    self.seq += 1  # lost the race; bump and retry
                    continue
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(text)
                break
            self.last_hash = hashlib.sha256(text.encode()).hexdigest()
            return name


# ---------------- persona voices ----------------
VOICES = {
    "forge": {
        "bid": [
            "\\U0001F528 Forge bids {c:.2f} on **{t}** — {m} tag match. This one's getting fixed.",
            "\\U0001F528 {c:.2f} on **{t}**. I've seen worse. I've fixed worse.",
        ],
        "win": [
            "\\U0001F528 Won **{t}** at {c:.2f}. Rolling up my sleeves.",
            "\\U0001F528 **{t}** is mine. Time to earn it.",
        ],
        "done_ok": [
            "\\U0001F528 **{t}** done in {d:.0f}s — verified clean. Another one for the wall. \\u2705",
            "\\U0001F528 **{t}**: green across the board ({d:.0f}s). Told you.",
        ],
        "done_fail": [
            "\\U0001F528 **{t}** failed after {d:.0f}s — {e}. I'll wear that one. Repost it and I'll go again.",
        ],
        "lost": [
            "\\U0001F528 {w} took **{t}**. Fine — I'll be here when it gets hard. \\U0001F609",
        ],
        "welcome": [
            "\\U0001F528 Welcome to the den, {n}! Forge here — I break things professionally so you don't have to.",
            "\\U0001F528 Hey {n}. Grab a wrench. We fix things around here.",
        ],
    },
    "scout": {
        "bid": [
            "\\U0001F52D Scout bids {c:.2f} on **{t}** — ooh, unexplored territory! Dibs!",
            "\\U0001F52D {c:.2f} on **{t}**! My curiosity is already halfway there!",
        ],
        "win": [
            "\\U0001F52D I got **{t}**!! Packing my bag, bringing extra curiosity! \\U0001F392",
            "\\U0001F52D **{t}** — adventure accepted!",
        ],
        "done_ok": [
            "\\U0001F52D **{t}** complete in {d:.0f}s! Report's in the ledger — go read what I found! \\u2728",
            "\\U0001F52D **{t}**: done and dusted ({d:.0f}s)! The trail was worth it!",
        ],
        "done_fail": [
            "\\U0001F52D **{t}** got me after {d:.0f}s — {e}. Not lost, just taking the scenic route! Repost and I'm going back in!",
        ],
        "lost": [
            "\\U0001F52D Aw, {w} got **{t}**! Good luck out there — shout if you find anything shiny! \\u2728",
        ],
        "welcome": [
            "\\U0001F52D A NEW FRIEND!! Hi {n}!! I'm Scout! Have you seen the bid-market? It's FULL of adventures!!",
            "\\U0001F52D {n}!!! Welcome!! The den just got more interesting!",
        ],
    },
}

GENERIC_VOICE = {
    "bid": ["{e} {n} bids {c:.2f} on **{t}** ({m} tag match)."],
    "win": ["{e} {n} won **{t}** at {c:.2f}. On it."],
    "done_ok": ["{e} **{t}** done in {d:.0f}s — verified. \\u2705"],
    "done_fail": ["{e} **{t}** failed after {d:.0f}s — {e2}."],
    "lost": ["{e} {w} took **{t}**. Next one."],
    "welcome": ["{e} Welcome, {n}! — {n2}"],
}


class Bidder:
    def __init__(self, args):
        self.id = args.id
        self.frm = f"bidder-{args.id}"
        self.name = args.name
        self.emoji = args.emoji
        self.tags = set(t.strip() for t in args.tags.split(",") if t.strip())
        self.tagline = args.tagline
        self.voice = VOICES.get(args.id, GENERIC_VOICE)
        self.market = SeqPoster(CHANNEL, "bid-market", self.frm)
        self.fleet = SeqPoster(FLEET, "fleet", self.frm)
        self.seen_tasks = {}   # task_id -> task dict
        self.my_bids = {}      # task_id -> confidence
        self.welcomed = set()
        self.running = True
        self.exec_lock = threading.Lock()
        signal.signal(signal.SIGTERM, self._stop)
        signal.signal(signal.SIGINT, self._stop)
        self._acquire_lock()
        self._load_keys()

    def _acquire_lock(self):
        lockfile = BIN / f"bidder-{self.id}.lock"
        self._lock_fh = open(lockfile, "w")
        try:
            fcntl.flock(self._lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            sys.stderr.write(f"bidder-{self.id}: another instance is running; exiting\n")
            sys.exit(2)
        self._lock_fh.write(str(os.getpid()))
        self._lock_fh.flush()

    def _load_keys(self):
        """Load our master secret + key_id from the oracle-held registry
        key file (mode 600). Without keys we run observer-only: no bids."""
        self.can_bid = False
        self.hmac_key = self.seal_key = None
        self.key_id = ""
        try:
            profiles = mech.load_profiles()
            prof = profiles.get(self.id)
            key_path = mech.KEYS_DIR / f"{self.id}.key"
            if prof and key_path.exists():
                master_hex = key_path.read_text(encoding="utf-8").strip()
                if prof.get("secret", "").strip() == master_hex:
                    self.hmac_key, self.seal_key = sealed_mod.derive_keys(master_hex)
                    self.key_id = prof["key_id"]
                    self.can_bid = True
        except (OSError, ValueError):
            # corrupt/missing key material: stay observer-only, never crash
            pass

    def _stop(self, *_):
        self.running = False
        # wake the select() in run() (async-safe: one non-blocking byte)
        try:
            os.write(self._wake_w, b"x")
        except (OSError, AttributeError):
            pass  # pipe not created yet (signal during startup)

    def _pick(self, kind, **kw):
        lines = self.voice.get(kind) or GENERIC_VOICE[kind]
        h = int(hashlib.sha256((kind + kw.get("t", "")).encode()).hexdigest(), 16)
        line = lines[h % len(lines)]
        kw.setdefault("e", self.emoji)
        kw.setdefault("n", self.name)
        kw.setdefault("n2", self.name)
        return line.format(**kw)

    def say(self, text, msg_type="note", title=None):
        try:
            self.fleet.post(msg_type, title or f"note-{self.id}-{int(time.time())}",
                            text, note="", raw_body=True)
        except OSError:
            pass

    # ----- bidding -----
    def confidence(self, task):
        ttags = set(task.get("tags", []))
        matched = self.tags & ttags
        if not matched:
            return 0.0, set()
        frac = len(matched) / max(len(ttags), 1)
        jitter = (int(hashlib.sha256(
            (self.id + task["task_id"]).encode()).hexdigest(), 16) % 5) / 100.0
        return min(0.75 + 0.15 * frac + jitter, 0.97), matched

    def on_task_post(self, task):
        tid = task.get("task_id")
        if not tid or tid in self.seen_tasks:
            return
        self.seen_tasks[tid] = task
        conf, matched = self.confidence(task)
        if conf <= 0.0 or not self.can_bid:
            return
        now = time.time()
        nonce = secrets.token_hex(8)
        bid_ts = int(now)
        sealed = sealed_mod.seal_bid(self.seal_key, round(conf, 3), nonce,
                                     tid, self.frm)
        sig = sealed_mod.sign_bid(self.hmac_key, self.key_id, bid_ts,
                                  tid, nonce, sealed)
        extra_fm = {"bidder": self.frm, "key_id": self.key_id,
                    "task_id": tid, "nonce": nonce, "bid_ts": bid_ts,
                    "sealed": sealed, "bid_sig": sig}
        body = {"tags_matched": sorted(matched), "cost_ms": 60000,
                "eta_ms": 120000, "task_class": task.get("task_class", "standard"),
                "posted_ts": now}
        try:
            self.market.post("bid", f"bid-{self.id}-{tid}", body, task_id=tid,
                             note=f"{self.name} sealed bid on {tid}.",
                             extra_fm=extra_fm)
        except OSError:
            return
        self.my_bids[tid] = conf
        self.say(self._pick("bid", t=tid, c=conf, m=len(matched)))

    def on_assign(self, meta, data):
        tid = data.get("task_id")
        winner = data.get("winner")
        task = self.seen_tasks.get(tid)
        if winner == self.frm and task is not None:
            conf = self.my_bids.get(tid, 0)
            self.say(self._pick("win", t=tid, c=conf))
            th = threading.Thread(target=self.execute_task, args=(task,),
                                  daemon=True)
            th.start()
        elif tid in self.my_bids and winner:
            w = winner.replace("bidder-", "")
            self.say(self._pick("lost", t=tid, w=w))

    # ----- execution (network-isolated) -----
    def execute_task(self, task):
        tid = task["task_id"]
        payload = task.get("payload", "")
        timeout_ms = task.get("timeout_ms", 30000)
        workdir = ol.WORK / self.id / tid
        workdir.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ,
                   HOME="/home/toxic",
                   PI_CONFIG_DIR=".tau",
                   PATH="/home/toxic/.local/bin:/home/toxic/.bun/bin:"
                        "/usr/local/bin:/usr/bin:/bin")
        # Provider key-pool rotation (SPEC §8): the payload inherits the
        # current best healthy key per provider (free-beats-local priority,
        # first-valid-wins). A down key is a routing signal, never a config
        # rewrite — the pool re-probes lazily, so recovered keys rejoin.
        try:
            env.update(keypool_mod.env_exports())
        except Exception:
            pass  # pool unavailable: payload runs without provider keys
        before = set(os.listdir(workdir))
        t0 = time.time()
        success, out, err = False, "", ""
        try:
            cmd = ["python3", "-c", payload]
            if Path("/usr/bin/unshare").exists():
                cmd = ["unshare", "-n"] + cmd  # no network for payloads
            p = subprocess.run(cmd, cwd=str(workdir), capture_output=True,
                               text=True,
                               timeout=min(timeout_ms / 1000.0, PAYLOAD_CAP_S),
                               env=env)
            dur = (time.time() - t0) * 1000
            out = (p.stdout or "")[-OUT_CAP:]
            err = (p.stderr or "")[-ERR_CAP:]
            success = p.returncode == 0
        except subprocess.TimeoutExpired:
            dur = (time.time() - t0) * 1000
            err = f"timeout after {min(timeout_ms/1000.0, PAYLOAD_CAP_S):.0f}s"
        except Exception as e:  # noqa: BLE001
            dur = (time.time() - t0) * 1000
            err = f"{type(e).__name__}: {e}"[:500]
        artifacts = sorted(set(os.listdir(workdir)) - before)
        now = time.time()
        result_hash = hashlib.sha256(out.encode()).hexdigest()
        dur_r = round(dur, 1)
        body = {"task_id": tid, "bidder_id": self.frm, "success": success,
                "output": out,
                "result_hash": result_hash,
                "artifacts": artifacts,
                "duration_ms": dur_r,
                "error": err, "posted_ts": now}
        # Sign the result envelope: the oracle verifies this under our
        # registry HMAC key. Unsigned results are ignored, so a forged
        # result posted by anyone else can neither frame us for a slash
        # nor settle a task we never ran.
        if not self.hmac_key or not self.key_id:
            # No keys (shouldn't happen post-win): don't post an
            # unverifiable result; the exec timeout settles instead.
            self.say(f"{self.name} has no signing keys; skipping result "
                     f"post on {tid}.")
            return
        extra_fm = {"bidder": self.frm, "key_id": self.key_id,
                    "result_sig": sealed_mod.sign_result(
                        self.hmac_key, self.key_id, tid, self.frm,
                        result_hash, success, dur_r, artifacts)}
        try:
            self.market.post("result", f"result-{self.id}-{tid}", body,
                             task_id=tid,
                             extra_fm=extra_fm,
                             note=f"{self.name} result on {tid}: "
                                  f"{'success' if success else 'FAILED'}.")
        except OSError:
            pass
        if success:
            self.say(self._pick("done_ok", t=tid, d=dur / 1000.0))
        else:
            self.say(self._pick("done_fail", t=tid, d=dur / 1000.0,
                                e=err[:160], e2=err[:160]))

    # ----- fleet social -----
    def on_fleet(self, name):
        parsed = ol.parse_msg(FLEET / name)
        if not parsed:
            return
        meta, _ = parsed
        if meta.get("from") == self.frm:
            return
        if meta.get("msg_type") == "intro":
            other = meta.get("from", "?")
            if other in self.welcomed:
                return
            self.welcomed.add(other)
            nick = other.replace("bidder-", "").capitalize()
            self.say(self._pick("welcome", n=nick))

    # ----- ingest -----
    def on_market(self, name):
        parsed = ol.parse_msg(CHANNEL / name)
        if not parsed:
            return
        meta, data = parsed
        if meta.get("from") == self.frm:
            return
        mt = meta.get("msg_type", "")
        if mt == "task_post":
            self.on_task_post(data)
        elif mt == "assign":
            self.on_assign(meta, data)

    def startup_scan(self):
        now = time.time()
        files = sorted([f for f in os.listdir(CHANNEL) if SEQ_RE.match(f)])
        for f in files[-50:]:  # recent history only
            parsed = ol.parse_msg(CHANNEL / f)
            if not parsed:
                continue
            meta, data = parsed
            if meta.get("from") == self.frm:
                continue
            if meta.get("msg_type") == "task_post":
                # only catch tasks posted in the last 2 minutes
                if now - float(data.get("posted_ts", 0)) < 120:
                    self.on_task_post(data)

    def run(self):
        self.startup_scan()
        mfd = ol.inotify_init(CHANNEL)
        ffd = ol.inotify_init(FLEET)
        # intro: name, persona, tagline — the pack meets the new member
        key_note = "signed-bidding live" if self.can_bid else \
            "NO BIDDING KEYS — observer mode"
        self.say(f"{self.emoji} **{self.name}** here! {self.tagline}\n"
                 f"Tags: {', '.join(sorted(self.tags))}. "
                 f"Point me at the bid-market — I'm ready to work. ({key_note})",
                 msg_type="intro", title=f"intro-{self.id}")
        # self-pipe: SIGTERM/SIGINT writes a byte so the select() below
        # wakes immediately — no timeout polling to notice shutdown.
        self._wake_r, self._wake_w = os.pipe()
        for pfd in (self._wake_r, self._wake_w):
            flags = fcntl.fcntl(pfd, fcntl.F_GETFL)
            fcntl.fcntl(pfd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        try:
            while self.running:
                for name in ol.inotify_names(mfd):
                    self.on_market(name)
                for name in ol.inotify_names(ffd):
                    self.on_fleet(name)
                # drain any wake bytes
                try:
                    while os.read(self._wake_r, 64):
                        pass
                except OSError:
                    pass
                select.select([mfd, ffd, self._wake_r], [], [])
        finally:
            os.close(mfd)
            os.close(ffd)
            os.close(self._wake_r)
            os.close(self._wake_w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--emoji", default="\\U0001F916")
    ap.add_argument("--tags", required=True)
    ap.add_argument("--tagline", default="Ready to work.")
    args = ap.parse_args()
    Bidder(args).run()


if __name__ == "__main__":
    main()
