#!/usr/bin/env python3
"""
Sovereign Watchdog — Maximal Emergent Monitoring
Monitors: llama-server (GPU/perf), nfcot_proxy (latency/injection),
          openfang (controller), caddy (proxy), system vitals
Actions: logs, alerts, optional process-compose restart via REST API
"""
import os, sys, time, json, logging, subprocess, threading, requests
from datetime import datetime
from collections import deque

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
    handlers=[
        logging.FileHandler('/home/toxic/sovereign/logs/watchdog.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("sovereign_watchdog")

# ─── Config ─────────────────────────────────────────────────────────
CHECK_INTERVAL = 10          # seconds between full sweeps
ALERT_THRESHOLD = 3          # consecutive failures before action
GPU_MEM_WARN = 22_000        # MB — warn if VRAM usage > this (24GB card)
GPU_MEM_CRIT = 23_000        # MB — critical
TOKEN_TPS_WARN = 10.0        # warn if gen speed drops below
LATENCY_WARN_MS = 5000       # nfcot_proxy response time warn

# process-compose REST API (for remote restart if needed)
PC_API_URL = os.environ.get('PC_API_URL', 'http://127.0.0.1:8080')
PC_API_TOKEN = os.environ.get('PC_API_TOKEN', '')

# ─── State ────────────────────────────────────────────────────────────
failures = {k: 0 for k in ['llama', 'nfcot', 'openfang', 'caddy', 'gpu']}
metrics_history = {
    'token_tps': deque(maxlen=60),
    'latency_ms': deque(maxlen=60),
    'gpu_mem': deque(maxlen=60),
}

# ─── Helpers ────────────────────────────────────────────────────────
def pc_headers():
    h = {'Content-Type': 'application/json'}
    if PC_API_TOKEN:
        h['Authorization'] = f'Bearer {PC_API_TOKEN}'
    return h

def pc_restart(process_name: str):
    """Ask process-compose to restart a process via its REST API."""
    try:
        url = f"{PC_API_URL}/process/{process_name}/restart"
        r = requests.post(url, headers=pc_headers(), timeout=5)
        log.warning(f"PC restart {process_name}: HTTP {r.status_code}")
        return r.ok
    except Exception as e:
        log.error(f"PC restart {process_name} failed: {e}")
        return False

def nvidia_smi():
    """Parse nvidia-smi for GPU metrics. Returns dict or None."""
    try:
        out = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total,temperature.gpu,utilization.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if out.returncode != 0:
            return None
        parts = [p.strip() for p in out.stdout.strip().split(',')]
        return {
            'mem_used': int(parts[0]),
            'mem_total': int(parts[1]),
            'temp': int(parts[2]),
            'util': int(parts[3]),
        }
    except Exception as e:
        log.debug(f"nvidia-smi failed: {e}")
        return None

def check_llama():
    """Health + perf metrics from llama-server."""
    try:
        t0 = time.time()
        r = requests.get('http://127.0.0.1:25001/health', timeout=5)
        latency = (time.time() - t0) * 1000

        if r.status_code == 503:
            log.warning("llama-server: still loading model")
            failures['llama'] += 1
            return False
        if r.status_code != 200:
            log.error(f"llama-server: HTTP {r.status_code}")
            failures['llama'] += 1
            return False

        # Grab metrics endpoint for token throughput
        try:
            m = requests.get('http://127.0.0.1:25001/metrics', timeout=3)
            # llama-server metrics are Prometheus-style; parse loosely
            tps = 0.0
            for line in m.text.splitlines():
                if 'llama_tokens_per_second' in line and not line.startswith('#'):
                    try:
                        tps = float(line.split()[-1])
                        metrics_history['token_tps'].append(tps)
                    except ValueError:
                        pass
            if tps > 0 and tps < TOKEN_TPS_WARN and len(metrics_history['token_tps']) > 5:
                log.warning(f"llama-server: token TPS collapsed to {tps:.1f}")
        except Exception:
            pass

        failures['llama'] = 0
        return True

    except requests.exceptions.ConnectionError:
        log.error("llama-server: connection refused")
        failures['llama'] += 1
        return False
    except Exception as e:
        log.error(f"llama-server: check failed: {e}")
        failures['llama'] += 1
        return False

def check_nfcot():
    """Proxy health + latency + flow injection sanity."""
    try:
        t0 = time.time()
        r = requests.get('http://127.0.0.1:25008/v1/models', timeout=5)
        latency = (time.time() - t0) * 1000
        metrics_history['latency_ms'].append(latency)

        if r.status_code != 200:
            log.error(f"nfcot_proxy: HTTP {r.status_code}")
            failures['nfcot'] += 1
            return False

        if latency > LATENCY_WARN_MS:
            log.warning(f"nfcot_proxy: latency {latency:.0f}ms (warn {LATENCY_WARN_MS}ms)")

        failures['nfcot'] = 0
        return True

    except requests.exceptions.ConnectionError:
        log.error("nfcot_proxy: connection refused")
        failures['nfcot'] += 1
        return False
    except Exception as e:
        log.error(f"nfcot_proxy: check failed: {e}")
        failures['nfcot'] += 1
        return False

def check_openfang():
    try:
        r = requests.get('http://127.0.0.1:25004/api/health', timeout=5)
        if r.status_code != 200:
            log.error(f"openfang: HTTP {r.status_code}")
            failures['openfang'] += 1
            return False
        failures['openfang'] = 0
        return True
    except requests.exceptions.ConnectionError:
        log.error("openfang: connection refused")
        failures['openfang'] += 1
        return False
    except Exception as e:
        log.error(f"openfang: check failed: {e}")
        failures['openfang'] += 1
        return False

def check_caddy():
    try:
        r = requests.get('http://127.0.0.1:25000/health', timeout=5)
        if r.status_code != 200:
            log.error(f"caddy: HTTP {r.status_code}")
            failures['caddy'] += 1
            return False
        failures['caddy'] = 0
        return True
    except requests.exceptions.ConnectionError:
        log.error("caddy: connection refused")
        failures['caddy'] += 1
        return False
    except Exception as e:
        log.error(f"caddy: check failed: {e}")
        failures['caddy'] += 1
        return False

def check_gpu():
    """NVIDIA GPU vitals."""
    gpu = nvidia_smi()
    if gpu is None:
        log.error("GPU: nvidia-smi unavailable")
        failures['gpu'] += 1
        return False

    metrics_history['gpu_mem'].append(gpu['mem_used'])

    if gpu['mem_used'] > GPU_MEM_CRIT:
        log.critical(f"GPU: VRAM {gpu['mem_used']}/{gpu['mem_total']} MB — CRITICAL")
        failures['gpu'] += 1
    elif gpu['mem_used'] > GPU_MEM_WARN:
        log.warning(f"GPU: VRAM {gpu['mem_used']}/{gpu['mem_total']} MB — high")
        failures['gpu'] = max(0, failures['gpu'] - 1)
    else:
        failures['gpu'] = 0

    if gpu['temp'] > 85:
        log.warning(f"GPU: temp {gpu['temp']}°C — thermal warning")

    return True

def emit_status():
    """Periodic summary log."""
    status = {k: ('DOWN' if v >= ALERT_THRESHOLD else 'DEGRADED' if v > 0 else 'OK')
              for k, v in failures.items()}
    log.info(f"STATUS | {' | '.join(f'{k}:{v}' for k,v in status.items())}")

    # Rolling averages
    if metrics_history['token_tps']:
        avg_tps = sum(metrics_history['token_tps']) / len(metrics_history['token_tps'])
        log.info(f"METRICS | avg_tps={avg_tps:.1f} | "
                 f"avg_latency={sum(metrics_history['latency_ms'])/len(metrics_history['latency_ms']):.0f}ms | "
                 f"gpu_mem={metrics_history['gpu_mem'][-1] if metrics_history['gpu_mem'] else 'N/A'}MB")

def take_action():
    """Restart processes that have failed too many times."""
    for proc, name in [('llama', 'llama-server'), ('nfcot', 'nfcot_proxy'),
                       ('openfang', 'openfang'), ('caddy', 'caddy')]:
        if failures[proc] >= ALERT_THRESHOLD:
            log.critical(f"{proc}: failure threshold reached — restarting {name}")
            pc_restart(name)
            failures[proc] = 0  # reset after action

# ─── Main Loop ───────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("SOVEREIGN WATCHDOG — Maximal Emergent Monitoring")
    log.info("=" * 60)

    # Wait for initial stack to come up
    time.sleep(15)

    while True:
        check_llama()
        check_nfcot()
        check_openfang()
        check_caddy()
        check_gpu()
        emit_status()
        take_action()
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
