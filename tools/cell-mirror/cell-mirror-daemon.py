#!/usr/bin/env python3
"""cell-mirror live daemon: Dropbox-style one-way sync, cell -> yote.

Event-driven via inotify (directory watches only; the container caps watches
at 63,750 and the tree has 155k files). Directory watches catch create /
delete / rename / new-subdir. In-place content modifications (IN_MODIFY on an
existing file) do NOT raise dir events; those are caught by the supervisor's
periodic `find -newer` repair sweep (documented safety net, same as Dropbox's
periodic scan). This daemon itself never polls.

Batching: events accumulate for BATCH_SEC, then coalesce per-path and sync.
Deletes propagate. Moves are paired by inotify cookie and replayed as `mv`.

Excludes mirror the seed: venvs/, .git/, __pycache__/, .tmpdir/, tmp*/,
node_modules/, *.log, *.tmp, plus logs/ (avoids mirroring our own log),
plus a hard denylist that is NEVER mirrored: private key material
(*/.ssh/id_*, *.pem, *.key).

Also mirrors ~/.bashrc (watched via a non-recursive watch on /home/hatch).

Logs to ~/workspace/logs/cell-mirror.log. PID file ~/workspace/.tmpdir/cell-mirror.pid.
"""
import base64, fnmatch, json, os, queue, sys, threading, time, urllib.request

CONN = "http://127.0.0.1:18301/exec"
SRC_ROOT = os.path.expanduser("~/workspace")
YOTE_ROOT = "/home/toxic/estate/cell-mirror"
YOTE_INC = YOTE_ROOT + "/.incoming"
BATCH_SEC = 10
CHUNK_B64 = 16 * 1024  # keep the ws-lane payload (~17KB JSON) well under
                       # the awrawr-ws-exec frame limit (~32-48KB, 2026-10-03)
LOG = os.path.join(SRC_ROOT, "logs", "cell-mirror.log")
PIDFILE = os.path.join(SRC_ROOT, ".tmpdir", "cell-mirror.pid")
LASTSYNC = os.path.join(SRC_ROOT, ".tmpdir", "cell-mirror-last-sync")

EXCLUDE_DIRS = {"venvs", ".git", "__pycache__", ".tmpdir", "node_modules", "logs"}
EXCLUDE_GLOBS = ("tmp*", "*.log", "*.tmp")
DENY_GLOBS = ("*.pem", "*.key")
DENY_DIRS = {".ssh"}  # never mirror private key dirs' id_* files (checked below)

from inotify_simple import INotify, flags

WATCH_MASK = (flags.CREATE | flags.DELETE | flags.MOVED_FROM | flags.MOVED_TO |
              flags.DELETE_SELF | flags.MOVE_SELF)

log_lock = threading.Lock()

def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    with log_lock:
        print(line, flush=True)
        try:
            with open(LOG, "a") as f:
                f.write(line + "\n")
        except OSError:
            pass

def yote_exec(cmd, timeout=90):
    req = urllib.request.Request(
        CONN, data=json.dumps({"cmd": cmd, "timeout": timeout}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout + 30) as r:
        return json.loads(r.read())

def yote(cmd, timeout=120):
    d = yote_exec(cmd, timeout)
    if d.get("code") != 0:
        raise RuntimeError(f"yote rc={d.get('code')}: {d.get('stdout','')[:200]} {d.get('stderr','')[:200]}")
    return d.get("stdout", "")

def excluded_rel(rel):
    """True if a workspace-relative path should never be mirrored."""
    if rel in (".bashrc",):
        return False
    parts = rel.split("/")
    for p in parts:
        if p in EXCLUDE_DIRS:
            return True
        for g in EXCLUDE_GLOBS:
            if fnmatch.fnmatch(p, g):
                return True
    for g in DENY_GLOBS:
        if fnmatch.fnmatch(parts[-1], g):
            return True
    if ".ssh" in parts and parts[-1].startswith("id_"):
        return True
    return False

def safe_rel(path):
    """Workspace-relative path, or None if it escapes / is excluded."""
    if path == os.path.expanduser("~/.bashrc"):
        return ".bashrc"
    try:
        rel = os.path.relpath(path, SRC_ROOT)
    except ValueError:
        return None
    if rel.startswith("..") or os.path.isabs(rel):
        return None
    if excluded_rel(rel):
        return None
    return rel

class Mirror:
    def __init__(self):
        self.ino = INotify()
        self.wd_to_path = {}
        self.pending = {}   # rel -> action ('sync' | 'delete')
        self.moves = {}     # cookie -> (src_rel)
        self.lock = threading.Lock()

    def add_watch_recursive(self, path):
        for root, dirs, _files in os.walk(path):
            # prune excluded dirs in-place
            dirs[:] = [d for d in dirs
                       if d not in EXCLUDE_DIRS
                       and not any(fnmatch.fnmatch(d, g) for g in EXCLUDE_GLOBS)]
            rel = safe_rel(root)
            if rel is None and root != SRC_ROOT:
                dirs[:] = []
                continue
            try:
                wd = self.ino.add_watch(root, WATCH_MASK)
                self.wd_to_path[wd] = root
            except OSError as e:
                log(f"watch failed {root}: {e}")

    def run(self):
        log(f"adding watches under {SRC_ROOT} ...")
        self.add_watch_recursive(SRC_ROOT)
        # non-recursive watch on $HOME for .bashrc only
        try:
            wd = self.ino.add_watch(os.path.expanduser("~"), WATCH_MASK)
            self.wd_to_path[wd] = os.path.expanduser("~") + "|top"
        except OSError as e:
            log(f"home watch failed: {e}")
        log(f"watching {len(self.wd_to_path)} dirs; batch={BATCH_SEC}s")
        # Bridge may be down at startup (post-restart, outage). Do not let a
        # dead bridge kill the daemon — log it, stay alive, keep batching ops
        # so the flush loop and later repair sweeps catch up on recovery.
        try:
            yote(f"mkdir -p {YOTE_INC}")
        except Exception as e:
            log(f"bridge unreachable at startup ({e}); daemon staying alive, will retry in loop")
        self.initial_catchup()
        last_flush = time.time()
        while True:
            for ev in self.ino.read(timeout=1000):
                self.handle(ev)
            if time.time() - last_flush >= BATCH_SEC:
                self.flush()
                last_flush = time.time()

    def initial_catchup(self):
        """Upload anything changed since the seed tar started (or last sync)."""
        try:
            with open(LASTSYNC) as f:
                since = f.read().strip()
        except OSError:
            since = None
        if not since:
            log("no last-sync marker; skipping catch-up sweep (seed assumed current)")
            return
        log(f"catch-up sweep: files newer than {since}")
        count = 0
        failed_oldest = None
        for root, dirs, files in os.walk(SRC_ROOT):
            dirs[:] = [d for d in dirs
                       if d not in EXCLUDE_DIRS
                       and not any(fnmatch.fnmatch(d, g) for g in EXCLUDE_GLOBS)]
            for fn in files:
                p = os.path.join(root, fn)
                rel = safe_rel(p)
                if rel is None:
                    continue
                try:
                    mt = os.path.getmtime(p)
                    if mt > float(since):
                        try:
                            self.sync_file(p, rel)
                        except Exception as e:
                            # one bad file must never abort the sweep or kill
                            # the daemon (matches flush()'s per-op tolerance)
                            log(f"catch-up sync failed {rel}: {str(e)[:160]}")
                            # keep the watermark at/behind the failed file so
                            # the next sweep retries it instead of skipping it
                            failed_oldest = mt if failed_oldest is None \
                                else min(failed_oldest, mt)
                            continue
                        count += 1
                except OSError:
                    pass
        # .bashrc
        b = os.path.expanduser("~/.bashrc")
        try:
            if os.path.getmtime(b) > float(since):
                try:
                    self.sync_file(b, ".bashrc")
                except Exception as e:
                    log(f"catch-up sync failed .bashrc: {str(e)[:160]}")
                    failed_oldest = os.path.getmtime(b) \
                        if failed_oldest is None \
                        else min(failed_oldest, os.path.getmtime(b))
                else:
                    count += 1
        except OSError:
            pass
        self.write_lastsync(failed_oldest)
        log(f"catch-up sweep done: {count} files synced")

    def write_lastsync(self, ts=None):
        # ts pins the watermark: on a catch-up sweep with failures it is the
        # oldest failed file's mtime, so failed files get retried next sweep.
        try:
            with open(LASTSYNC, "w") as f:
                f.write(str(time.time() if ts is None else ts))
        except OSError:
            pass

    def handle(self, ev):
        wd_path = self.wd_to_path.get(ev.wd)
        if wd_path is None:
            return
        if wd_path.endswith("|top"):
            # home dir, non-recursive: only .bashrc matters
            if ev.name != ".bashrc":
                return
            full = os.path.join(os.path.expanduser("~"), ev.name)
            base = wd_path[:-4]
        else:
            full = os.path.join(wd_path, ev.name)
            base = wd_path
        mask = ev.mask
        if mask & flags.ISDIR:
            if mask & (flags.CREATE | flags.MOVED_TO):
                # new dir: watch it, mirror it, and sync any files already
                # inside it (mv/git-clone/tar can populate before we watch)
                self.add_watch_recursive(full)
                rel = safe_rel(full)
                if rel:
                    with self.lock:
                        self.pending[rel] = "mkdir"
                        for r2, _d, fs in os.walk(full):
                            for fn in fs:
                                p2 = os.path.join(r2, fn)
                                rel2 = safe_rel(p2)
                                if rel2:
                                    self.pending[rel2] = "sync"
            elif mask & (flags.DELETE | flags.MOVED_FROM | flags.DELETE_SELF | flags.MOVE_SELF):
                rel = safe_rel(full)
                if rel:
                    with self.lock:
                        self.pending[rel] = "delete"
                # drop watches under it
                for wd, p in list(self.wd_to_path.items()):
                    if p == full or p.startswith(full + "/"):
                        try:
                            self.ino.rm_watch(wd)
                        except OSError:
                            pass
                        self.wd_to_path.pop(wd, None)
            return
        # file event
        if mask & flags.MOVED_FROM:
            rel = safe_rel(full)
            if rel:
                self.moves[ev.cookie] = rel
        elif mask & flags.MOVED_TO:
            rel = safe_rel(full)
            src = self.moves.pop(ev.cookie, None)
            if src and rel:
                with self.lock:
                    self.pending[f"{src}\x00{rel}"] = "move"
            elif rel:
                with self.lock:
                    self.pending[rel] = "sync"
        elif mask & flags.CREATE:
            rel = safe_rel(full)
            if rel:
                with self.lock:
                    self.pending[rel] = "sync"
        elif mask & flags.DELETE:
            rel = safe_rel(full)
            if rel:
                with self.lock:
                    # delete wins over an earlier sync in the same batch
                    self.pending[rel] = "delete"
        elif mask & flags.MODIFY:
            # can only happen on the top-level home watch (files aren't
            # individually watched); treat as sync
            if wd_path.endswith("|top"):
                with self.lock:
                    self.pending[".bashrc"] = "sync"

    def flush(self):
        with self.lock:
            batch, self.pending = self.pending, {}
        if not batch:
            return
        log(f"flush: {len(batch)} pending ops")
        for key, action in batch.items():
            try:
                if action == "sync":
                    full = os.path.join(SRC_ROOT, key) if key != ".bashrc" else os.path.expanduser("~/.bashrc")
                    if os.path.isfile(full):
                        self.sync_file(full, key)
                elif action == "mkdir":
                    yote(f"mkdir -p {YOTE_ROOT}/{key}")
                elif action == "delete":
                    # never let a delete escape the mirror root
                    if ".." in key or key.startswith("/"):
                        log(f"REFUSED delete of suspicious path: {key}")
                        continue
                    yote(f"rm -rf -- {YOTE_ROOT}/{key}")
                elif action == "move":
                    src, dst = key.split("\x00")
                    if ".." in src or ".." in dst:
                        log(f"REFUSED move of suspicious path: {key}")
                        continue
                    yote(f"mkdir -p $(dirname {YOTE_ROOT}/{dst}) && mv -- {YOTE_ROOT}/{src} {YOTE_ROOT}/{dst}")
            except Exception as e:
                log(f"op failed {action} {key}: {str(e)[:200]}")
        self.write_lastsync()
        log(f"flush done: {len(batch)} ops")

    def sync_file(self, full, rel):
        size = os.path.getsize(full)
        if size > 200 * 1024 * 1024:
            log(f"skip oversized {rel} ({size} bytes)")
            return
        dst = f"{YOTE_ROOT}/{rel}"
        # staging is per-process: concurrent sweeps (daemon catch-up vs.
        # supervisor repair sweep) must never share a staging file, or one
        # side's rm -f wipes the other's chunks and base64 -d fails -> the
        # RuntimeError used to propagate out of initial_catchup() and kill
        # the daemon (its finally-block unlinks the PID file).
        tmp = f"{YOTE_INC}/{rel.replace('/', '_')}.{os.getpid()}.b64"
        yote(f"mkdir -p $(dirname {tmp}) && rm -f {tmp} && touch {tmp} && mkdir -p $(dirname {dst})")
        with open(full, "rb") as f:
            idx = 0
            while True:
                data = f.read((CHUNK_B64 * 3) // 4)
                if not data:
                    break
                b64 = base64.b64encode(data).decode()
                ok = False
                for _ in range(3):
                    d = yote_exec(f"python3 -c \"open('{tmp}','a').write('{b64}')\"", timeout=60)
                    if d.get("code") == 0:
                        ok = True
                        break
                    time.sleep(2)
                if not ok:
                    raise RuntimeError(f"chunk {idx} failed for {rel}")
                idx += 1
        yote(f"base64 -d {tmp} > {dst}.tmp && mv {dst}.tmp {dst} && rm -f {tmp}", timeout=300)

def main():
    if "--repair-only" in sys.argv:
        # Supervisor's periodic sweep: catch in-place content modifications
        # (IN_MODIFY) that directory watches cannot see. No daemon needed.
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        log("repair sweep start")
        Mirror().initial_catchup()
        log("repair sweep done")
        return
    os.makedirs(os.path.dirname(PIDFILE), exist_ok=True)
    # single instance
    try:
        with open(PIDFILE) as f:
            old = int(f.read().strip())
        os.kill(old, 0)
        print(f"already running as pid {old}", file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError):
        pass
    with open(PIDFILE, "w") as f:
        f.write(str(os.getpid()))
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    log("=== cell-mirror daemon start ===")
    try:
        Mirror().run()
    finally:
        try:
            os.unlink(PIDFILE)
        except OSError:
            pass

if __name__ == "__main__":
    main()
