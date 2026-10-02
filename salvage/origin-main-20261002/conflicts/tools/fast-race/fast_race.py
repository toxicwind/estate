#!/usr/bin/env python3
"""fast-race: HFT-style inference racing for the `fast` alias (exaone-1.2b-iq4xs).

Doctrine borrowed from shingle-workspace/squawk-hft-latency.md (non-trading HFT):
  1. Hot persistent connections  - one keep-alive HTTPConnection per lane, dial once.
  2. Redundant raced lanes        - primary :25122 (pitchfork-supervised) vs
                                   herd dynamic slot :25001 (best-effort, auto-
                                   discovered). First valid wins.
  3. Fail-fast ceilings          - a lane that misses its TTFT deadline loses;
                                   fallback lane(s) planned BEFORE the primary.
  4. Measure every hop           - JSONL race log + P50/P95/P99 bench tables.

Usage:
  fast_race.py "prompt"                 single request, primary with fail-fast fallback
  fast_race.py --race "prompt"          fire all healthy lanes, first valid wins
  fast_race.py --bench [--reps N]       N reps x (hot vs cold) + P50/P95/P99 per lane
  fast_race.py --lanes 127.0.0.1:25122  override lane list
  fast_race.py --ceiling 2.0            TTFT fail-fast ceiling in seconds
"""
import argparse
import concurrent.futures as cf
import http.client
import json
import os
import sys
import time

DEFAULT_LANES = ["127.0.0.1:25122", "127.0.0.1:25001"]
LOG_PATH = "/home/toxic/sovereign/data/fast-race.log"
STALE_CONN_ERRORS = (http.client.RemoteDisconnected, BrokenPipeError,
                     ConnectionResetError)


class Lane:
    """One inference lane with a hot persistent connection (warm standby)."""

    def __init__(self, addr):
        self.addr = addr
        host, port = addr.rsplit(":", 1)
        self.host, self.port = host, int(port)
        self.conn = None
        self.dials = 0

    def dial(self, timeout=5.0):
        if self.conn is not None and self.conn.sock is not None:
            return
        self.drop()
        t0 = time.perf_counter()
        self.conn = http.client.HTTPConnection(self.host, self.port, timeout=timeout)
        self.conn.connect()
        self.dials += 1
        return (time.perf_counter() - t0) * 1000.0

    def drop(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.conn = None

    def healthy(self):
        try:
            self.dial(timeout=2.0)
            self.conn.request("GET", "/health")
            r = self.conn.getresponse()
            ok = r.status == 200
            r.read()
            return ok
        except Exception:
            self.drop()
            return False

    def complete_stream(self, payload, ttft_ceiling):
        """Stream one completion. One silent re-dial on stale keep-alive;
        TTFT-ceiling misses are NOT retried (fail fast — lane loses)."""
        try:
            return self._once(payload, ttft_ceiling)
        except STALE_CONN_ERRORS:
            self.drop()
            return self._once(payload, ttft_ceiling)

    def _once(self, payload, ttft_ceiling):
        self.dial()
        body = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        t_send = time.perf_counter()
        deadline = t_send + ttft_ceiling
        self.conn.sock.settimeout(ttft_ceiling)
        self.conn.request("POST", "/v1/chat/completions", body=body, headers=headers)
        resp = self.conn.getresponse()
        if resp.status != 200:
            resp.read()
            raise RuntimeError("http %d" % resp.status)
        ttft_ms = None
        tokens = 0
        text_parts = []
        usage = {}
        buf = b""
        done = False
        try:
            while not done:
                remaining = deadline - time.perf_counter()
                if remaining <= 0 and ttft_ms is None:
                    raise TimeoutError("ttft ceiling %.2fs missed" % ttft_ceiling)
                self.conn.sock.settimeout(max(0.05, remaining if ttft_ms is None else 30.0))
                try:
                    piece = resp.read(4096)
                except Exception as e:
                    raise TimeoutError("read stall: %s" % e)
                if not piece:
                    break
                buf += piece
                while b"\n" in buf:
                    raw, buf = buf.split(b"\n", 1)
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        done = True
                        break
                    try:
                        chunk = json.loads(data)
                    except Exception:
                        continue
                    if ttft_ms is None:
                        ttft_ms = (time.perf_counter() - t_send) * 1000.0
                    for choice in chunk.get("choices", []):
                        delta = choice.get("delta", {})
                        if delta.get("content"):
                            tokens += 1
                            text_parts.append(delta["content"])
                    if chunk.get("usage"):
                        usage = chunk["usage"]
        except Exception:
            self.drop()
            raise
        # drain the tail so the keep-alive connection stays reusable
        try:
            self.conn.sock.settimeout(5.0)
            resp.read()
        except Exception:
            pass
        total_ms = (time.perf_counter() - t_send) * 1000.0
        if ttft_ms is None:
            raise RuntimeError("no tokens streamed")
        comp_tokens = usage.get("completion_tokens", tokens)
        return {
            "lane": self.addr,
            "ttft_ms": round(ttft_ms, 1),
            "total_ms": round(total_ms, 1),
            "tokens": comp_tokens,
            "gen_tps": round(comp_tokens / max(total_ms - ttft_ms, 1) * 1000.0, 1),
            "text": "".join(text_parts),
        }


def log_race(entry):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def discover_lanes(addrs):
    lanes = [Lane(a) for a in addrs]
    return [l for l in lanes if l.healthy()]


def payload_for(prompt, max_tokens=128):
    return {
        "model": "fast",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.6,
        "stream": True,
        "stream_options": {"include_usage": True},
    }


def run_single(prompt, lanes, ceiling, max_tokens=128):
    """Primary with fail-fast fallback (fallback planned before primary)."""
    primary, backups = lanes[0], lanes[1:]
    entry = {"ts": time.time(), "mode": "single", "prompt_chars": len(prompt),
             "ceiling_s": ceiling, "attempts": []}
    try:
        res = primary.complete_stream(payload_for(prompt, max_tokens), ceiling)
        res["path"] = "primary"
        entry["attempts"].append({"lane": primary.addr, "ok": True,
                                  "ttft_ms": res["ttft_ms"], "gen_tps": res["gen_tps"]})
        entry["winner"] = primary.addr
        log_race(entry)
        return res
    except Exception as e:
        entry["attempts"].append({"lane": primary.addr, "ok": False, "error": str(e)[:120]})
        if not backups:
            entry["winner"] = None
            log_race(entry)
            raise
        with cf.ThreadPoolExecutor(max_workers=len(backups)) as ex:
            futs = {ex.submit(b.complete_stream, payload_for(prompt, max_tokens), ceiling): b
                    for b in backups}
            for fut in cf.as_completed(futs):
                lane = futs[fut]
                try:
                    res = fut.result()
                    res["path"] = "fallback-race"
                    entry["attempts"].append({"lane": lane.addr, "ok": True,
                                              "ttft_ms": res["ttft_ms"], "gen_tps": res["gen_tps"]})
                    entry["winner"] = lane.addr
                    log_race(entry)
                    return res
                except Exception as be:
                    entry["attempts"].append({"lane": lane.addr, "ok": False,
                                              "error": str(be)[:120]})
        entry["winner"] = None
        log_race(entry)
        raise RuntimeError("all lanes failed")


def run_race(prompt, lanes, ceiling, max_tokens=128):
    """Full HFT: fire every healthy lane, first valid wins."""
    entry = {"ts": time.time(), "mode": "race", "prompt_chars": len(prompt),
             "ceiling_s": ceiling, "attempts": []}
    with cf.ThreadPoolExecutor(max_workers=len(lanes)) as ex:
        futs = {ex.submit(l.complete_stream, payload_for(prompt, max_tokens), ceiling): l
                for l in lanes}
        for fut in cf.as_completed(futs):
            lane = futs[fut]
            try:
                res = fut.result()
                res["path"] = "race"
                res["winner_lane"] = lane.addr
                for l2 in lanes:
                    if l2 is not lane:
                        entry["attempts"].append({"lane": l2.addr, "ok": False,
                                                  "error": "lost race"})
                entry["attempts"].append({"lane": lane.addr, "ok": True,
                                          "ttft_ms": res["ttft_ms"], "gen_tps": res["gen_tps"]})
                entry["winner"] = lane.addr
                log_race(entry)
                return res
            except Exception as e:
                entry["attempts"].append({"lane": lane.addr, "ok": False,
                                          "error": str(e)[:120]})
    entry["winner"] = None
    log_race(entry)
    raise RuntimeError("all lanes failed")


def pct(data, p):
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def run_bench(lanes, reps, ceiling):
    prompt = "Explain in three sentences how transformer attention works."
    print("warmup (3, not counted)...", file=sys.stderr)
    for _ in range(3):
        try:
            lanes[0].complete_stream(payload_for(prompt), ceiling)
        except Exception:
            pass
    results = {}
    for lane in lanes:
        ttfts, tps = [], []
        for _ in range(reps):
            try:
                r = lane.complete_stream(payload_for(prompt), ceiling)
                ttfts.append(r["ttft_ms"])
                tps.append(r["gen_tps"])
            except Exception as e:
                print("rep failed on %s: %s" % (lane.addr, e), file=sys.stderr)
        results[lane.addr] = (ttfts, tps)
    cold_ttfts = []
    for _ in range(reps):
        l = Lane(lanes[0].addr)
        try:
            r = l.complete_stream(payload_for(prompt), ceiling)
            cold_ttfts.append(r["ttft_ms"])
        except Exception:
            pass
        l.drop()
    print("")
    print("lane                 TTFT p50 / p95 / p99 (ms)      gen_tps p50")
    for addr, (ttfts, tps) in results.items():
        if not ttfts:
            print("%-20s no successful runs" % addr)
            continue
        print("%-20s %7.1f / %7.1f / %7.1f ms        %7.1f tok/s   (n=%d)" % (
            addr, pct(ttfts, 50), pct(ttfts, 95), pct(ttfts, 99),
            pct(tps, 50), len(ttfts)))
    if cold_ttfts and results[lanes[0].addr][0]:
        hot_p50 = pct(results[lanes[0].addr][0], 50)
        cold_p50 = pct(cold_ttfts, 50)
        print("")
        print("hot-vs-cold TTFT p50 on %s: hot %.1f ms vs cold %.1f ms (delta %+.1f ms)" % (
            lanes[0].addr, hot_p50, cold_p50, cold_p50 - hot_p50))


def main():
    ap = argparse.ArgumentParser(description="HFT-style racing client for the fast alias")
    ap.add_argument("prompt", nargs="?", default="In one sentence, why is the sky blue?")
    ap.add_argument("--race", action="store_true",
                    help="fire all healthy lanes, first valid wins")
    ap.add_argument("--bench", action="store_true",
                    help="benchmark: reps x hot/cold, P50/P95/P99")
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--lanes", default=",".join(DEFAULT_LANES))
    ap.add_argument("--ceiling", type=float, default=2.0,
                    help="TTFT fail-fast ceiling seconds")
    ap.add_argument("--max-tokens", type=int, default=128)
    args = ap.parse_args()
    if not sys.stdin.isatty() and args.prompt == ap.get_default("prompt"):
        args.prompt = sys.stdin.read().strip() or args.prompt
    lanes = discover_lanes([a.strip() for a in args.lanes.split(",") if a.strip()])
    if not lanes:
        print("no healthy lanes", file=sys.stderr)
        sys.exit(2)
    print("lanes: %s" % ", ".join(l.addr for l in lanes), file=sys.stderr)
    if args.bench:
        run_bench(lanes, args.reps, args.ceiling)
        return
    fn = run_race if args.race else run_single
    t0 = time.perf_counter()
    try:
        res = fn(args.prompt, lanes, args.ceiling, args.max_tokens)
    except Exception as e:
        print("FAILED: %s" % e, file=sys.stderr)
        sys.exit(1)
    wall = (time.perf_counter() - t0) * 1000.0
    print(res["text"])
    print("[path=%s lane=%s ttft=%.1fms total=%.1fms wall=%.1fms gen=%.1f tok/s n=%d]" % (
        res.get("path"), res.get("winner_lane", res["lane"]), res["ttft_ms"],
        res["total_ms"], wall, res["gen_tps"], res["tokens"]), file=sys.stderr)


if __name__ == "__main__":
    main()
