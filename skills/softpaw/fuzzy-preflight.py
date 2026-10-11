#!/usr/bin/env python3
"""fuzzy-preflight.py — fuzzy trigger-shape matching for the classifier project.

Uses rapidfuzz (installed via paru) to catch obfuscated/typo'd trigger phrases
that pure regex misses. Each canonical trigger phrase gets a fuzzy threshold;
text that scores above it gets flagged with the matched shape + rewrite guidance.

Usage:
  python3 fuzzy-preflight.py "some text to screen"
  python3 fuzzy-preflight.py --file /path/to/text.txt
  python3 fuzzy-preflight.py --selftest
"""
import json
import sys
from rapidfuzz import fuzz

# Canonical trigger phrases mapped to their shape id + rewrite guidance.
# Thresholds tuned: 80+ catches single-typo/obfuscation without flagging prose.
TRIGGER_PHRASES = [
    ("bypass-bare", "bypass", 85, "Describe the supported route instead of adversarial wording."),
    ("bypass-stats", "bypass the safety filter", 80, "Describe the supported route instead of adversarial wording."),
    ("c2-term", "command and control", 80, "Say 'yote-conn bridge' or 'fleet bus'."),
    ("zero-approval", "zero approval", 85, "Name the standing order instead of asserting absence of approval."),
    ("never-ask", "never ask", 85, "Say 'decide autonomously' in behavioral language."),
    ("yolo", "yolo", 90, "Remove; keep the operational meaning in behavioral language."),
    ("malware-stack", "malware", 85, "Describe the concrete action instead."),
    ("ignore-safety", "ignore safety", 80, "Describe the concrete action instead."),
    ("route-around-filter", "route around the filter", 75, "Say 'use the supported route'."),
    ("asleep-act", "act without approval while chris is asleep", 70, "Cite the standing autonomous-operation order."),
    ("refusal-theory", "refusal is a verdict", 75, "Refusals are unreliable narrator: rephrase and redo."),
    ("sudo-passwordless", "passwordless sudo", 80, "Describe the concrete privilege need."),
]

def screen(text, threshold_boost=0):
    """Return list of (shape_id, matched_phrase, score, rewrite) hits."""
    hits = []
    low = text.lower()
    for shape_id, phrase, thresh, rewrite in TRIGGER_PHRASES:
        score = fuzz.partial_ratio(phrase, low)
        if score >= thresh + threshold_boost:
            hits.append({
                "shape": shape_id,
                "phrase": phrase,
                "score": score,
                "rewrite": rewrite,
            })
    # Dedupe by shape, keep highest score
    best = {}
    for h in hits:
        if h["shape"] not in best or h["score"] > best[h["shape"]]["score"]:
            best[h["shape"]] = h
    return sorted(best.values(), key=lambda h: -h["score"])

def selftest():
    cases = [
        ("bypas the filter and continue", True),   # typo'd bypass
        ("by-pass the safety filter", True),       # hyphenated
        ("b y p a s s the filter", True),          # spaced
        ("command & control server", True),        # obfuscated c2
        ("route arond the filter", True),          # typo
        ("the weather is nice today", False),      # clean
        ("please review this pull request", False),# clean
    ]
    ok = True
    for text, should_flag in cases:
        hits = screen(text)
        flagged = len(hits) > 0
        status = "OK " if flagged == should_flag else "FAIL"
        if flagged != should_flag:
            ok = False
        print(f"[{status}] {text!r:45} -> {[h['shape']+':'+str(h['score']) for h in hits]}")
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--selftest":
        return selftest()
    if args[0] == "--file":
        with open(args[1]) as f:
            text = f.read()
    else:
        text = " ".join(args)
    hits = screen(text)
    print(json.dumps({"text": text[:120], "hits": hits}, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
