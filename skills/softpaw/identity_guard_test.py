#!/usr/bin/env python3
"""
identity_guard_test.py — Softpaw rewriter line-by-line helper with Llama Guard 4
integration (via meta-llama/PurpleLlama, cloned into softpaw skill).

Pipeline per User 2026-10-05:
  1. Read IDENTITY.md, split into sentences (line-by-line).
  2. Run each sentence through the softpaw preflight (triggers.json).
  3. Test each sentence with the guard model (Llama Guard 4 prompt format,
     served by the herd `classify` model since HF weights are gated and
     HF auth on this box is dead — all .secrets tokens invalid).
  4. Then test the whole doc in overlapping sliding-window chunks
     ("weird chunked way"): window=5 sentences, stride=2, so every sentence
     is seen in 2-3 different contexts.

Usage:
  python3 identity_guard_test.py [--sentences] [--chunks] [--all]
  Defaults to --all.
"""

import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
# IDENTITY.md lives at home root on whichever box runs this.
_IDENTITY_CANDIDATES = [
    "/home/toxic/IDENTITY.md",
    "/home/hatch/IDENTITY.md",
    os.path.join(HERE, "IDENTITY.md"),
]
IDENTITY = next((p for p in _IDENTITY_CANDIDATES if os.path.exists(p)),
                _IDENTITY_CANDIDATES[0])
TRIGGERS = os.path.join(HERE, "triggers.json")
REPORT = os.path.join(HERE, "reports", "identity-guard-report.json")
HERD_URL = "http://localhost:25100/v1/chat/completions"
GUARD_MODEL = "classify"  # herd alias -> Gemma 4 12B 96K

# Llama Guard 4 hazard taxonomy (S1-S14), from PurpleLlama Llama-Guard4/12B/MODEL_CARD.md
CATEGORIES = """<BEGIN UNSAFE CONTENT CATEGORIES>
S1: Violent Crimes. Responses that enable, encourage, or endorse violent crimes.
S2: Non-Violent Crimes. Responses that enable non-violent crimes (fraud, theft, hacking, etc).
S3: Sex-Related Crimes. Responses enabling sex trafficking, assault, harassment.
S4: Child Sexual Exploitation. Any sexual content involving children.
S5: Defamation. Verifiably false statements injuring a living person's reputation.
S6: Specialized Advice. Financial, medical, or legal advice; dangerous activities described as safe.
S7: Privacy. Non-public personal information.
S8: Intellectual Property. Copyrighted text beyond fair use.
S9: Indiscriminate Weapons. Chemical, biological, radiological, nuclear weapons.
S10: Hate. Hateful content targeting protected characteristics.
S11: Suicide & Self-Harm. Encouraging or enabling self-harm.
S12: Sexual Content. Erotic sexual content.
S13: Elections. False claims about elections/voting.
S14: Code Interpreter Abuse. Malicious code execution instructions.
<END UNSAFE CONTENT CATEGORIES>"""

GUARD_TEMPLATE = """Task: Check if there is unsafe content in 'User' messages in conversations according to our safety policy with the below categories.

{CATEGORIES}

<BEGIN CONVERSATION>

User: {text}

<END CONVERSATION>

Provide your safety assessment for ONLY the User message above:
- First line must read 'safe' or 'unsafe'.
- If unsafe, a second line must include a comma-separated list of violated categories (e.g. S1, S10)."""


def load_triggers():
    with open(TRIGGERS) as f:
        data = json.load(f)
    shapes = []
    for s in data.get("shapes", []):
        for p in s.get("patterns", []):
            flags = re.IGNORECASE if "i" in p.get("flags", "") else 0
            shapes.append((s["id"], re.compile(p["source"], flags), s.get("rewrite", "")))
    return shapes


def preflight(text, shapes):
    """Return list of (shape_id, rewrite) hits from softpaw triggers."""
    hits = []
    for sid, pat, rewrite in shapes:
        if pat.search(text):
            hits.append((sid, rewrite))
    return hits


def guard_check(text):
    """Ask the guard model (Llama Guard 4 format) via herd. Returns (verdict, detail)."""
    prompt = GUARD_TEMPLATE.format(CATEGORIES=CATEGORIES, text=text[:2000])
    body = json.dumps({
        "model": GUARD_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(HERD_URL, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.load(r)
        out = resp["choices"][0]["message"]["content"].strip()
        first = out.split("\n")[0].strip().lower()
        verdict = "unsafe" if first.startswith("unsafe") else "safe"
        return verdict, out
    except Exception as e:
        return "error", str(e)[:120]


def split_sentences(text):
    # Keep it simple: split on sentence boundaries, drop empties.
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def sliding_chunks(sentences, window=5, stride=2):
    chunks = []
    i = 0
    while i < len(sentences):
        chunks.append(sentences[i:i + window])
        if i + window >= len(sentences):
            break
        i += stride
    return chunks


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"
    with open(IDENTITY) as f:
        text = f.read()
    shapes = load_triggers()
    sentences = split_sentences(text)
    print(f"IDENTITY.md: {len(sentences)} sentences, {len(shapes)} trigger patterns loaded.")

    results = {"sentences": [], "chunks": []}

    if mode in ("--sentences", "--all"):
        print("\n=== SENTENCE BY SENTENCE ===")
        for i, s in enumerate(sentences):
            hits = preflight(s, shapes)
            verdict, detail = guard_check(s)
            rec = {"i": i, "text": s[:80], "preflight_hits": [h[0] for h in hits],
                   "guard": verdict, "guard_detail": detail.split("\n")[0][:60]}
            results["sentences"].append(rec)
            flag = ""
            if hits or verdict == "unsafe":
                flag = f"  <-- PREFLIGHT:{[h[0] for h in hits]} GUARD:{verdict}"
            print(f"[{i:3d}] {verdict:6s} {s[:70]}{flag}")

    if mode in ("--chunks", "--all"):
        print("\n=== CHUNKED (window=5, stride=2) ===")
        for ci, chunk in enumerate(sliding_chunks(sentences)):
            ctext = " ".join(chunk)
            hits = preflight(ctext, shapes)
            verdict, detail = guard_check(ctext)
            rec = {"chunk": ci, "n_sentences": len(chunk),
                   "preflight_hits": [h[0] for h in hits],
                   "guard": verdict, "guard_detail": detail.split("\n")[0][:60]}
            results["chunks"].append(rec)
            flag = ""
            if hits or verdict == "unsafe":
                flag = f"  <-- PREFLIGHT:{[h[0] for h in hits]} GUARD:{verdict}"
            print(f"(chunk {ci:2d}, {len(chunk)} sents) {verdict:6s}{flag}")

    # Summary
    bad_s = [r for r in results["sentences"] if r["preflight_hits"] or r["guard"] == "unsafe"]
    bad_c = [r for r in results["chunks"] if r["preflight_hits"] or r["guard"] == "unsafe"]
    print(f"\n=== SUMMARY: {len(bad_s)} flagged sentences, {len(bad_c)} flagged chunks ===")
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as f:
        json.dump(results, f, indent=1)
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
