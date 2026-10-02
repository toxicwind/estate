#!/usr/bin/env python3
"""tmp-classify — /tmp provenance classifier.

Scans a temp directory and classifies every entry by provenance so a repo
sweep can delete the disposable, integrate the meaningful, and quarantine
the secret-shaped — without a manual hunt.

Classes:
  DISPOSABLE  transfer fragments, caches, empty files, tool outputs,
              log dumps, locks, pid files. Safe to delete after review.
  MEANINGFUL  scripts, docs, configs, source, data worth a repo home.
  SECRET      secret-shaped names or content. NEVER delete silently,
              NEVER commit. Report shape only, never values.
  IN_USE      sockets, fifos, X11/ICE dirs, live tmux sockets. Leave alone.
  UNKNOWN     needs a worker's eyes.

Usage:
  tmp-classify.py [--root /tmp] [--json] [--delete-disposable] [--min-age-min 30]

  --delete-disposable  actually remove DISPOSABLE entries (default: dry run).
                       Never touches SECRET / IN_USE / UNKNOWN, and never
                       touches anything younger than --min-age-min (default 30)
                       unless --min-age-min 0.

Exit codes: 0 ok; 2 secrets were found (reported, nothing deleted).

The script is box-local and stdlib-only: copy it to the target box
(e.g. via yote-conn) and run it there. Do NOT run a hatch scan and apply
the verdicts to yote — different boxes, different provenance.
"""

import argparse
import base64
import hashlib
import json
import os
import re
import stat
import sys
import time

# ---------------------------------------------------------------------------
# Rule tables
# ---------------------------------------------------------------------------

# Exact names / dirs that are always live runtime state
IN_USE_NAMES = {
    ".ICE-unix", ".X11-unix", ".XIM-unix", ".font-unix",
    "tmux-0",
}

# Name regexes -> (class, reason). Checked in order; first match wins.
NAME_RULES = [
    # secrets first: never misclassify a secret as disposable
    (r"\.(tok|pem|key|p12|pfx|jks|kdbx)$", "SECRET", "secret-shaped extension"),
    (r"(^|[/_.~-])(id_rsa|id_ed25519|id_ecdsa)(\.|$)", "SECRET", "private key name"),
    (r"(^|[/_.~-])\.?netrc$", "SECRET", "netrc file"),
    (r"secret|credential|passwd|shadow", "SECRET", "secret-shaped name"),
    (r"\.env(\.|$)", "SECRET", "dotenv file"),
    # in-use runtime state
    (r"^tmux-", "IN_USE", "tmux socket"),
    # transfer fragments: base64 / chunked payloads shuttled between boxes
    (r"\.b64$", "DISPOSABLE", "base64 transfer fragment"),
    (r"\.b64chunks$", "DISPOSABLE", "base64-chunk transfer fragment"),
    (r"\.chunk\.[a-z0-9]+$", "DISPOSABLE", "split chunk"),
    (r"(^|-)chunk-[a-z0-9]+$", "DISPOSABLE", "split chunk"),
    (r"\.part$", "DISPOSABLE", "partial transfer"),
    (r"\.hm$", "DISPOSABLE", "empty hash-lock marker"),
    # caches
    (r"^(node-compile-cache|__pycache__)$", "DISPOSABLE", "build cache"),
    (r"^bunx-", "DISPOSABLE", "bunx cache"),
    (r"^hsperfdata_", "DISPOSABLE", "jvm perfdata"),
    # locks / pids / sockets
    (r"\.(pid|lock|lck)$", "DISPOSABLE", "lock/pid file"),
    (r"(^|/)fslock$", "DISPOSABLE", "file lock dir"),
    # tool outputs / dumps (regenerable)
    (r"jarvis-tool-output-", "DISPOSABLE", "jarvis tool output dump"),
    (r"-baseline\.(json|ya?ml)$", "DISPOSABLE", "baseline dump"),
    (r"mat-debug-.*\.log$", "DISPOSABLE", "mat debug log"),
    (r"(^|/)fleet\.(txt|log)$", "DISPOSABLE", "fleet log scrape"),
    (r"(^|/)leads\.txt$", "DISPOSABLE", "leads scrape"),
    # one-off transfer/patch job scripts: printf-chunked base64 into /tmp/xfer.b64
    # (content rule below confirms; name alone is only a hint)
]

# Content regexes -> (class, reason). Only read first 64KB of regular files.
CONTENT_RULES = [
    (r"(?i)(api[_-]?key|secret[_-]?key|bearer|client[_-]?secret)\s*[:=]\s*['\"]?\S{20,}",
     "SECRET", "credential-shaped assignment in content"),
    (r"-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
     "SECRET", "private key material in content"),
    (r"printf\s+'%s'\s+'[A-Za-z0-9+/=]{200,}'.*base64\s+-d",
     "DISPOSABLE", "chunked base64 transfer job script"),
    (r"/tmp/xfer\.b64", "DISPOSABLE", "xfer.b64 transfer job script"),
]

TRANSFER_JOB_HINTS = re.compile(r"xfer|mr-patch|chunk", re.IGNORECASE)

SHEBANG_RE = re.compile(r"^#!\s*\S+")
B64_RE = re.compile(r"^[A-Za-z0-9+/=\s]+$")
KV_LINE_RE = re.compile(r"^\s*\d+\s+\S")  # "12345 name" inventory lines


def is_mostly_base64(text):
    """True if the body is overwhelmingly base64 alphabet (a transfer fragment)."""
    body = text.strip()
    if len(body) < 100:
        return False
    sample = body[:20000]
    b64chars = sum(1 for c in sample if c in
                   "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/= \t\n\r")
    return b64chars / max(len(sample), 1) > 0.97


def looks_like_inventory(text):
    """Size-sorted inventory dump: most lines are '<number> <name>'."""
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 5:
        return False
    kv = sum(1 for l in lines[:200] if KV_LINE_RE.match(l))
    return kv / min(len(lines), 200) > 0.7


def looks_like_log_scrape(text):
    """Fleet/channel scrape: many lines with [seq] author @ timestamp shapes."""
    lines = text.splitlines()[:200]
    if len(lines) < 20:
        return False
    scrapey = sum(1 for l in lines if re.search(r"\[\d{4,}\].*@.*\d{4}-\d{2}-\d{2}", l))
    return scrapey / len(lines) > 0.3


def classify(path, name, st, now, min_age_min):
    """Return (class, reason)."""
    mode = st.st_mode
    # --- type-based first ---
    if stat.S_ISSOCK(mode):
        return "IN_USE", "unix socket"
    if stat.S_ISFIFO(mode):
        return "IN_USE", "fifo"
    if name in IN_USE_NAMES:
        return "IN_USE", "runtime state dir/socket"
    if stat.S_ISDIR(mode):
        return "UNKNOWN", "directory: inspect contents"
    if not stat.S_ISREG(mode):
        return "UNKNOWN", "special file"
    if st.st_size == 0:
        return "DISPOSABLE", "empty file"

    # --- name rules ---
    for pat, cls, reason in NAME_RULES:
        if re.search(pat, name):
            return cls, reason

    # --- content rules (first 64KB) ---
    try:
        with open(path, "rb") as fh:
            raw = fh.read(65536)
    except OSError as e:
        return "UNKNOWN", f"unreadable: {e}"
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        # binary blob: check magic-ish; tarballs/archives are data, not fragments
        if raw[:2] == b"\x1f\x8b" or raw[:4] == b"PK\x03\x04":
            return "MEANINGFUL", "archive: inspect via als, never extract blindly"
        return "UNKNOWN", "binary blob"

    for pat, cls, reason in CONTENT_RULES:
        if re.search(pat, text):
            return cls, reason

    if is_mostly_base64(text):
        return "DISPOSABLE", "base64-only content (transfer fragment)"
    if looks_like_inventory(text):
        return "DISPOSABLE", "inventory dump (regenerable)"
    if looks_like_log_scrape(text):
        return "DISPOSABLE", "log/channel scrape (regenerable)"

    # one-off transfer job scripts: chunked printf + base64, no lasting value
    if name.endswith((".py", ".sh")) and TRANSFER_JOB_HINTS.search(name) \
            and ("base64" in text or "xfer" in text):
        return "DISPOSABLE", "one-off transfer job script"

    # meaningful shapes
    if SHEBANG_RE.match(text) or name.endswith(
            (".py", ".sh", ".go", ".rs", ".ts", ".js", ".toml", ".yaml", ".yml", ".md")):
        return "MEANINGFUL", "script/doc/config/source: needs a repo home"
    if text.lstrip().startswith(("{", "[")):
        return "MEANINGFUL", "structured data: check provenance"

    return "UNKNOWN", "no rule matched"


def find_reassembled(root, entries):
    """Detect chunk sets whose decode matches another file in root.

    Returns {chunk_group_prefix: original_name} for confirmed reassemblies,
    so the chunks can be deleted with confidence.
    """
    by_md5 = {}
    for e in entries:
        p = os.path.join(root, e)
        try:
            st = os.lstat(p)
        except OSError:
            continue
        if stat.S_ISREG(st.st_mode) and st.st_size and st.st_size < 5_000_000:
            try:
                with open(p, "rb") as fh:
                    by_md5.setdefault(hashlib.md5(fh.read()).hexdigest(), p)
            except OSError:
                pass
    # group candidate chunk files by common prefix
    groups = {}
    for e in entries:
        m = re.match(r"^(.+?)[._-]?(chunk|b64|part)[._-]?([a-z0-9]{2,4})$", e,
                     re.IGNORECASE)
        if m:
            groups.setdefault(m.group(1), []).append(e)
    confirmed = {}
    for prefix, members in groups.items():
        if len(members) < 2:
            continue
        members.sort()
        blob = b""
        ok = True
        for m in members:
            try:
                with open(os.path.join(root, m), "rb") as fh:
                    blob += fh.read().strip()
            except OSError:
                ok = False
                break
        if not ok:
            continue
        for enc in ("utf-8", "ascii"):
            try:
                decoded = base64.b64decode(blob, validate=True)
                break
            except Exception:
                decoded = None
        if decoded is None:
            continue
        hit = by_md5.get(hashlib.md5(decoded).hexdigest())
        if hit and os.path.basename(hit) not in members:
            confirmed[prefix] = os.path.basename(hit)
    return confirmed


def main():
    ap = argparse.ArgumentParser(description="Classify /tmp entries by provenance.")
    ap.add_argument("--root", default="/tmp")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--delete-disposable", action="store_true",
                    help="Actually delete DISPOSABLE entries (default: dry run).")
    ap.add_argument("--min-age-min", type=int, default=30,
                    help="Never delete anything younger than this (default 30).")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    now = time.time()
    try:
        entries = sorted(os.listdir(root))
    except OSError as e:
        print(f"cannot list {root}: {e}", file=sys.stderr)
        return 1

    results = []
    for name in entries:
        path = os.path.join(root, name)
        try:
            st = os.lstat(path)
        except OSError as e:
            results.append({"path": path, "class": "UNKNOWN",
                            "reason": f"lstat failed: {e}", "size": -1,
                            "mtime": None})
            continue
        cls, reason = classify(path, name, st, now, args.min_age_min)
        results.append({"path": path, "class": cls, "reason": reason,
                        "size": st.st_size, "mtime": st.st_mtime})

    reassembled = find_reassembled(root, entries)
    for prefix, original in reassembled.items():
        for r in results:
            base = os.path.basename(r["path"])
            if base.startswith(prefix) and r["class"] == "DISPOSABLE" \
                    and "transfer fragment" in r["reason"]:
                r["reason"] += f"; reassembles byte-identical to {original}"

    deleted, skipped_young, secrets = [], [], 0
    if args.delete_disposable:
        for r in results:
            if r["class"] != "DISPOSABLE":
                if r["class"] == "SECRET":
                    secrets += 1
                continue
            if r["mtime"] and (now - r["mtime"]) < args.min_age_min * 60:
                skipped_young.append(r["path"])
                continue
            try:
                if os.path.isdir(r["path"]) and not os.path.islink(r["path"]):
                    import shutil
                    shutil.rmtree(r["path"])
                else:
                    os.unlink(r["path"])
                deleted.append(r["path"])
            except OSError as e:
                r["reason"] += f"; DELETE FAILED: {e}"
    else:
        secrets = sum(1 for r in results if r["class"] == "SECRET")

    summary = {
        "root": root,
        "scanned": len(results),
        "by_class": {},
        "reassembled_chunks": reassembled,
        "deleted": deleted,
        "skipped_too_young": skipped_young,
        "dry_run": not args.delete_disposable,
    }
    for r in results:
        summary["by_class"][r["class"]] = summary["by_class"].get(r["class"], 0) + 1

    if args.json:
        print(json.dumps({"summary": summary, "entries": results}, indent=1))
    else:
        print(f"# tmp-classify {root} — {len(results)} entries "
              f"({'DRY RUN' if not args.delete_disposable else 'DELETE MODE'})")
        for cls in ("DISPOSABLE", "MEANINGFUL", "SECRET", "IN_USE", "UNKNOWN"):
            items = [r for r in results if r["class"] == cls]
            if not items:
                continue
            print(f"\n## {cls} ({len(items)})")
            for r in sorted(items, key=lambda x: x["path"]):
                age = ("age?"
                       if r["mtime"] is None
                       else f"{int((now - r['mtime']) / 60)}m")
                print(f"  {r['path']}  [{r['size']}B {age}] — {r['reason']}")
        if reassembled:
            print("\n## reassembled chunk sets (safe to delete the chunks)")
            for prefix, original in reassembled.items():
                print(f"  {prefix}*  ->  {original}")
        if args.delete_disposable:
            print(f"\ndeleted {len(deleted)}, skipped {len(skipped_young)} too young")
    return 2 if secrets else 0


if __name__ == "__main__":
    sys.exit(main())