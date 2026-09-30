#!/usr/bin/env python3
"""Transfer a file to yote over the bridge connector in base64 chunks."""
import argparse, base64, hashlib, json, os, shlex, sys, urllib.request

CONN = "http://127.0.0.1:18301/exec"


def parse_args():
    p = argparse.ArgumentParser(
        description="Transfer a file to yote over the bridge connector in "
                    "base64 chunks, with SHA-256 verification.")
    p.add_argument("src", help="local source file")
    p.add_argument("dst", help="remote destination path on yote")
    p.add_argument("--chunk", type=int, default=2400,
                   help="base64 chars per exec call (default 2400)")
    a = p.parse_args()
    if not os.path.isfile(a.src):
        p.error(f"src not found: {a.src}")
    return a

def yote_exec(cmd, timeout=60):
    req = urllib.request.Request(CONN, data=json.dumps(
        {"cmd": cmd, "timeout": timeout}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout + 30) as r:
        d = json.loads(r.read())
    if d.get("code") != 0:
        raise RuntimeError(f"yote cmd failed: {d.get('stdout','')[:500]} {d.get('stderr','')[:500]}")
    return d.get("stdout", "")

def main():
    a = parse_args()
    SRC, DST, CHUNK = a.src, a.dst, a.chunk
    qdst = shlex.quote(DST)
    data = open(SRC, "rb").read()
    b64 = base64.b64encode(data).decode()
    print(f"transferring {len(data)} bytes in {len(b64)//CHUNK + 1} chunks", flush=True)

    yote_exec(f"rm -f {qdst}.b64 && touch {qdst}.b64")
    for i in range(0, len(b64), CHUNK):
        piece = b64[i:i + CHUNK]
        yote_exec(f"printf '%s' '{piece}' >> {qdst}.b64")
        if (i // CHUNK + 1) % 25 == 0:
            print(f"  chunk {i // CHUNK + 1}...", flush=True)

    out = yote_exec(f"base64 -d {qdst}.b64 > {qdst} && sha256sum {qdst} | cut -d' ' -f1 && rm -f {qdst}.b64")
    remote_sha = out.strip().split("\n")[-1].strip()
    local_sha = hashlib.sha256(data).hexdigest()
    print(f"local  {local_sha[:16]}\nremote {remote_sha[:16]}", flush=True)
    if remote_sha != local_sha:
        raise SystemExit("SHA MISMATCH - transfer corrupt")
    print("TRANSFER_OK", flush=True)


if __name__ == "__main__":
    try:
        from bridge_sem import bridge_slot
    except ImportError:
        from contextlib import nullcontext as bridge_slot
    with bridge_slot():
        main()
