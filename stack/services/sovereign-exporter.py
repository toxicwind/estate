#!/usr/bin/env python3
"""sovereign-exporter: estate metrics for Prometheus/Grafana (port 25213).

Covers what the estate's dashboards actually query but nothing exports:
  fleet_gpu_*            GPU via nvidia-smi (Fleet-Bench dashboard)
  sovereign_daemon_up    pitchfork daemon states from state.toml
  sovereign_port_listening  ss listeners, labeled with known service names
  sovereign_bridge_lane_up  TCP connect checks on the bridge lanes
  sovereign_market_*     oracle-market workflow: bidders, loop, ledger events
Stdlib only. Scraped every 15s by Prometheus.
"""
import json
import re
import socket
import subprocess
import time
import tomllib
from http.server import BaseHTTPRequestHandler, HTTPServer

LISTEN = ("127.0.0.1", 25213)
STATE_TOML = "/home/toxic/.local/state/pitchfork/state.toml"
LEDGER = "/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl"

KNOWN_PORTS = {
    25100: "herd", 25101: "model-guard", 25102: "yote", 25103: "axiom",
    25105: "prometheus", 25106: "hf-downloader", 25107: "null-g",
    25109: "keypool", 25110: "grafana", 25127: "mesh-mcp",
    25135: "squawk-feed", 25146: "whatsapp-webhook", 25147: "squawk-ws",
    25193: "flock", 25198: "mcp", 25201: "serve-root", 25202: "gemini-mcp",
    25204: "exec-ws", 25205: "prom-backend", 25207: "status",
    25208: "nginx", 25209: "matter", 25210: "grafana-backend",
    25211: "node-exporter", 25213: "sovereign-exporter",
}
BRIDGE_LANES = {"ws-exec": 25204, "mcp": 25198, "squawk-ws": 25147,
                "squawk-feed": 25135}


def sh(cmd, timeout=10):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout).stdout
    except Exception:
        return ""


def gpu_metrics(out):
    q = sh(["nvidia-smi",
            "--query-gpu=power.draw,temperature.gpu,utilization.gpu,"
            "memory.used,fan.speed",
            "--format=csv,noheader,nounits"], timeout=15)
    for i, line in enumerate(q.strip().splitlines()):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 5:
            continue
        try:
            power, temp, util, mem_mb, fan = map(float, parts)
        except ValueError:
            continue
        lbl = '{gpu="%d"}' % i
        out.append("fleet_gpu_power_draw_watts%s %f" % (lbl, power))
        out.append("fleet_gpu_temperature_celsius%s %f" % (lbl, temp))
        out.append("fleet_gpu_utilization_percent%s %f" % (lbl, util))
        out.append("fleet_gpu_memory_used_mb%s %f" % (lbl, mem_mb))
        out.append("fleet_gpu_fan_speed_percent%s %f" % (lbl, fan))


def daemon_metrics(out):
    try:
        with open(STATE_TOML, "rb") as f:
            daemons = tomllib.load(f).get("daemons", {})
    except Exception:
        return
    items = daemons.items() if isinstance(daemons, dict) else []
    for did, d in items:
        if not isinstance(d, dict):
            continue
        name = str(d.get("id", did)).split("/")[-1]
        name = re.sub(r"[^a-zA-Z0-9_:]", "_", name)
        up = 1 if d.get("status") == "running" else 0
        out.append('sovereign_daemon_up{name="%s"} %d' % (name, up))


def port_metrics(out):
    listening = set()
    for line in sh(["ss", "-ltn"], timeout=10).splitlines():
        m = re.search(r":(\d+)\s", line)
        if m:
            listening.add(int(m.group(1)))
    for port, svc in KNOWN_PORTS.items():
        out.append('sovereign_port_listening{port="%d",service="%s"} %d'
                   % (port, svc, 1 if port in listening else 0))


def lane_metrics(out):
    for lane, port in BRIDGE_LANES.items():
        ok = 0
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=3)
            s.close()
            ok = 1
        except OSError:
            pass
        out.append('sovereign_bridge_lane_up{lane="%s"} %d' % (lane, ok))


def market_metrics(out):
    procs = sh(["ps", "-eo", "cmd"], timeout=10)
    bidders = len(re.findall(r"bidder\.py", procs))
    loop_up = 1 if "oracle_loop.py" in procs else 0
    core_up = 1 if "oracle_daemon.py" in procs else 0
    out.append("sovereign_market_bidders %d" % bidders)
    out.append("sovereign_oracle_loop_up %d" % loop_up)
    out.append("sovereign_oracle_core_up %d" % core_up)
    cutoff = time.time() - 3600
    events = {}
    opened = settled = 0
    try:
        with open(LEDGER) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                ts = d.get("ts", 0)
                ev = d.get("event", "?")
                if ts >= cutoff:
                    events[ev] = events.get(ev, 0) + 1
                if ev == "task_open":
                    opened += 1
                elif ev == "settled":
                    settled += 1
    except OSError:
        pass
    for ev, n in sorted(events.items()):
        ev = re.sub(r"[^a-zA-Z0-9_:]", "_", str(ev))
        out.append('sovereign_market_events_1h{event="%s"} %d' % (ev, n))
    out.append("sovereign_market_open_tasks %d" % max(0, opened - settled))


def render():
    out = []
    gpu_metrics(out)
    daemon_metrics(out)
    port_metrics(out)
    lane_metrics(out)
    market_metrics(out)
    return "\n".join(out) + "\n"


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = render().encode()
        self.send_response(200)
        self.send_header("Content-Type",
                         "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(LISTEN, H).serve_forever()
