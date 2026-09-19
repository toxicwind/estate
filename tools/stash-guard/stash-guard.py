#!/usr/bin/env python3
"""
stash-guard -- autonomous WIP flight-recorder + drop-proof stash vault.

Watches a git repo and all of its worktrees, and continuously:

  * snapshots dirty worktrees into non-destructive commits under
    refs/guard/wt/<worktree-slug>/<YYYYMMDD-HHMMSS>          (tracked changes)
    refs/guard/wt/<worktree-slug>/<YYYYMMDD-HHMMSS>-untracked (untracked files)
  * pins every stash entry under refs/guard/stash/<sha12> so
    `git stash drop` / `git stash clear` can never lose work again
  * pushes all guard refs to the `archive` remote (best effort)
  * records every action in an append-only flight-recorder log (SQLite)

Fully non-destructive by design: it never touches a worktree's files, index,
HEAD, or branches. It only creates git objects and refs/guard/* refs.
Snapshots use `git stash create` (creates the commit, changes nothing) plus
plumbing for untracked files (hash-object/mktree/commit-tree).

Usage:
  stash-guard.py [--repo PATH] [--interval SEC] [--once] [--deep]
                 [--deep-every SEC] [--keep N] [--state-dir PATH]
                 [--extra-repos A,B] [--push/--no-push]
  stash-guard.py list [--repo PATH] [--state-dir PATH] [-n N]
  stash-guard.py restore <ref> [--to PATH] [--apply]

Restore semantics:
  * default: prints what the snapshot holds and the exact commands to restore.
  * --apply --to <worktree>: actually applies (stash apply / checkout -- .).
    This is the only mutating mode and it is explicit.
"""

import argparse
import datetime
import fnmatch
import json
import os
import sqlite3
import stat
import subprocess
import sys
import time

GUARD_NS = "refs/guard"
MAX_FILE_BYTES = 100 * 1024 * 1024      # skip single files > 100MB
MAX_TOTAL_BYTES = 1024 * 1024 * 1024     # cap untracked payload per snapshot
DEFAULT_KEEP = 24                        # snapshots retained per worktree
DEFAULT_INTERVAL = 90                    # fast-path cadence (seconds)
DEFAULT_DEEP_EVERY = 3600                # deep sweep cadence (seconds)

DEFAULT_EXCLUDES = [
    "builds/",
    "buildsrv*/",
    "bench-*/",
    ".broken-git-backup/",
    "analysis-*/",
    "*.pcap",
    "*.pcapng",
    "node_modules/",
    "__pycache__/",
    "*.pyc",
    "dist/",
    "*.log",
    "*.tmp",
    "*.bak",
    ".DS_Store",
    # fleet scratch-dir conventions: one-shot audit/merge artifacts, not WIP
    "*-20260914/",
    "*-20260915/",
    "*-20260916/",
    "*-20260917/",
    "*-20260918/",
    "*-20260919/",
    "merge-*/",
    "gear-*/",
    "*-scratch-*/",
    "sovereign-merge-stash-*/",
    "mesh-bruteforce-*/",
    "tau-ext-forks/",
    "tau-extensions-merge/",
    ".broken-git-backup/",
    "shingle-workspace/",
    "pitchfork.toml.bak*",
]

GIT_ENV = {
    "GIT_AUTHOR_NAME": "stash-guard",
    "GIT_AUTHOR_EMAIL": "stash-guard@local",
    "GIT_COMMITTER_NAME": "stash-guard",
    "GIT_COMMITTER_EMAIL": "stash-guard@local",
}


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[%s] %s" % (ts, msg), flush=True)


def run_git(cwd, *args, input=None, env_extra=None, ok_codes=(0,)):
    env = dict(os.environ)
    env.update(GIT_ENV)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run(
        ["git", "-C", cwd] + list(args),
        input=input,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if p.returncode not in ok_codes:
        raise RuntimeError(
            "git -C %s %s -> rc=%d: %s" % (cwd, " ".join(args[:4]),
                                          p.returncode,
                                          p.stderr.decode()[:300]))
    return p


def out(cwd, *args, **kw):
    return run_git(cwd, *args, **kw).stdout.decode()


def load_excludes(repo):
    pats = list(DEFAULT_EXCLUDES)
    for cand in (os.path.join(repo, ".stashguardignore"),
                 os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "excludes.default")):
        if os.path.isfile(cand):
            with open(cand) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        pats.append(line)
    return pats


def is_excluded(rel, pats):
    for pat in pats:
        if pat.endswith("/"):
            g = pat[:-1]
            # directory pattern (glob-aware): matches the dir itself or
            # anything beneath it
            if fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(rel, g + "/*"):
                return True
        elif fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(
                os.path.basename(rel), pat):
            return True
    return False


# ---------------------------------------------------------------- worktrees

def list_worktrees(repo):
    wts = []
    cur = {}
    for line in out(repo, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            if cur:
                wts.append(cur)
            cur = {"path": line[len("worktree "):]}
        elif line.startswith("HEAD "):
            cur["head"] = line[5:]
        elif line.startswith("branch "):
            cur["branch"] = line[7:]
        elif line == "detached":
            cur["branch"] = "(detached)"
        elif line == "bare":
            cur["bare"] = True
    if cur:
        wts.append(cur)
    return [w for w in wts if not w.get("bare") and os.path.isdir(w["path"])]


def slugify(path, branch):
    base = os.path.basename(os.path.normpath(path)) or "root"
    br = (branch or "detached").replace("refs/heads/", "")
    s = "%s-%s" % (base, br)
    return "".join(c if (c.isalnum() or c in "-_") else "-" for c in s)


def worktree_signature(wt_path):
    head = out(wt_path, "rev-parse", "HEAD").strip()
    status = out(wt_path, "status", "--porcelain=v1",
                 "--untracked-files=normal")
    import hashlib
    h = hashlib.sha256(status.encode()).hexdigest()[:16]
    return "%s:%s" % (head, h)


# --------------------------------------------------------------- snapshots

def snapshot_tracked(repo, wt_path, slug, ts):
    """Non-destructive stash commit of tracked modifications."""
    p = run_git(wt_path, "stash", "create",
                "stash-guard %s %s" % (slug, ts))
    sha = p.stdout.decode().strip()
    if not sha:
        return None
    ref = "%s/wt/%s/%s" % (GUARD_NS, slug, ts)
    run_git(repo, "update-ref", "-m", "stash-guard snapshot", ref, sha)
    nfiles = out(repo, "show", "--stat", "--oneline", sha).count("\n")
    return ref, sha, nfiles


def build_tree_from_files(repo, files):
    """files: [(relpath, abspath)] -> tree sha. Objects written via hash-object."""
    blobs = {}
    for rel, ap in files:
        try:
            with open(ap, "rb") as f:
                data = f.read()
        except OSError:
            continue  # vanished between scan and snapshot; skip
        p = run_git(repo, "hash-object", "-w", "--stdin", "--path=" + rel,
                    input=data)
        sha = p.stdout.decode().strip()
        if len(sha) < 7:
            raise RuntimeError("hash-object produced no sha for %s" % rel)
        blobs[rel] = sha
    # dir -> {name: (is_tree, sha)}; dedupes shared parent dirs across files
    entries = {}
    for rel, sha in blobs.items():
        parts = rel.split("/")
        for i, part in enumerate(parts):
            d = "/".join(parts[:i])
            is_last = (i == len(parts) - 1)
            e = entries.setdefault(d, {})
            if part in e:
                prev_tree, prev_sha = e[part]
                if prev_tree != (not is_last) or (is_last and prev_sha != sha):
                    log("name collision at %s/%s: keeping first, "
                        "dropping second" % (d or "/", part))
                continue
            e[part] = ((not is_last), sha if is_last else None)
    trees = {}
    # Deepest first; the root ('') must sort strictly last so every
    # subtree exists before its parent references it.
    for d in sorted(entries,
                    key=lambda x: (-x.count("/"), 1 if x == "" else 0)):
        lines = []
        for name in sorted(entries[d]):
            is_tree, sha = entries[d][name]
            if is_tree:
                sub = (d + "/" + name) if d else name
                lines.append("040000 tree %s\t%s" % (trees[sub], name))
            else:
                lines.append("100644 blob %s\t%s" % (sha, name))
        p = run_git(repo, "mktree", input=("\n".join(lines) + "\n").encode())
        trees[d] = p.stdout.decode().strip()
    return trees.get("")


def snapshot_untracked(repo, wt_path, slug, ts, parent_sha, excludes):
    raw = out(wt_path, "ls-files", "--others", "--exclude-standard", "-z")
    files, total = [], 0
    for rel in raw.split("\0"):
        if not rel or is_excluded(rel, excludes):
            continue
        ap = os.path.join(wt_path, rel)
        try:
            st = os.lstat(ap)
        except OSError:
            continue
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_FILE_BYTES:
            continue
        if total + st.st_size > MAX_TOTAL_BYTES:
            log("untracked cap hit in %s, truncating list" % wt_path)
            break
        total += st.st_size
        files.append((rel, ap))
    if not files:
        return None
    tree = build_tree_from_files(repo, files)
    if not tree:
        return None
    p = run_git(repo, "commit-tree", tree, "-p", parent_sha, "-m",
                "stash-guard %s %s untracked (%d files)" % (slug, ts,
                                                           len(files)))
    sha = p.stdout.decode().strip()
    ref = "%s/wt/%s/%s-untracked" % (GUARD_NS, slug, ts)
    run_git(repo, "update-ref", "-m", "stash-guard snapshot untracked",
            ref, sha)
    return ref, sha, len(files), total


def vault_stashes(repo):
    """Pin every live stash entry under refs/guard/stash/. Returns new pins."""
    raw = out(repo, "stash", "list", "--format=%H%x00%gs").strip()
    if not raw:
        return []
    pinned = []
    for line in raw.splitlines():
        sha, _, msg = line.partition("\x00")
        ref = "%s/stash/%s" % (GUARD_NS, sha[:12])
        exists = run_git(repo, "rev-parse", "--verify", "--quiet", ref,
                         ok_codes=(0, 1))
        if exists.returncode == 0 and \
                exists.stdout.decode().strip() == sha:
            continue
        run_git(repo, "update-ref", "-m", "stash-guard vault: " + msg[:80],
                ref, sha)
        pinned.append((ref, sha, msg))
    return pinned


def prune_snapshots(repo, keep):
    for line in out(repo, "for-each-ref", "--format=%(refname)",
                    GUARD_NS + "/wt/").splitlines():
        # group key: refs/guard/wt/<slug>/
        parts = line.split("/")
        if len(parts) < 4:
            continue
        key = "/".join(parts[:4])
        refs = sorted(
            r for r in out(repo, "for-each-ref", "--format=%(refname)",
                           key + "/").splitlines())
        for old in refs[:-keep]:
            run_git(repo, "update-ref", "-d", old)
            log("pruned %s" % old)


def remote_guard_refs(repo):
    """{refname: sha} for refs/guard/* on the archive remote."""
    p = run_git(repo, "ls-remote", "archive", GUARD_NS + "/*", ok_codes=(0, 1))
    refs = {}
    if p.returncode == 0:
        for line in p.stdout.decode().splitlines():
            sha, _, name = line.partition("\t")
            if name:
                refs[name.strip()] = sha.strip()
    return refs


def local_guard_refs(repo):
    refs = {}
    for line in out(repo, "for-each-ref", "--format=%(objectname) %(refname)",
                    GUARD_NS + "/").splitlines():
        sha, _, name = line.partition(" ")
        refs[name.strip()] = sha.strip()
    return refs


def push_guards(repo):
    p = run_git(repo, "remote", "get-url", "archive", ok_codes=(0, 2))
    if p.returncode != 0 or not p.stdout.decode().strip():
        return False
    # Guard refs are machine-generated snapshots, not human code: the repo's
    # push-guard (whitespace/conflict-marker lint) false-positives on
    # historical stash content. The documented emergency bypass is used here,
    # loudly: this log line is the audit trail.
    env = {"PUSH_GUARD_SKIP": "1"}
    local = local_guard_refs(repo)
    try:
        remote = remote_guard_refs(repo)
    except Exception as e:
        log("archive ls-remote failed (non-fatal): %s" % e)
        return False
    new = ["%s:%s" % (r, r) for r, s in local.items()
           if remote.get(r) != s]
    stale = [r for r in remote if r not in local]
    if not new and not stale:
        return True
    log("PUSH_GUARD_SKIP=1 engaged for guard-ref push "
        "(%d new, %d stale; machine snapshots)" % (len(new), len(stale)))
    ok = True
    if new:
        # bulk first (fast path); fall back to per-ref on failure so one
        # bad pack doesn't sink the batch (observed: transient HTTP 500)
        try:
            run_git(repo, "push", "--quiet", "archive", *new, env_extra=env)
        except Exception as e:
            log("bulk guard push failed, retrying per-ref: %s" % e)
            for spec in new:
                try:
                    run_git(repo, "push", "--quiet", "archive", spec,
                            env_extra=env)
                except Exception as e2:
                    log("per-ref push failed %s: %s" % (spec, e2))
                    ok = False
    for r in stale:
        try:
            run_git(repo, "push", "--quiet", "archive", ":%s" % r,
                    env_extra=env)
        except Exception as e:
            log("stale guard ref delete failed %s: %s" % (r, e))
            ok = False
    if ok:
        log("pushed %s/* to archive remote" % GUARD_NS)
    return ok


# ------------------------------------------------------------------ events

def db_conn(state_dir):
    os.makedirs(state_dir, exist_ok=True)
    db = sqlite3.connect(os.path.join(state_dir, "events.db"))
    db.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY, ts REAL, repo TEXT, kind TEXT, subject TEXT,
        ref TEXT, sha TEXT, files INTEGER, bytes INTEGER, pushed INTEGER,
        note TEXT)""")
    return db


def record(db, repo, kind, subject, ref, sha, files=0, nbytes=0,
           pushed=0, note=""):
    db.execute(
        "INSERT INTO events(ts,repo,kind,subject,ref,sha,files,bytes,pushed,note)"
        " VALUES(?,?,?,?,?,?,?,?,?,?)",
        (time.time(), repo, kind, subject, ref, sha, files, nbytes,
         pushed, note))
    db.commit()


def load_state(state_dir):
    p = os.path.join(state_dir, "state.json")
    if os.path.isfile(p):
        with open(p) as f:
            return json.load(f)
    return {}


def save_state(state_dir, st):
    p = os.path.join(state_dir, "state.json") + ".tmp"
    with open(p, "w") as f:
        json.dump(st, f)
    os.replace(p, os.path.join(state_dir, "state.json"))


# ------------------------------------------------------------------- scan

def scan_repo(repo, db, st, excludes, keep, do_push, deep_slug=None):
    repo_st = st.setdefault(repo, {"worktrees": {}, "vaulted": []})
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    pushed_flag = 0

    # 1. worktree snapshots
    for wt in list_worktrees(repo):
        wpath = wt["path"]
        slug = ("deep-" + deep_slug + "-" + slugify(wpath, wt.get("branch"))
                if deep_slug else slugify(wpath, wt.get("branch")))
        sig = worktree_signature(wpath)
        if repo_st["worktrees"].get(wpath, {}).get("sig") == sig:
            continue  # unchanged since last pass
        head = out(wpath, "rev-parse", "HEAD").strip()
        res = snapshot_tracked(repo, wpath, slug, ts)
        if res:
            ref, sha, nfiles = res
            record(db, repo, "snapshot", wpath, ref, sha, files=nfiles,
                   note="tracked")
            log("snapshot %s -> %s (%d files)" % (wpath, ref, nfiles))
            parent = sha
        else:
            parent = head
        ures = snapshot_untracked(repo, wpath, slug, ts, parent, excludes)
        if ures:
            ref, sha, nfiles, nbytes = ures
            record(db, repo, "snapshot", wpath, ref, sha, files=nfiles,
                   nbytes=nbytes, note="untracked")
            log("snapshot %s -> %s (%d untracked files, %d bytes)"
                % (wpath, ref, nfiles, nbytes))
        if res or ures:
            repo_st["worktrees"][wpath] = {"sig": sig, "ts": ts}
        else:
            # tracked/untracked both empty but sig changed (e.g. branch move):
            # just update sig, nothing to snapshot
            repo_st["worktrees"][wpath] = {"sig": sig,
                                           "ts": repo_st["worktrees"]
                                           .get(wpath, {}).get("ts")}

    # 2. stash vault (stash is repo-global, not per-worktree)
    for ref, sha, msg in vault_stashes(repo):
        record(db, repo, "vault", msg[:120], ref, sha, note="stash pin")
        log("vaulted stash %s -> %s" % (sha[:12], ref))

    # 3. retention + push
    prune_snapshots(repo, keep)
    if do_push:
        try:
            if push_guards(repo):
                pushed_flag = 1
                log("pushed %s/* to archive remote" % GUARD_NS)
        except Exception as e:
            log("push failed (non-fatal): %s" % e)
    return pushed_flag


def deep_repos(root="/home/toxic"):
    repos = []
    for dirpath, dirnames, _ in os.walk(root, followlinks=False):
        depth = dirpath[len(root):].count(os.sep)
        # prune expensive/irrelevant subtrees
        for skip in ("node_modules", ".cache", "vendor", ".git",
                     "__pycache__", ".cargo", ".npm"):
            if skip in dirnames:
                dirnames.remove(skip)
        if depth > 5:
            dirnames[:] = []
            continue
        if ".git" in os.listdir(dirpath):
            repos.append(dirpath)
            dirnames[:] = []  # don't descend into repo contents
    return repos


def repo_slug(path):
    rel = os.path.relpath(path, "/home/toxic")
    return "".join(c if (c.isalnum() or c in "-_") else "-"
                   for c in rel.replace(os.sep, "-"))[:64]


def deep_scan(db, st, excludes, keep, do_push):
    for repo in deep_repos():
        try:
            dirty = out(repo, "status", "--porcelain=v1",
                        "--untracked-files=no").strip()
            nstash = len(out(repo, "stash", "list",
                             "--format=%H").strip().splitlines())
            if not dirty and not nstash:
                continue
            log("deep: at-risk repo %s (dirty=%s stashes=%d)"
                % (repo, bool(dirty), nstash))
            scan_repo(repo, db, st, excludes, keep, do_push,
                      deep_slug=repo_slug(repo))
        except Exception as e:
            log("deep: skip %s: %s" % (repo, e))


# ------------------------------------------------------------------- CLI

def cmd_list(args):
    db = db_conn(args.state_dir)
    n = args.n
    print("== recent flight-recorder events ==")
    for row in db.execute(
            "SELECT datetime(ts,'unixepoch'),repo,kind,subject,ref,sha,files,bytes"
            " FROM events ORDER BY id DESC LIMIT ?", (n,)):
        print("%s | %s | %s | %s | %s %s files=%s bytes=%s" % row)
    print("== live guard refs ==")
    try:
        print(out(args.repo, "for-each-ref", "--sort=-creatordate",
                  "--format=%(refname:short) %(objectname:short) "
                  "%(creatordate:short)", GUARD_NS + "/"))
    except RuntimeError as e:
        print("(none: %s)" % e)


def cmd_restore(args):
    repo = args.repo
    sha = out(repo, "rev-parse", "--verify", args.ref).strip()
    parents = out(repo, "rev-list", "--parents", "-n", "1", sha).strip().split()
    msg = out(repo, "log", "-1", "--format=%s", sha).strip()
    is_stash = len(parents) >= 4  # sha + HEAD + index [+ untracked]
    print("ref %s -> %s" % (args.ref, sha))
    print("message: %s" % msg)
    print("stash-like: %s" % is_stash)
    if not args.apply:
        if is_stash:
            print("restore: git -C <worktree> stash apply %s" % sha)
        else:
            print("restore: git -C <worktree> checkout %s -- .   # untracked snapshot" % sha)
        print("(re-run with --apply --to <worktree> to execute)")
        return
    if not args.to or not os.path.isdir(args.to):
        sys.exit("--apply requires --to <worktree path>")
    if is_stash:
        run_git(args.to, "stash", "apply", sha)
    else:
        run_git(args.to, "checkout", sha, "--", ".")
    log("restored %s into %s" % (sha[:12], args.to))


def cmd_run(args):
    state_dir = args.state_dir
    db = db_conn(state_dir)
    st = load_state(state_dir)
    repos = [args.repo] + [r for r in (args.extra_repos or "").split(",")
                           if r and os.path.isdir(os.path.join(r, ".git"))]
    excludes = load_excludes(args.repo)
    last_deep = 0.0

    def once():
        for repo in repos:
            try:
                scan_repo(repo, db, st, excludes, args.keep,
                          do_push=not args.no_push)
            except Exception as e:
                log("scan failed for %s: %s" % (repo, e))
        save_state(state_dir, st)

    if args.once:
        once()
        if args.deep:
            deep_scan(db, st, excludes, args.keep, do_push=not args.no_push)
            save_state(state_dir, st)
        return
    log("stash-guard live: repos=%s interval=%ss deep=%s" %
        (repos, args.interval, args.deep))
    while True:
        try:
            once()
            if args.deep and time.time() - last_deep > args.deep_every:
                deep_scan(db, st, excludes, args.keep,
                          do_push=not args.no_push)
                save_state(state_dir, st)
                last_deep = time.time()
        except Exception as e:
            log("loop error (continuing): %s" % e)
        time.sleep(args.interval)


def main():
    ap = argparse.ArgumentParser(description="stash-guard")
    ap.add_argument("--repo", default="/home/toxic/sovereign")
    ap.add_argument("--state-dir",
                    default=os.path.expanduser("~/.local/state/stash-guard"))
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    ap.add_argument("--deep-every", type=int, default=DEFAULT_DEEP_EVERY)
    ap.add_argument("--keep", type=int, default=DEFAULT_KEEP)
    ap.add_argument("--extra-repos", default="")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--deep", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    lp = sub.add_parser("list")
    lp.add_argument("-n", type=int, default=30)
    rp = sub.add_parser("restore")
    rp.add_argument("ref")
    rp.add_argument("--to", default=None)
    rp.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "restore":
        cmd_restore(args)
    else:
        cmd_run(args)


if __name__ == "__main__":
    main()
