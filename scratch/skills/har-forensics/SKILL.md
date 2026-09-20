# har-forensics

One-shot forensic pipeline for HAR captures (and `.txt` files containing HAR JSON): **ingest → dataframes → chat extraction → topic analysis → report**. Built because the multi-step meta-process (spawn subagent, hand-write parse scripts, base64-pipe them to the bridge, repeat) is annoying as hell.

## When to use

- Someone hands you a HAR file / clipboard-pasted HAR / DevTools export and asks "wtf is being said in these chats" or "what did this session do".
- Any `.har`, `.txt`, or extensionless file containing HAR 1.2 JSON.

## How to run

The files usually live on **awrawr-pc** (the bridge box). Run the driver there via the `awrawr-mcp` bridge:

```bash
cd ~/workspace/skills/awrawr-mcp
B64=$(base64 -w0 ~/workspace/skills/har-forensics/bin/forensics.py)
python3 bin/exec.py "echo $B64 | base64 -d | python3 - /path/to/capture1.txt /path/to/capture2.har --out /home/toxic/analysis-<name>" /home/toxic
```

Or copy the HARs to the cell first and run `bin/forensics.py` directly (needs only stdlib + numpy).

## What it does (stages)

1. **ingest** — SHA-256 dedupes input files (byte-identical dupes are skipped, not re-analyzed). Parses HAR 1.2 → one row per entry: timestamp, method, URL, host, path, status, mime, timings, body sizes. Writes `entries.csv`.
2. **bodies** — pulls request/response body text out of each entry (decodes base64 `content.text` when the HAR says so). Skips bodies over `--max-body-mb` (default 8).
3. **chat-extract** — walks every JSON body recursively and pulls candidate chat messages: any string > 40 chars under a key like `text|content|message|body|snippet`, plus role/sender/chat-id context when nearby. gRPC-web binary bodies fall back to printable-string scraping. Writes `messages.csv` (`started, chat_id, role, service, text`).
4. **analyze** — TF-IDF + k-means++ implemented in pure numpy (no sklearn needed) over message texts → `clusters.csv` (top terms per cluster, sizes, time span). Also flags anomalies: status-0 blocked requests, p99 latencies, giant bodies.
5. **report** — `REPORT.md`: anchor-linked TOC, cluster tables, anomaly alerts, and real message excerpts so you can see wtf was being said.
6. **todo** — `TODO.md`: speculative routes forward, always. Multiple routes (anomaly triage, chat reconstruction, topic followthrough, artifact recovery, skill hardening), each with full checkbox todos grounded in this run's findings.

## Outputs (in `--out`)

- `entries.csv` — every HAR entry as a dataframe row
- `messages.csv` — extracted chat messages
- `clusters.csv` — topic clusters with top terms
- `REPORT.md` — the human-readable deep dive
- `TODO.md` — speculative routes with full todos (always generated)

**Unique output dir per run** (2026-09-14 lesson): two writers, one dir = clobbered
outputs. A rogue duplicate pipeline launched 18:52 wrote into the same `deep/`
as the real run and overwrote `clusters.csv` at 19:02 — the /tmp fratricide
pattern applied to outputs. Always use a timestamped dir:
`--out /home/toxic/analysis-clipboard-20260914/deep-<HHMM>/`, never a bare shared
name when another run might be in flight.

## Flags

- `--out DIR` (required) — output directory
- `--max-body-mb N` — skip bodies larger than N MB (default 8)
- `--min-text-len N` — min chars for a chat-text candidate (default 40)
- `--k K` — k-means clusters (default 8)

## Lessons baked in

- HAR exports pasted into `.txt` files are still just JSON — don't let the extension fool you.
- Portal-audit style captures come in byte-identical pairs (raw + BACKUP) — always hash first.
- Kimi's `ChatService/Chat` is gRPC-web; `ListMessages`/feed endpoints are plain JSON and carry the actual chat text.
- Read-only on inputs. Unique output dir per run. Never shared `/tmp` paths.
- **Race your hot path.** The extraction stage was raced 2026-09-14 (`hft-latency/bin/race.py`, tag `har-extract`): object_hook single-pass **0.30s** won over recursive-walk 0.31s and regex-scan 2.40s, byte-identical output. Slow is a kind of wrong — when latency is too high, race similar-but-different implementations instead of hand-tuning one.
