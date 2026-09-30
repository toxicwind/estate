#!/usr/bin/env bash
# fleet-mirror-flush — complete yote-journaled fleet messages.
#
# Sweeps /home/toxic/hatch/fleet-outbox/pending/*.json — the write-ahead
# journal that fleet-post (hatch cell) writes concurrently with its delivery
# race. For each record:
#   - if its uuid is already present in the fleet channel -> delete the
#     record (already delivered; this also repairs a journalDelete that raced
#     a late-arriving journal write).
#   - else if the same (sender, message body) is already present in the
#     channel (posted via `squawk send`, which carries no uuid) -> delete
#     the record (already delivered; no double-post).
#   - else -> post the message by direct file write into the channel dir
#     (same frontmatter format as fleet-post path B, same uuid) and delete
#     the record.
#
# Why the content check exists: fleet-post's path A (`squawk send`) embeds
# the uuid NOWHERE — only path B's frontmatter carries it. A uuid-only
# already-delivered check therefore misses every path-A delivery and
# double-posts (observed 2026-09-30: 7 duplicates in one sweep). The
# (sender, body) check over files with mtime near the journal's own mtime
# closes that gap. Both checks are idempotent: a crash between post and
# delete is repaired on the next run.
#
# SCOPE: this sweeps ONLY the yote mirror. The cell spool
# (~/workspace/fleet-outbox on the hatch cell — the bridge-DOWN last resort)
# is swept by the Hatch platform cron "fleet-outbox-flush". The two stores
# are disjoint by construction (a message is journaled to exactly one,
# depending on whether the journal write landed), so there is no double-fire.
set -u
PENDING="${PENDING:-/home/toxic/hatch/fleet-outbox/pending}"
LOG="${LOG:-/home/toxic/hatch/fleet-outbox/flush.log}"
LOCK="${LOCK:-/home/toxic/hatch/fleet-outbox/flush.lock}"
SQUAWK_ROOT="${SQUAWK_ROOT:-/home/toxic/.fleet-bus/squawk-root}"

log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }

[ -d "$PENDING" ] || exit 0
exec 9>"$LOCK" || exit 0
flock -n 9 || exit 0   # another run holds the lock; skip quietly

shopt -s nullglob
records=( "$PENDING"/*.json )
[ ${#records[@]} -eq 0 ] && exit 0

n_already=0
n_completed=0
n_bad=0
for rec in "${records[@]}"; do
  result="$(python3 - "$rec" "$SQUAWK_ROOT" <<'PYEOF'
import json, os, re, sys, time

rec_path, squawk_root = sys.argv[1], sys.argv[2]
fname = os.path.basename(rec_path)
if not re.fullmatch(r"[a-f0-9-]{8,40}\.json", fname):
    print("BAD filename"); sys.exit(0)
uuid = fname[:-5]
try:
    with open(rec_path) as f:
        r = json.load(f)
except Exception:
    print("BAD json"); sys.exit(0)
sender = str(r.get("sender", "")).strip() or "agent (ember's pack)"
channel = str(r.get("channel", "")).strip() or "fleet"
message = str(r.get("message", ""))
ts = str(r.get("ts", "")).strip()
if str(r.get("uuid", "")) != uuid or not message or not re.fullmatch(r"[a-z0-9_-]{1,40}", channel):
    print("BAD content"); sys.exit(0)

def delivered_already(chan_dir, uuid, sender, message, rec_mtime):
    """True if the channel already holds this message.
    (1) uuid match anywhere in frontmatter head — catches path-B posts and
        this flusher's own earlier completions.
    (2) (sender, body) match on files with mtime near the journal's mtime —
        catches path-A (`squawk send`) posts, which carry no uuid."""
    uuid_b = ("uuid: " + uuid).encode()
    want_body = message.strip()
    try:
        names = os.listdir(chan_dir)
    except OSError:
        return False
    # Pass 1: uuid over the whole channel (cheap 2KB head reads).
    for name in names:
        if not name.endswith(".md"):
            continue
        p = os.path.join(chan_dir, name)
        try:
            with open(p, "rb") as f:
                head = f.read(2048)
        except OSError:
            continue
        if uuid_b in head:
            return True
    # Pass 2: (sender, body) over files written near the journal record.
    for name in names:
        if not name.endswith(".md"):
            continue
        p = os.path.join(chan_dir, name)
        try:
            if abs(os.path.getmtime(p) - rec_mtime) > 900:
                continue
            with open(p, "rb") as f:
                raw = f.read(65536)
        except OSError:
            continue
        try:
            text = raw.decode("utf-8", "replace")
        except Exception:
            continue
        lines = text.split("\n")
        if not lines or lines[0].strip() != "---":
            continue
        try:
            end = lines.index("---", 1)
        except ValueError:
            continue
        fm, body = lines[1:end], "\n".join(lines[end + 1:])
        frm = ""
        for ln in fm:
            if ln.startswith("from:"):
                frm = ln[5:].strip()
                break
        if frm == sender and body.strip() == want_body:
            return True
    return False

chan_dir = os.path.join(squawk_root, channel)
os.makedirs(chan_dir, exist_ok=True)
# already delivered? (repairs journalDelete/delete races + crash windows;
# also catches path-A posts via the (sender, body) check)
try:
    rec_mtime = os.path.getmtime(rec_path)
except OSError:
    rec_mtime = time.time()
if delivered_already(chan_dir, uuid, sender, message, rec_mtime):
    os.remove(rec_path)
    print("ALREADY"); sys.exit(0)

# post it: same frontmatter shape as fleet-post path B, same uuid
slug = re.sub(r"[^a-z0-9]+", "-", sender.lower()).strip("-") or "agent"
out_name = "%d-%s-%s.md" % (int(time.time() * 1000), slug, uuid)
front = ("---\nseq: ts-%d\nfrom: %s\nto: all\nchannel: %s\nts: %s\n"
         "status: discussion\nuuid: %s\ntitle: msg\n---\n%s\n"
         % (int(time.time() * 1000), sender, channel, ts, uuid, message))
out_path = os.path.join(chan_dir, out_name)
with open(out_path, "w") as f:
    f.write(front)
if os.path.getsize(out_path) > 0:
    os.remove(rec_path)
    print("COMPLETED " + out_name)
else:
    print("BAD write-failed")
PYEOF
)"
  case "$result" in
    ALREADY*) n_already=$((n_already+1)) ;;
    COMPLETED*) n_completed=$((n_completed+1)); log "completed $result uuid=$(basename "$rec" .json)" ;;
    BAD*) n_bad=$((n_bad+1)); log "bad record $result: $rec" ;;
    *) log "unexpected result for $rec: $result" ;;
  esac
done

if [ "$n_completed" -gt 0 ] || [ "$n_bad" -gt 0 ] || [ "$n_already" -gt 0 ]; then
  log "sweep done: completed=$n_completed already_delivered=$n_already bad=$n_bad"
fi
exit 0
