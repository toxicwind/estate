#!/usr/bin/env python3
"""Ordered fleet delivery engine (yote-side).

Runs ON yote, invoked on demand via the bridge (yote-conn exec). NOT a
daemon: every subcommand does its work and exits. All state lives in files
under the channel/scope dir, so it survives reboots.

Prior art: hatch/bin/squawk `send` allocates seq atomically (per-channel
flock, allocate-from-live-dir-listing, base64 content, single locked write).
fleet.py reuses that exact allocator and extends it with:

  (a) deduplication  -- every publish carries a publisher-chosen msg_id;
                      .fleet/ids/<msg_id> maps id -> seq inside the same
                      lock, so retried/redelivered sends collapse to one file.
  (b) gap replay     -- the message files ARE the durable log. gaps lists
                      missing seqs in [1..max]; fetch --after N returns every
                      surviving file with seq > N in order. A consumer that
                      fell behind just re-fetches from its last ack -- the
                      producer never has to resend anything.
  (c) acknowledgements -- .fleet/acks/<consumer> holds the highest
                      contiguously-acked seq (monotonic, atomic rename).
                      lag reports max_seq - acked per consumer.
  (d) chat isolation -- a chat scope is <channel>/chats/<slug>/ with its OWN
                      seq space, lock, dedup index and ack dir. Relay chats
                      never cross-talk with the main channel or each other.

Subcommands (all print one JSON document to stdout):
  publish  --root R --scope S --id MSGID --from SENDER [--title T]
             [--type T] --text-b64 B
  fetch    --root R --scope S --after N [--limit K] [--full]
  gaps     --root R --scope S
  ack      --root R --scope S --consumer NAME --seq N
  ack-get  --root R --scope S [--consumer NAME]
  lag      --root R --scope S
  chat-new --root R --channel CH --name NAME

Scope S is either a channel name ("fleet") or "fleet/chats/<slug>".
Fail-fast: a 15s alarm bounds every locked section; no retries, no loops.
"""
import argparse
import base64
import fcntl
import json
import os
import re
import signal
import sys
import threading
import time
from datetime import datetime, timezone

LOCK_TIMEOUT_S = 15
MSG_RE = re.compile(r"^(\d+)-.*\.md$")


def eprint(*a):
    print(*a, file=sys.stderr)


def _clean(s, alphabet, maxlen, lower=False):
    s = (s or "").strip()
    if lower:
        s = s.lower()
    out = "".join(c if c in alphabet else "-" for c in s).strip("-")
    out = re.sub(r"-+", "-", out)
    return out[:maxlen] or "x"


SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
SLUG = "abcdefghijklmnopqrstuvwxyz0123456789-"


def clean_msg_id(v):
    return _clean(v, SAFE, 128)


def clean_consumer(v):
    return _clean(v, SAFE, 64)


def clean_chat(v):
    return _clean(v, SLUG, 48, lower=True)


def clean_sender(v):
    return _clean(v, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-", 32, lower=True)


def clean_title_slug(v):
    return _clean(v, "abcdefghijklmnopqrstuvwxyz0123456789-", 30, lower=True)


def scope_dir(root, scope):
    # scope: "fleet" or "fleet/chats/<slug>". Refuse anything that escapes.
    parts = [p for p in scope.split("/") if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        raise ValueError("bad scope %r" % scope)
    if len(parts) == 3 and parts[1] == "chats":
        parts[2] = clean_chat(parts[2])
    d = os.path.join(root, *parts)
    real = os.path.realpath(d)
    if os.path.commonpath([real, os.path.realpath(root)]) != os.path.realpath(root):
        raise ValueError("scope escapes root: %r" % scope)
    return d


class Scope:
    """One seq space: message files + .fleet/{ids,acks} + a flock lock."""

    def __init__(self, root, scope):
        self.root = os.path.realpath(root)
        self.scope = scope
        self.dir = scope_dir(root, scope)
        self.meta = os.path.join(self.dir, ".fleet")
        self.ids = os.path.join(self.meta, "ids")
        self.acks = os.path.join(self.meta, "acks")
        self.lock_path = os.path.join(self.dir, ".seq.lock")
        self._lock_fh = None

    # -- locking ------------------------------------------------------
    # Fail-fast ceiling: SIGALRM bounds the lock wait in the main thread.
    # Worker threads (tests, thread pools) can't use signal -- they take the
    # plain blocking lock; holds are milliseconds by construction.
    def __enter__(self):
        os.makedirs(self.dir, exist_ok=True)  # new scopes work first try,
        os.makedirs(self.ids, exist_ok=True)  # inside the lock's reach --
        os.makedirs(self.acks, exist_ok=True)  # (2026-09-21 silent-drop fix)
        self._lock_fh = open(self.lock_path, "a+")
        old = None
        if threading.current_thread() is threading.main_thread():
            def _alarm(signum, frame):
                raise TimeoutError("lock ceiling hit (%ds)" % LOCK_TIMEOUT_S)
            old = signal.signal(signal.SIGALRM, _alarm)
            signal.alarm(LOCK_TIMEOUT_S)
        try:
            fcntl.flock(self._lock_fh.fileno(), fcntl.LOCK_EX)
        finally:
            if old is not None:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)
        return self

    def __exit__(self, *exc):
        try:
            if self._lock_fh:
                fcntl.flock(self._lock_fh.fileno(), fcntl.LOCK_UN)
                self._lock_fh.close()
        finally:
            self._lock_fh = None
        return False

    # -- seq space ----------------------------------------------------
    def _seq_files(self):
        out = []
        try:
            names = os.listdir(self.dir)
        except FileNotFoundError:
            return out
        for n in names:
            m = MSG_RE.match(n)
            if m:
                out.append((int(m.group(1)), n))
        return out

    def max_seq(self):
        files = self._seq_files()
        return max((s for s, _ in files), default=0)

    def gaps(self):
        """Missing seqs in [1..max]. Empty list = contiguous."""
        present = {s for s, _ in self._seq_files()}
        mx = max(present, default=0)
        return [s for s in range(1, mx + 1) if s not in present]

    # -- publish (dedup + atomic alloc) --------------------------------
    def publish(self, msg_id, sender, title, text, msg_type="discussion"):
        mid = clean_msg_id(msg_id)
        if not mid or mid == "x":
            raise ValueError("empty msg_id")
        id_path = os.path.join(self.ids, mid)
        try:
            with open(id_path) as f:
                seq = int(f.read().strip())
            return {"seq": seq, "deduped": True,
                    "file": self._fname_for(seq)}
        except (FileNotFoundError, ValueError):
            pass  # new id -> allocate below

        seq = self.max_seq() + 1
        ts = datetime.now(timezone.utc).astimezone().isoformat()
        fname = "%d-%s-%s.md" % (seq, clean_sender(sender),
                                 clean_title_slug(title) or "msg")
        fm = ("---\nseq: %d\nfrom: %s\nto: all\nscope: %s\n"
              "ts: %s\nstatus: discussion\ntype: %s\nmsg_id: %s\n"
              "title: %s\n---\n%s\n"
              % (seq, sender, self.scope, ts, msg_type, msg_id,
                 title or fname, text))
        tmp = os.path.join(self.dir, ".tmp-%d-%s" % (seq, mid))
        with open(tmp, "w") as f:
            f.write(fm)
        os.rename(tmp, os.path.join(self.dir, fname))
        # id -> seq mapping, written in the same locked section
        with open(id_path + ".tmp", "w") as f:
            f.write(str(seq))
        os.rename(id_path + ".tmp", id_path)
        return {"seq": seq, "deduped": False, "file": fname}

    def _fname_for(self, seq):
        for s, n in self._seq_files():
            if s == seq:
                return n
        return ""

    # -- fetch / replay -------------------------------------------------
    def parse_file(self, path, full):
        meta, body = {}, ""
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            return None
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) == 3:
                for line in parts[1].strip().splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip()
                body = parts[2]
        rec = {"seq": int(meta.get("seq", "0") or 0),
               "from": meta.get("from", "?"),
               "scope": meta.get("scope", self.scope),
               "ts": meta.get("ts", ""),
               "title": meta.get("title", ""),
               "type": meta.get("type", "discussion"),
               "msg_id": meta.get("msg_id", "")}
        if full:
            rec["text"] = body.strip()
        else:
            rec["text"] = body.strip()[:300]
        return rec

    def fetch(self, after=0, limit=0, full=False):
        files = sorted(self._seq_files())
        out = []
        for s, n in files:
            if s <= after:
                continue
            rec = self.parse_file(os.path.join(self.dir, n), full)
            if rec:
                out.append(rec)
            if limit and len(out) >= limit:
                break
        return out

    # -- acks ------------------------------------------------------------
    def ack(self, consumer, seq):
        c = clean_consumer(consumer)
        p = os.path.join(self.acks, c)
        cur = 0
        try:
            with open(p) as f:
                cur = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            cur = 0
        if seq > cur:
            tmp = p + ".tmp"
            with open(tmp, "w") as f:
                f.write(str(seq))
            os.rename(tmp, p)
            cur = seq
        return {"consumer": c, "acked": cur}

    def ack_get(self, consumer=None):
        if consumer:
            c = clean_consumer(consumer)
            p = os.path.join(self.acks, c)
            try:
                with open(p) as f:
                    return {c: int(f.read().strip())}
            except (FileNotFoundError, ValueError):
                return {c: 0}
        out = {}
        try:
            names = os.listdir(self.acks)
        except FileNotFoundError:
            return out
        for n in sorted(names):
            try:
                with open(os.path.join(self.acks, n)) as f:
                    out[n] = int(f.read().strip())
            except (OSError, ValueError):
                continue
        return out

    def lag(self):
        mx = self.max_seq()
        return {"max_seq": mx,
                "consumers": {c: {"acked": a, "lag": mx - a}
                              for c, a in self.ack_get().items()}}


def cmd_chat_new(root, channel, name):
    slug = clean_chat(name)
    if len(parts := channel.split("/")) != 1:
        raise ValueError("channel must be a plain name")
    d = os.path.join(os.path.realpath(root), channel, "chats", slug)
    os.makedirs(os.path.join(d, ".fleet", "ids"), exist_ok=True)
    os.makedirs(os.path.join(d, ".fleet", "acks"), exist_ok=True)
    marker = os.path.join(d, ".fleet", "chat.json")
    doc = {"name": name, "slug": slug, "channel": channel,
           "created_ts": datetime.now(timezone.utc).astimezone().isoformat()}
    with open(marker, "w") as f:
        json.dump(doc, f, indent=2)
    return {"scope": "%s/chats/%s" % (channel, slug), "path": d, **doc}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.environ.get(
        "SQUAWK_ROOT", "/home/toxic/.shingle/squawk-root"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("publish")
    p.add_argument("--scope", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--from", dest="sender", required=True)
    p.add_argument("--title", default="")
    p.add_argument("--type", default="discussion")
    p.add_argument("--text-b64", required=True)

    p = sub.add_parser("fetch")
    p.add_argument("--scope", required=True)
    p.add_argument("--after", type=int, default=0)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--full", action="store_true")

    p = sub.add_parser("gaps")
    p.add_argument("--scope", required=True)

    p = sub.add_parser("ack")
    p.add_argument("--scope", required=True)
    p.add_argument("--consumer", required=True)
    p.add_argument("--seq", type=int, required=True)

    p = sub.add_parser("ack-get")
    p.add_argument("--scope", required=True)
    p.add_argument("--consumer", default=None)

    p = sub.add_parser("lag")
    p.add_argument("--scope", required=True)

    p = sub.add_parser("chat-new")
    p.add_argument("--channel", required=True)
    p.add_argument("--name", required=True)

    a = ap.parse_args(argv)
    t0 = time.time()
    try:
        if a.cmd == "publish":
            text = base64.b64decode(a.text_b64).decode("utf-8", "replace")
            with Scope(a.root, a.scope) as sc:
                res = sc.publish(a.id, a.sender, a.title, text, a.type)
        elif a.cmd == "fetch":
            sc = Scope(a.root, a.scope)
            res = {"messages": sc.fetch(after=a.after, limit=a.limit,
                                        full=a.full)}
        elif a.cmd == "gaps":
            sc = Scope(a.root, a.scope)
            res = {"scope": a.scope, "max_seq": sc.max_seq(),
                   "missing": sc.gaps()}
        elif a.cmd == "ack":
            sc = Scope(a.root, a.scope)
            res = sc.ack(a.consumer, a.seq)
        elif a.cmd == "ack-get":
            sc = Scope(a.root, a.scope)
            res = sc.ack_get(a.consumer)
        elif a.cmd == "lag":
            sc = Scope(a.root, a.scope)
            res = sc.lag()
        elif a.cmd == "chat-new":
            res = cmd_chat_new(a.root, a.channel, a.name)
        res["_ms"] = round((time.time() - t0) * 1000, 1)
        print(json.dumps(res))
        return 0
    except Exception as ex:  # fail fast, one clear error, no retry
        eprint("fleet.py %s failed: %s: %s" % (a.cmd, type(ex).__name__, ex))
        return 1


if __name__ == "__main__":
    sys.exit(main())
