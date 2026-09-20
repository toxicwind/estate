# README audit — toxicwind/fleet-chat @ f0e973f0 — 2026-09-14

**Verdict:** NEEDS UPDATE

Mechanical (`bin/audit.py`): readme-exists PASS (10581 chars); mentioned-paths FAIL on
`src/hub/store.js` (donor-repo reference, see below — audit.py false positive, but the
path reads like a local path); quickstart-entrypoints WARN on `.bids/ .clocks/ .cursors/
.presence/ .traces/ .vectors/` (data dirs, not commands — false positive); relative
links, versions, badges, external links all PASS.

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| File-based, no daemon/sockets/HTTP, folder of Markdown | tree: no server code; chat.py imports stdlib+ctypes only | VERIFIED |
| Forked from `n24q02m/agent-chat-plugin` (Apache-2.0) | LICENSE, pyproject.toml `name = "agent-chat-plugin"`, CHANGELOG.md upstream releases | VERIFIED |
| Merged 6 other agent-chat repos + 10 papers | provenance tables; all 10 papers named in fleet_*.py docstrings (grep: Demers→fleet_gossip, Lamport→fleet_delta, SWIM/Jelasity→fleet_presence, De Nicola/Ferrante→fleet_stigmergy, Almeida→fleet_delta, Borth→fleet_dag, Wang→fleet_bids, Shapiro→fleet_crdt) | VERIFIED |
| `chat.py` (pristine at `914d1c0`) | chat.py modified in 44b3db46, 07aff5ca, 42586c4f, 1ae024df, 991ac87c (via `commits?path=chat.py`); 914d1c0 exists in history but the file is not pristine | WRONG |
| chat.py + fleet_*.py "stdlib only" | fleet_e2ee.py:86 `from cryptography.fernet import Fernet`; raises RuntimeError without it ("Refusing to handle private channels rather than degrading to plaintext"); `cryptography` not in pyproject.toml | WRONG |
| Arch tree: `.presence/<agent>.json` (fleet_presence) | fleet_presence.py:74-76 uses `.heartbeats/`, `.peers/`, `.suspects/` — no `.presence` dir anywhere | WRONG |
| Arch tree: `.clocks/<agent>`, `.bids/`, `.traces/`, `.vectors/`, `.channels-index` | fleet_time.py:75 `.clocks`; fleet_bids, fleet_stigmergy, fleet_delta, fleet_watch.py:47 `.channels-index` | VERIFIED |
| Arch tree omits `.cursors/` (layout section includes it) | chat.py keeps per-channel cursors; fleet_delta.py:28 | STALE (minor inconsistency between the two trees) |
| Quickstart: `init`/`keygen`/`post`/`read`/`wait` with shown flags | chat.py:1769 (init, positional channel), :1879-1880 (keygen, positional agent_id), :1890-1904 (post: --from/--to/--title/--reply/--status/--body/--body-file), :1949-1957 (wait: channel, --as, --timeout) | VERIFIED |
| `AGENT_CHAT_ROOT`, keys in `~/.shingle/keys/` or `$FLEET_KEYS_DIR` | chat.py:60, fleet_identity.py:98-99 | VERIFIED |
| Command reference table (19 commands incl. gossip/react/suggest-role/task/dag/thread/clocks/ops/heartbeat/presence/suspect/gc/mark-ephemeral) | all `add_parser` entries + cmd_* handlers present (chat.py:531-1660, 1769-1957) | VERIFIED |
| E2EE: priv-* key at init, encrypt-before-sign, verify-then-decrypt, tamper fails closed, keyless post refused | chat.py:439,813,913; fleet_e2ee.py:66 PRIV_PREFIX, :91-100 fail-closed RuntimeError | VERIFIED |
| "E2EE (7/7)" / "HMAC v2 (7/7)" counts | behaviors in code (commit 991ac87c, 1ae024df); no test source in tree yields those counts | UNVERIFIED (counts) |
| Anti-entropy: `gossip --repair` recovers byte-identical file + `recovered_from: log.jsonl` | fleet_gossip.py:303,322; gossip parser --repair default True (chat.py:1829+) | VERIFIED |
| Wait regression: irrelevant traffic no longer ends wait | commit 55879913; cmd_wait chat.py:1034 | VERIFIED |
| Bidding: non-winner rejected, winner claims, round archived, trace feeds suggest-role | fleet_bids.py:221 archive_round; cmd_task_bid/bids/claim chat.py:1555-1598 | VERIFIED |
| CRDT merge proven in `fleet_crdt.selftest()` | fleet_crdt.py:222 | VERIFIED |
| Two-agent post/wait/read smoke | tests_smoke_two_agent.py; commit f0e973f0 | VERIFIED |
| Roster: single file at `~/.shingle/roster`, revocation first-class | fleet_roster.py:54 (`/home/toxic/.shingle/roster`, `$FLEET_ROSTER` override) | VERIFIED |
| `_meta.json`, `log.jsonl`, `.ops.jsonl` per channel | chat.py:278; fleet_log, fleet_crdt | VERIFIED |
| "Screened 59 candidates, selected 12, ten implemented" | numbers appear only in README; not in SPEC.md or elsewhere | UNVERIFIED |
| `src/hub/store.js` (agentsync provenance row) | path belongs to the donor repo, not this one; reads as a local path in context | UNVERIFIED (clarity — audit.py FAIL is a false positive) |

Last-20-commits sweep: all 20 recent commits (dag/thread/clocks, CRDT, bidding,
HMAC v2, E2EE, wait fix, gossip, stigmergy, presence, digest, Lamport, ephemeral,
log.jsonl, inotify wait, HMAC/keygen, fleet_addr, README rewrite, smoke test) are
reflected in the README. Nothing recent is omitted. (Older history is upstream
release chores; CHANGELOG.md is the upstream's and covers none of the fleet work —
repo hygiene note, not a README defect.)

## Missing from README

- **`cryptography` prerequisite for priv-* channels** (`pip install cryptography`); README claims stdlib-only, so a fresh user hitting the E2EE section gets a RuntimeError with no prior warning.
- Correct presence storage dirs (`.heartbeats/`, `.peers/`, `.suspects/` instead of the documented `.presence/<agent>.json`).

## Quickstart check

- [x] Commands exist
- [x] Ports/config keys match code (no ports; `AGENT_CHAT_ROOT`, `FLEET_KEYS_DIR` match)
- [x] A fresh user could follow the public-channel quickstart end to end
- [ ] priv-* path: missing `pip install cryptography` prerequisite

## Action taken

- None — report only per task rules. Fixes are bounded (stdlib-only claim,
  presence dir names, "pristine" claim, cryptography prerequisite); no rewrite needed.
