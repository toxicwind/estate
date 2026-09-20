#!/usr/bin/env python3
"""error_claims — ERROR_CLAIM_CATALOG + classify_error_claim for the stall-slayer lane.

An error string is a CLAIM, not a fact (unreliable-narrator doctrine, AGENTS.md
section 5: "what actually happened outranks what the error says happened"). A
diagnosis that trusts the string can kill healthy work — this module catalogs
the error claims seen on this estate, each with:

  claim_id      stable machine key
  name          human label
  patterns      regexes that match the claim text (case-insensitive)
  usual_reality what direct observation usually shows instead
  verify        the executable check that settles it (copy-paste, run)
  action        what to do once the check confirms the reality
  severity      mislead | transient | genuine
                  mislead   = the string routinely lies; verify BEFORE acting
                  transient = real but self-healing; retry, don't escalate
                  genuine   = take the error at face value; act on it

Grounded claims come from real 2026-09-20 estate incidents:

  disk-full          pip "No space left on device" with 2% disk used
  token-dead-probe   HF v1 whoami 401s even for VALID tokens (void verdicts)
  exec-hang          bridge exec has fail-fast ceilings; stalls are unreaped
                     rows, not hung calls
  ledger-stall       oracle ledger gap of 21,050s during a healthy quiet market
  meter-limit        subscription "100%/limit hit" language vs actual tool use
  spawn-lock-timeout subagent reservation "lock timeout" under swarm load
  bridge-401         ~3-minute transient WS/HTTPS 401 window, self-recovered
  conn-refused       listener bound to the wrong iface (tailscale vs loopback)
  provider-rate-limit 429 / connector_rate_limited — provider-side throttle
  quota-402          402 insufficient-credit — genuine billing wall
  eaddrinuse         two holders on one port; pick the canonical holder

Consumers:
  - hatch/bin/agent-reaper --classify-errors   (harvest -> classify -> report,
    optional --fleet-notes for high-confidence misleads)
  - hatch/bin/progress-watchdog cond()         (one-line claim annotation on
    every alert, appended to text_new — dedup sig untouched)
  - projects/ops/stall-detect/queries.sql Q8/Q9/Q10 + README runbook

Zero third-party deps. Pure stdlib so the watchdog and reaper can import it
without a venv.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys

CATALOG_VERSION = "1.0.0"

ERROR_CLAIM_CATALOG = [
    {
        "claim_id": "disk-full",
        "name": "disk full",
        "patterns": [
            r"no space left on device",
            r"\bdisk full\b",
            r"\benospc\b",
        ],
        "confidence": 0.9,
        "usual_reality": (
            "Transient or mount-specific. 2026-09-20: pip failed with "
            "'No space left on device' while df showed 2% used."
        ),
        "verify": "df -h / && df -i / && df -h /tmp",
        "action": (
            "Trust df, not the string. If df shows headroom, retry the "
            "operation. If one mount is genuinely full, clear that mount — "
            "never treat a full /tmp as a full /."
        ),
        "severity": "mislead",
    },
    {
        "claim_id": "token-dead-probe",
        "name": "token dead (probe endpoint)",
        "patterns": [
            r"token[s]?\s+(are\s+|is\s+)?(invalid|expired|dead|revoked|bad)",
            r"whoami.*\b401\b",
            r"\b401\b.*whoami",
        ],
        "confidence": 0.9,
        "usual_reality": (
            "The HF v1 whoami probe 401s even for VALID tokens (void "
            "verdicts, 2026-09-20). A probe refusal is not a token verdict."
        ),
        "verify": (
            "Validate against the authoritative endpoint (a real API call), "
            "never the probe alone."
        ),
        "action": (
            "Never declare a token dead from a probe endpoint. Confirm with "
            "a real request first, then treat as credential hygiene."
        ),
        "severity": "mislead",
    },
    {
        "claim_id": "exec-hang",
        "name": "command hung / timed out",
        "patterns": [
            r"(command|exec|call|tool).{0,40}(timed?\s*out|hung|stuck|hangs)",
            r"(timed?\s*out|hung|stuck).{0,40}(command|exec|call|tool)",
        ],
        "confidence": 0.75,
        "usual_reality": (
            "Bridge exec has fail-fast ceilings (120s WS / 180s HTTP). Most "
            "'hangs' are unreaped rows or finished work whose delivery was "
            "missed — not a live process stuck on a call."
        ),
        "verify": "ps aux | grep <cmd> ; check the output file / mailbox for the result",
        "action": (
            "If the process is alive, read its log. If it is dead with no "
            "output, the row is the stall — re-issue the work, don't chase "
            "a hang."
        ),
        "severity": "mislead",
    },
    {
        "claim_id": "ledger-stall",
        "name": "ledger / queue stalled",
        "patterns": [
            r"ledger.{0,30}(stalled|hasn.?t grown|not grown|no growth)",
            r"stalled\s+\d+\s*seconds?",
            r"queue.{0,30}(stalled|not draining)",
        ],
        "confidence": 0.8,
        "usual_reality": (
            "Ledger age cannot distinguish a dead loop from a quiet market. "
            "2026-09-20: a 21,050s gap was a healthy quiet market, not a "
            "dead loop. Ledger-age alerts are false-green machinery."
        ),
        "verify": "pgrep -af <loop>; ls <intake-dir> for pending files",
        "action": (
            "Replace ledger-age alerts with process facts: is the loop "
            "alive, is there pending work. Age alone is not a finding."
        ),
        "severity": "mislead",
    },
    {
        "claim_id": "meter-limit",
        "name": "subscription / meter limit",
        "patterns": [
            r"(subscription|meter|allowance).{0,40}(100%|limit|exhausted|hit)",
            r"(100%|limit hit|quota exceeded).{0,40}(subscription|meter|token)",
        ],
        "confidence": 0.9,
        "usual_reality": (
            "Meter language is narrator noise. Only an actual tool refusal "
            "on quota grounds counts as a limit."
        ),
        "verify": "Attempt the tool call. A refusal is the only real limit.",
        "action": "Ignore meter language. Keep working.",
        "severity": "mislead",
    },
    {
        "claim_id": "spawn-lock-timeout",
        "name": "subagent spawn lock timeout",
        "patterns": [
            r"subagent.{0,40}(lock|reservation).{0,20}(timeout|failed)",
            r"spawn reservation failed before spawn row persistence",
            r"lock timeout.{0,40}(spawn|subagent)",
        ],
        "confidence": 0.9,
        "usual_reality": (
            "DB lock contention under swarm load (2026-09-20: dozens of "
            "workers). No child ever ran; nothing is orphaned."
        ),
        "verify": (
            "SELECT status FROM agent.agents WHERE agent_id='<id>'; "
            "confirm no spawn row for the child."
        ),
        "action": (
            "The parent retries the spawn. Do NOT close anything — there "
            "is nothing to close. Do not reap 'errored' spawn rows."
        ),
        "severity": "transient",
    },
    {
        "claim_id": "bridge-401",
        "name": "bridge 401 unauthorized",
        "patterns": [
            r"\b401\b.{0,40}(exec|ws|bridge|wss)",
            r"(exec|ws|bridge|wss).{0,40}\b401\b",
            r"unauthorized.{0,40}(bridge|exec|ws)",
        ],
        "confidence": 0.8,
        "usual_reality": (
            "Usually transient: a ~3-minute broker/yote token-skew window "
            "on 2026-09-20 self-recovered with zero intervention. Don't "
            "message Chris about a 401 until it survives a retry."
        ),
        "verify": (
            "Wait 2-3 minutes, retry. Compare token fingerprints on both "
            "sides if it persists."
        ),
        "action": (
            "Retry after 2 minutes before escalating. Escalate to Chris "
            "(token mint via vault page) only if it persists >5 minutes."
        ),
        "severity": "transient",
    },
    {
        "claim_id": "conn-refused",
        "name": "connection refused",
        "patterns": [
            r"connection refused",
            r"\beconnrefused\b",
            r"no route to host",
        ],
        "confidence": 0.85,
        "usual_reality": (
            "Usually the listener binds a different interface than probed "
            "(tailscale vs loopback) or the port moved in the serve map "
            "(e.g. 8379 -> 25204), not an outage."
        ),
        "verify": (
            "ss -ltnp | grep <port>; tailscale serve status; check the "
            "serve map before declaring an outage."
        ),
        "action": (
            "Verify the listener on the right interface and port first. "
            "Only then treat as a backend outage."
        ),
        "severity": "genuine",
    },
    {
        "claim_id": "provider-rate-limit",
        "name": "provider rate limit (429)",
        "patterns": [
            r"\b429\b",
            r"rate.?limit(ed)?",
            r"too many requests",
            r"connector_rate_limited",
            r"provider_rate_limit_stop",
        ],
        "confidence": 0.9,
        "usual_reality": (
            "Genuine provider-side throttle. Retrying, delegating, or "
            "sleeping around it risks the account."
        ),
        "verify": "Read the 429 response headers/body for retry-after.",
        "action": (
            "HARD STOP for that provider scope this attempt: report partial "
            "progress; no sleep-retry, no delegation around it, no lower "
            "rate re-entry. The parent or a later run may reorganize."
        ),
        "severity": "genuine",
    },
    {
        "claim_id": "quota-402",
        "name": "provider quota / billing (402)",
        "patterns": [
            r"\b402\b",
            r"payment required",
            r"insufficient.{0,30}(quota|credit|balance|funds)",
        ],
        "confidence": 0.9,
        "usual_reality": "Genuine billing/quota wall on that provider lane.",
        "verify": "Provider dashboard / usage API.",
        "action": (
            "Route through a different provider lane. Flag to Chris; don't "
            "hammer the wall."
        ),
        "severity": "genuine",
    },
    {
        "claim_id": "eaddrinuse",
        "name": "port already in use",
        "patterns": [
            r"\beaddrinuse\b",
            r"address already in use",
            r"port.{0,20}already.{0,20}in use",
        ],
        "confidence": 0.9,
        "usual_reality": (
            "Two holders on one port. Usually one is stale state (e.g. "
            "pitchfork state.toml tracking a dead pid) or a silent "
            "port-increment moved a service."
        ),
        "verify": (
            "ss -ltnp | grep <port>; compare the pid against the "
            "supervisor's tracked pid."
        ),
        "action": (
            "Pick the canonical holder (the supervisor's tracked process), "
            "remove the loser. Never kill loops — one verified holder, "
            "fail-fast guard only."
        ),
        "severity": "genuine",
    },
]


def classify_error_claim(text):
    """Classify an error-ish string against the claim catalog.

    Returns a list of match dicts, best confidence first. Each dict:
      claim_id, name, severity, confidence, matched, usual_reality,
      verify, action.
    Unknown text returns [] (not a claim we know — investigate raw).
    """
    if not text or not str(text).strip():
        return []
    text = str(text)
    hits = []
    for entry in ERROR_CLAIM_CATALOG:
        for pat in entry["patterns"]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                hits.append(
                    {
                        "claim_id": entry["claim_id"],
                        "name": entry["name"],
                        "severity": entry["severity"],
                        "confidence": entry.get("confidence", 0.8),
                        "matched": m.group(0)[:80],
                        "usual_reality": entry["usual_reality"],
                        "verify": entry["verify"],
                        "action": entry["action"],
                    }
                )
                break  # one hit per catalog entry
    hits.sort(key=lambda h: -h["confidence"])
    return hits


def annotate(text, min_confidence=0.8):
    """One-line claim annotation for alert text. '' when no confident match."""
    hits = [h for h in classify_error_claim(text) if h["confidence"] >= min_confidence]
    if not hits:
        return ""
    h = hits[0]
    return (
        "claim-check [%s/%s, conf %.2f]: %s — verify: %s"
        % (h["claim_id"], h["severity"], h["confidence"], h["usual_reality"][:140], h["verify"][:160])
    )


def _selftest():
    cases = [
        ("OSError: [Errno 28] No space left on device", "disk-full"),
        ("pip failed: disk full writing wheel", "disk-full"),
        ("HF token is invalid (whoami returned 401)", "token-dead-probe"),
        ("whoami probe: 401 unauthorized", "token-dead-probe"),
        ("exec call timed out after 120s, command hung", "exec-hang"),
        ("oracle ledger stalled 21050 seconds, no growth", "ledger-stall"),
        ("subscription meter at 100%, limit hit", "meter-limit"),
        ("subagent reservation failed before spawn row persistence (lock timeout)", "spawn-lock-timeout"),
        ("WS exec 401 unauthorized on /exec-ws", "bridge-401"),
        ("curl: (7) Failed to connect: Connection refused on 127.0.0.1:8379", "conn-refused"),
        ("provider returned 429 rate_limited, retry-after 60", "provider-rate-limit"),
        ("connector_rate_limited terminal_for_attempt", "provider-rate-limit"),
        ("402 Payment Required: insufficient credit balance", "quota-402"),
        ("bind(25109) = -1 EADDRINUSE", "eaddrinuse"),
        ("Address already in use on port 25126", "eaddrinuse"),
    ]
    for text, want in cases:
        hits = classify_error_claim(text)
        assert hits, "no classification for: %r" % text
        assert hits[0]["claim_id"] == want, "want %s got %s for %r" % (
            want, hits[0]["claim_id"], text)
    # unknown text -> no hits
    assert classify_error_claim("sunshine and rainbows, all green") == []
    assert classify_error_claim("") == []
    assert classify_error_claim(None) == []
    # false-positive resistance: prose about fixing errors is not an error claim
    assert classify_error_claim(
        "fixed the error handling in the retry path") == []
    # annotate() returns '' for clean text, a note for a claim
    assert annotate("all green") == ""
    assert "disk-full" in annotate("No space left on device")
    print("error_claims selftest OK (%d catalog cases)" % len(cases))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Error-claim catalog + classifier")
    ap.add_argument("--catalog", action="store_true",
                    help="Print ERROR_CLAIM_CATALOG as JSON.")
    ap.add_argument("--classify", action="store_true",
                    help="Read JSON array of {id, source, error_text} from stdin or file; print classified JSON.")
    ap.add_argument("--selftest", action="store_true",
                    help="Run built-in catalog assertions.")
    ap.add_argument("file", nargs="?",
                    help="Input file for --classify (default: stdin).")
    args = ap.parse_args(argv)

    if args.selftest:
        _selftest()
        return 0
    if args.catalog:
        json.dump({"version": CATALOG_VERSION, "catalog": ERROR_CLAIM_CATALOG},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.classify:
        src = open(args.file) if args.file else sys.stdin
        with src:
            candidates = json.load(src)
        out = []
        for c in candidates:
            text = c.get("error_text") or ""
            out.append({
                "id": c.get("id"),
                "source": c.get("source"),
                "error_text": text[:500],
                "claims": classify_error_claim(text),
            })
        json.dump(out, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
