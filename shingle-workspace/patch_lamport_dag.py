#!/usr/bin/env python3
"""Coordinator patch 5: Lamport tick + DAG parents in cmd_post."""
from pathlib import Path

CHAT = Path("/home/toxic/.shingle/chat/chat.py")
src = CHAT.read_text(encoding="utf-8")

def rep(old: str, new: str) -> None:
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new, 1)
    print(f"ok: {old[:60]!r}...")

# 1. imports
rep(
    "import fleet_ephemeral\nimport fleet_identity\n",
    "import fleet_dag\nimport fleet_ephemeral\nimport fleet_identity\n",
)
rep(
    "import fleet_roster\nimport fleet_wait\nimport fleet_watch\n",
    "import fleet_roster\nimport fleet_time\nimport fleet_wait\nimport fleet_watch\n",
)

# 2. DAG helpers, placed just before cmd_post
rep(
    "def cmd_post(root: Path, a):\n",
    '''def _resolve_reply_target(d: Path, reply: str):
    """Resolve a --reply value to a parent message id (or None)."""
    m = re.fullmatch(r"#?(\\d+)", reply.strip())
    if not m:
        return None  # name-style reply; no id join
    want = int(m.group(1))
    for p in message_files(d):
        if _seq_from_name(p.name) == want:
            return fleet_dag.msg_id(p)
    return None


def _dag_parents(d: Path, seq: int, reply):
    """Fleet DAG parent ids for a new message: [reply_target?, previous].

    Must run INSIDE the seq lock, after _next_seq: the "previous message" id
    is only stable while we hold it. Genesis (seq 1) gets [].
    """
    prev_id = None
    if seq > 1:
        prev_path = None
        prev_seq = 0
        for p in message_files(d):
            ps = _seq_from_name(p.name)
            if ps is not None and ps < seq and ps > prev_seq:
                prev_seq, prev_path = ps, p
        if prev_path is not None:
            prev_id = fleet_dag.msg_id(prev_path)
    target_id = _resolve_reply_target(d, reply) if reply else None
    return [x for x in (target_id, prev_id) if x]


def cmd_post(root: Path, a):
''',
)

# 3. cmd_post body: parents + lamport tick + frontmatter fields
rep(
    """    lock = _acquire_lock(d)
    try:
        seq = _next_seq(d)
        fname = f"{seq:04d}-{slugify(a.sender)}-{slugify(a.title)}.md\"""",
    """    lock = _acquire_lock(d)
    try:
        seq = _next_seq(d)
        # Fleet DAG: parent ids, computed under the seq lock (race-free).
        parents = _dag_parents(d, seq, reply)
        # Fleet Lamport: tick the sender's clock; readers sort causally.
        lamport = fleet_time.tick(root, sender)
        fname = f"{seq:04d}-{slugify(a.sender)}-{slugify(a.title)}.md\"""",
)

rep(
    """        fm += [
            f"channel: {channel}",
            f"ts: {timestamp}",
            f"status: {status}",
            f"title: {title}",
            f"hmac: {sig}",
            "---",
            "",
        ]""",
    """        fm += [
            f"channel: {channel}",
            f"ts: {timestamp}",
            f"status: {status}",
            f"title: {title}",
            f"lamport: {lamport}",
            f"parents: [{', '.join(parents)}]",
            f"hmac: {sig}",
            "---",
            "",
        ]""",
)

CHAT.write_text(src, encoding="utf-8")
print("patch applied:", CHAT)
