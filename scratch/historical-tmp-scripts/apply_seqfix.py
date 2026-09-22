#!/usr/bin/env python3
"""Apply the monotonic seq-alloc patch to the squawk worktree.

Exact-string replacements; aborts loudly if any anchor is missing or
ambiguous. Run on yote against the worktree root passed as argv[1].
"""
import sys
from pathlib import Path

WT = Path(sys.argv[1])

PATCHES = {
    # --- feed server ----------------------------------------------------
    "projects/mesh/squawk/squawk_feed.py": [
        (
            "import fleet_relay\n",
            "import fleet_relay\nimport seq_alloc\n",
        ),
        (
            "        self.high = _channel_high(chan_dir)\n",
            "        # Durable high-water floor (2026-09-21): after message\n"
            "        # deletions the disk-derived max can sit below seqs the\n"
            "        # feed already broadcast, so seed from the monotonic\n"
            "        # allocator too -- never start below it.\n"
            "        self.high = max(_channel_high(chan_dir),\n"
            "                        seq_alloc.read_high(chan_dir.parent, channel))\n",
        ),
        (
            "            max_seq = _channel_high(chan_dir)\n"
            "            seq = max_seq + 1\n",
            "            # Monotonic durable allocation (2026-09-21): the old\n"
            "            # disk-derived next-seq reused dead numbers after\n"
            "            # deletions and the in-memory high-water mark then\n"
            "            # suppressed those messages forever (seq <= high\n"
            "            # looks already-delivered). alloc_seq serializes on\n"
            "            # its own internal flock; safe inside this outer lock.\n"
            "            seq = seq_alloc.alloc_seq(root, channel)\n",
        ),
    ],
    # --- canonical chat_core --------------------------------------------
    "projects/mesh/squawk/chat_core.py": [
        (
            "from pathlib import Path\n"
            "\n"
            "from fleet_addr import addressed_wait_filter\n",
            "from pathlib import Path\n"
            "\n"
            "try:\n"
            "    import seq_alloc\n"
            "except ImportError:  # imported from a different cwd: look next to this file\n"
            "    sys.path.insert(0, str(Path(__file__).resolve().parent))\n"
            "    import seq_alloc\n"
            "\n"
            "from fleet_addr import addressed_wait_filter\n",
        ),
        (
            "def _next_seq(chan: Path) -> int:\n"
            "    return max_seq(chan) + 1\n",
            "def _next_seq(chan: Path) -> int:\n"
            '    """Monotonic seq allocation via the durable high-water mark.\n'
            "\n"
            "    Never reuses a deleted seq (2026-09-21: disk-derived next-seq\n"
            "    reused dead numbers and the feed suppressed those messages\n"
            "    forever). MUST run inside the per-channel seq lock; alloc_seq\n"
            "    serializes the read-modify-write on its own internal flock\n"
            "    as well.\n"
            '    """\n'
            "    return seq_alloc.alloc_seq(chan.parent, chan.name)\n",
        ),
    ],
    # --- legacy hatch/agents/ember/chat ----------------------------------
    "hatch/agents/ember/chat/chat.py": [
        (
            "from pathlib import Path\n"
            "\n"
            "from fleet_addr import addressed_wait_filter\n",
            "from pathlib import Path\n"
            "\n"
            "try:\n"
            "    import seq_alloc\n"
            "except ImportError:  # canonical allocator lives in the mesh squawk sources\n"
            '    sys.path.insert(0, "/home/toxic/sovereign/projects/mesh/squawk")\n'
            "    import seq_alloc\n"
            "\n"
            "from fleet_addr import addressed_wait_filter\n",
        ),
        (
            "def _next_seq(chan: Path) -> int:\n"
            "    return max_seq(chan) + 1\n",
            "def _next_seq(chan: Path) -> int:\n"
            '    """Monotonic seq allocation via the durable high-water mark.\n'
            "\n"
            "    Never reuses a deleted seq (2026-09-21: disk-derived next-seq\n"
            "    reused dead numbers and the feed suppressed those messages\n"
            "    forever). MUST run inside the per-channel seq lock; alloc_seq\n"
            "    serializes the read-modify-write on its own internal flock\n"
            "    as well.\n"
            '    """\n'
            "    return seq_alloc.alloc_seq(chan.parent, chan.name)\n",
        ),
    ],
}

failed = False
pending = {}
for rel, reps in PATCHES.items():
    p = WT / rel
    text = p.read_text(encoding="utf-8")
    for old, new in reps:
        n = text.count(old)
        if n != 1:
            print(f"ANCHOR FAIL [{rel}]: found {n}x: {old[:70]!r}")
            failed = True
            continue
        text = text.replace(old, new)
        print(f"patched [{rel}]: {old[:50]!r}...")
    pending[rel] = (p, text)

if failed:
    print("PATCH ABORTED -- nothing written")
    sys.exit(1)
for rel, (p, text) in pending.items():
    p.write_text(text, encoding="utf-8")
print("all patches applied")
