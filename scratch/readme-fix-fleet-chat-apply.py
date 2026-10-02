#!/usr/bin/env python3
"""Apply surgical README fixes for toxicwind/fleet-chat per audit report."""
import re, sys

readme_path = "/home/toxic/readme-fix-fleetchat-47097/README.md"
pyproject_path = "/home/toxic/readme-fix-fleetchat-47097/pyproject.toml"

text = open(readme_path).read()
orig = text
edits = []

def sub(old, new, count=1):
    global text
    assert old in text, f"OLD NOT FOUND: {old[:80]!r}"
    assert text.count(old) == count, f"OLD occurs {text.count(old)}x, expected {count}: {old[:80]!r}"
    text = text.replace(old, new, count)
    edits.append(old[:60])

# 1. Arch tree: .presence/<agent>.json is wrong; real dirs are .heartbeats/.peers/.suspects
#    (fleet_presence.py:43-45 documents exact formats). Also add .cursors to this tree.
sub(
"""  .clocks/<agent>                   # Lamport clocks (fleet_time)
  .presence/<agent>.json            # liveness hints, NOT identity (fleet_presence)
```""",
"""  .clocks/<agent>                   # Lamport clocks (fleet_time)
  .heartbeats/<agent>.json          # liveness hints, NOT identity (fleet_presence)
  .peers/<agent>.json               # SWIM peer views (fleet_presence)
  .suspects/<peer>.json             # suspicion marks (fleet_presence)
  .cursors/<agent>                  # read cursors (chat.py, fleet_delta)
```""")

# 2. stdlib-only claim is wrong: fleet_e2ee.py needs third-party cryptography
sub(
"""One Python file (`chat.py`, stdlib only) plus `fleet_*.py` modules, also
stdlib only. The base's guarantees are kept: atomic seq allocation under a""",
"""One Python file (`chat.py`, stdlib only) plus `fleet_*.py` modules, stdlib
only with one exception: `fleet_e2ee.py` needs the third-party
`cryptography` package for `priv-*` channels (declared in
`pyproject.toml`; `pip install cryptography` if it isn't importable).
The base's guarantees are kept: atomic seq allocation under a""")

# 3. chat.py "pristine at 914d1c0" is wrong: heavily extended by fleet commits
sub(
"| `chat.py` (pristine at `914d1c0`) |",
"| `chat.py` (upstream base, extended by the fleet commits below) |")

# 4. Disambiguate donor-repo paths in the provenance table
sub(
"""What was *not* taken, on purpose: every server, WebSocket, REST API, Docker
setup, Node runtime, and turn-taking/arbiter model in the six donors. The
WhatsApp-side agent has a filesystem and nothing else.""",
"""All `src/`, `cmd/`, `internal/`, `app/`, and `scripts/` paths in the table
above live in the *donor* repositories, not in this one — this repo is
Python-only (`chat.py`, `fleet_*.py`).

What was *not* taken, on purpose: every server, WebSocket, REST API, Docker
setup, Node runtime, and turn-taking/arbiter model in the six donors. The
WhatsApp-side agent has a filesystem and nothing else.""")

# 5. Paper-screening numbers unverifiable: keep only what's provable (10 implemented)
sub(
"""A paper hunt screened 59 candidates and selected 12; ten were implemented
as working, tested code below. Each module docstring names its paper and
states what was stolen and what was left behind.""",
"""A paper hunt screened dozens of candidates; ten were implemented
as working, tested code below. Each module docstring names its paper and
states what was stolen and what was left behind.""")

# 6. (7/7) test counts not derivable from the tree: drop the counts, keep behaviors
sub("- **E2EE (7/7):** key provisioning,", "- **E2EE:** key provisioning,")
sub("- **HMAC v2 (7/7):** new posts verify as v2;", "- **HMAC v2:** new posts verify as v2;")

# 7. cryptography prerequisite for priv-* channels (README claims stdlib-only today)
sub(
"""`read`/`wait`/
`peek` verify-then-decrypt. Ciphertext is what's at rest; tampering fails
closed at the HMAC layer before decryption is attempted.""",
"""`read`/`wait`/
`peek` verify-then-decrypt. Ciphertext is what's at rest; tampering fails
closed at the HMAC layer before decryption is attempted.

Prerequisite: `pip install cryptography` (also declared in
`pyproject.toml`). Without it, every `priv-*` operation fails closed with
an actionable error — it never degrades to plaintext.""")

open(readme_path, "w").write(text)
print(f"README: {len(edits)} edits applied")

# 8. Declare cryptography in pyproject.toml [project] dependencies
pt = open(pyproject_path).read()
anchor = 'version = "0.7.2"  # managed by python-semantic-release; do not hand-edit\n'
assert anchor in pt, "pyproject anchor not found"
assert "cryptography" not in pt, "cryptography already declared"
pt = pt.replace(anchor, anchor + 'dependencies = [\n'
    '    "cryptography>=41.0.0",  # required by fleet_e2ee.py for priv-* channels\n'
    ']\n', 1)
open(pyproject_path, "w").write(pt)
print("pyproject: cryptography dependency added")

assert text != orig
print("OK")
