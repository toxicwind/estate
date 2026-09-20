#!/usr/bin/env python3
"""w8-proof-reel: PNG charts + MP4 reel of the seed findings.
Plan: (1) load offending_tokens.json + seed_list_chat.json; (2) render
tokens.png: top-20 tokens by likelihood ratio, colored by confidence;
(3) render echo.png: echo-chain rate bar (72.8% measured); (4) assemble
reel.mp4 with ffmpeg if present (else deliver PNGs + note); (5) RESULT.json
with sha256 of each proof file.
"""
import json, os, time, hashlib, subprocess, shutil

WORK = os.path.dirname(os.path.abspath(__file__))
SEEDS = "/home/toxic/.shingle/coord/work/seeds"

d = json.load(open(os.path.join(SEEDS, "offending_tokens.json")))
toks = d["offending_tokens"][:20]
turns = json.load(open(os.path.join(SEEDS, "seed_list_chat.json")))
echo_rate = sum(1 for t in turns if t.get("echo_chain")) / max(1, sum(1 for t in turns if t["label"] == -1))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

col = {"high": "#ff5d5d", "medium": "#f5a623", "low": "#3b82f6"}
labels = [(t["token"] if len(t["token"]) < 14 else t["token"][:13] + "…") for t in toks]
lrs = [t["likelihood_ratio"] for t in toks]
cs = [col[t["confidence"]] for t in toks]
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(labels[::-1], lrs[::-1], color=cs[::-1])
ax.set_xlabel("likelihood ratio (pre-onset vs benign)")
ax.set_title("Top-20 offending tokens by measured likelihood ratio")
fig.tight_layout()
p1 = os.path.join(WORK, "tokens.png")
fig.savefig(p1, dpi=110)
plt.close(fig)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["echo-chained", "standalone"], [echo_rate, 1 - echo_rate],
       color=["#ff5d5d", "#3b82f6"])
ax.set_ylim(0, 1)
ax.set_title(f"Storm turns in echo chains: {echo_rate:.1%}")
p2 = os.path.join(WORK, "echo.png")
fig.savefig(p2, dpi=110)
plt.close(fig)

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

proofs = [p1, p2]
mp4 = None
if shutil.which("ffmpeg"):
    mp4 = os.path.join(WORK, "reel.mp4")
    r = subprocess.run(["ffmpeg", "-y", "-framerate", "1", "-i", os.path.join(WORK, "tokens.png"),
                        "-framerate", "1", "-i", os.path.join(WORK, "echo.png"),
                        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0",
                        "-pix_fmt", "yuv420p", mp4],
                       capture_output=True, text=True)
    if r.returncode == 0:
        proofs.append(mp4)
    else:
        mp4 = None

r = {"lane": "w8-proof-reel",
     "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
     "claims": [f"rendered tokens.png + echo.png (echo_rate={echo_rate:.3f})",
                f"mp4 reel: {'built' if mp4 else 'ffmpeg missing, PNGs only'}"],
     "evidence": {"sha256": {os.path.basename(p): sha(p) for p in proofs},
                  "echo_rate": round(echo_rate, 4)},
     "proof_files": [os.path.basename(p) for p in proofs] + ["brief.py"]}
json.dump(r, open(os.path.join(WORK, "RESULT.json"), "w"), indent=1)
print(json.dumps(r, indent=1))
