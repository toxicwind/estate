#!/usr/bin/env python3
"""Winners ledger: JSONL, fsync'd."""
from __future__ import annotations

import json
import os
from pathlib import Path


def append(path, entry) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return str(p)
