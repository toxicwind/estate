#!/usr/bin/env python3
"""
hft_race: HFT-style redundant-lane racing for tool-capable LLM inference.

Chris's HFT doctrine (non-trading): race redundant paths, first-VALID-wins;
fail-fast per-attempt ceilings; hot persistent connections (no handshake per
request); measure every hop; fallback planned before the primary.

Synthesis: hft_fetch.py races egress paths for HTTP; squawk races bridge vs WS
for chat transport. Nobody on yote races *inference lanes* for agentic tool
loops — this does exactly that.

Lanes (same model, different routes):
  direct  - http://127.0.0.1:25152  model qwen3.5-9b-tool (pitchfork daemon)
  herd    - http://127.0.0.1:25100  model toolcall-local/qwen3.5-9b-tool (llama-swap peer)

Valid = HTTP 200 + JSON with choices[0].message (structural; finish_reason is
recorded, not gated). First valid response wins; losers are abandoned.
Each lane keeps ONE hot persistent http.client connection (dial once).

Winner ledger: ~/.cache/toolcall-agent/race-winners.jsonl — one JSON line per
race: ts, winner, per-lane latencies, finish_reason, server timings. Read it to
keep the fast path hot; if one lane always wins, cut the other (doctrine).

API:
    from hft_race import race_chat
    resp, meta = race_chat(messages, tools=TOOLS, ceiling=30)
    # resp: parsed chat-completions JSON from the winning lane
    # meta: {"winner": "direct", "latencies": {...}, "errors": {...}, "ms_total": ...}

CLI:
    python3 hft_race.py --bench 20   # P50/P95/P99 per lane + winner distribution
"""
import http.client
import json
import os
import sys
import threading
import time

LANES = [
    ("direct", "127.0.0.1", 25152, "qwen3.5-9b-tool"),
    ("herd", "127.0.0.1", 25100, "toolcall-local/qwen3.5-9b-tool"),
]
CEILING = float(os.environ.get("RACE_CEILING", "30"))
LEDGER = os.path.expanduser("~/.cache/toolcall-agent/race-winners.jsonl")

_conns = {}
_conns_lock = threading.Lock()


def _conn(name, host, port):
    """Hot persistent connection per lane; reconnect if dead."""
    with _conns_lock:
        c = _conns.get(name)
        if c is not None:
            try:
                c.request("GET", "/health")
                r = c.getresponse()
                r.read()
                if r.status < 500:
                    return c
            except Exception:
                pass
            try:
                c.close()
            except Exception:
                pass
        c = http.client.HTTPConnection(host, port, timeout=CEILING)
        _conns[name] = c
        return c


def _ledger_write(entry):
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # ledger is telemetry; never fail a race over it


def _leg(name, host, port, model, body, box):
    t0 = time.time()
    try:
        c = _conn(name, host, port)
        payload = dict(body)
        payload["model"] = model
        data = json.dumps(payload).encode()
        c.request("POST", "/v1/chat/completions", body=data,
                  headers={"Content-Type": "application/json",
                           "Connection": "keep-alive"})
        r = c.getresponse()
        raw = r.read()
        lat = time.time() - t0
        if r.status != 200:
            box[name] = (False, None, lat, "http %d" % r.status)
            return
        try:
            resp = json.loads(raw)
        except Exception as e:
            box[name] = (False, None, lat, "bad json: %s" % e)
            return
        try:
            msg = resp["choices"][0]["message"]
            assert isinstance(msg, dict)
        except Exception:
            box[name] = (False, None, lat, "no choices[0].message")
            return
        box[name] = (True, resp, lat, None)
    except Exception as e:
        box[name] = (False, None, time.time() - t0,
                     "%s: %s" % (type(e).__name__, str(e)[:150]))


def race_chat(messages, tools=None, tool_choice="auto", temperature=0,
              ceiling=CEILING, log=True, collect_all=False):
    """Race all lanes; return (winning_response_json, meta). Raises on total loss.

    collect_all=True: wait for every leg (bounded by ceiling) so per-lane
    latency distributions are honest; winner is still first-valid.
    Abandoned lanes (losers when collect_all=False) are recorded as
    "abandoned", never as timeouts — the ledger must not lie.
    """
    body = {"messages": messages, "temperature": temperature}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice
    box, threads = {}, {}
    t0 = time.time()
    for name, host, port, model in LANES:
        t = threading.Thread(target=_leg, args=(name, host, port, model, body, box),
                             daemon=True)
        t.start()
        threads[name] = t
    winner, win_resp, latencies, errors, abandoned = None, None, {}, {}, []
    deadline = t0 + ceiling + 2.0
    pending = set(threads)
    while pending and time.time() < deadline:
        for name in list(pending):
            t = threads[name]
            t.join(timeout=0.05)
            if not t.is_alive():
                ok, resp, lat, err = box.get(name, (False, None, None, "no result"))
                latencies[name] = round(lat, 3) if lat is not None else None
                if err:
                    errors[name] = err
                if ok and winner is None:
                    winner = name
                    win_resp = resp
                pending.discard(name)
        if winner is not None and not collect_all:
            break
    # Lanes still pending: fail-fast record. With collect_all=False the winner
    # already decided, so leftovers were ABANDONED (not timed out).
    for name in pending:
        if not collect_all:
            abandoned.append(name)
            errors.setdefault(name, "abandoned (winner=%s)" % winner)
        else:
            latencies.setdefault(name, None)
            errors.setdefault(name, "timeout>%.0fs" % ceiling)
    ms_total = round((time.time() - t0) * 1000, 1)
    if winner is None:
        if log:
            _ledger_write({"ts": t0, "winner": None, "latencies": latencies,
                           "errors": errors, "ms_total": ms_total})
        raise RuntimeError("all lanes failed: %s" % json.dumps(errors))
    finish = None
    try:
        finish = win_resp["choices"][0].get("finish_reason")
    except Exception:
        pass
    srv_timings = win_resp.get("timings", {})
    meta = {"winner": winner, "latencies": latencies, "errors": errors,
            "abandoned": abandoned, "finish_reason": finish, "ms_total": ms_total,
            "server_timings": {k: srv_timings.get(k) for k in
                               ("prompt_ms", "predicted_ms") if k in srv_timings}}
    if log:
        _ledger_write({"ts": t0, "winner": winner, "latencies": latencies,
                       "abandoned": abandoned, "finish_reason": finish,
                       "ms_total": ms_total,
                       "server_timings": meta["server_timings"]})
    return win_resp, meta


def bench(n=20):
    """P50/P95/P99 per lane + winner distribution (doctrine: not just the mean)."""
    import statistics
    prompt = "What is 37 * 42? Use the calculator tool to compute it."
    tools = [{"type": "function", "function": {
        "name": "calculator", "description": "arithmetic",
        "parameters": {"type": "object",
                       "properties": {"expression": {"type": "string"}},
                       "required": ["expression"]}}}]
    per_lane, wins, fails = {}, {}, 0
    for i in range(n):
        try:
            _, meta = race_chat([{"role": "user", "content": prompt}],
                                tools=tools, ceiling=CEILING, collect_all=True)
            for lane, lat in meta["latencies"].items():
                if lat is not None:
                    per_lane.setdefault(lane, []).append(lat * 1000)
            wins[meta["winner"]] = wins.get(meta["winner"], 0) + 1
        except Exception as e:
            fails += 1
            print("iter %d failed: %s" % (i, e))
    print("n=%d fails=%d" % (n, fails))
    for lane, vals in per_lane.items():
        vals.sort()
        q = lambda p: vals[min(len(vals) - 1, int(p * len(vals)))]
        print("lane %-8s n=%-3d p50=%7.0fms p95=%7.0fms p99=%7.0fms mean=%7.0fms" %
              (lane, len(vals), q(0.50), q(0.95), q(0.99), statistics.mean(vals)))
    print("winner distribution:", wins)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--bench":
        bench(int(sys.argv[2]))
    else:
        resp, meta = race_chat([{"role": "user", "content": "ping"}])
        print(json.dumps(meta, indent=2))
