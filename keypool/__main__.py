"""Entry point: python -m keypool [--selftest]"""
import os
import signal
import sys
import threading
import time
from http.server import ThreadingHTTPServer

from . import alerts, persist, proxy, secrets as _sec, yamlparse
from .pool import Pool


LISTEN = (os.environ.get("KEYPOOL_HOST", "127.0.0.1"),
          int(os.environ.get("KEYPOOL_PORT", "25109")))
POOLS_PATH = os.environ.get("KEYPOOLS_CONFIG",
                            os.path.expanduser("~/sovereign/config/keypools.yaml"))
SECRETS_PATH = os.environ.get("KEYPOOL_SECRETS", os.path.expanduser("~/.secrets"))
AUDIT_PATH = os.environ.get("KEYPOOL_AUDIT",
                            os.path.expanduser("~/sovereign/data/keypool-audit.jsonl"))
HEALTH_PATH = os.environ.get("KEYPOOL_HEALTH",
                             os.path.expanduser("~/sovereign/data/keypool-health.json"))


def log(m):
    print(f"[keypool] {m}", file=sys.stderr, flush=True)


def build_pools():
    s = _sec.load(SECRETS_PATH)
    doc = yamlparse.load(open(POOLS_PATH, encoding="utf-8").read())
    pools = {}
    for name, cfg in (doc.get("pools") or {}).items():
        try:
            pools[name] = Pool(name, cfg, s)
            log(f"pool {name}: {len(pools[name].keys)} keys loaded")
        except Exception as e:
            log(f"pool {name} config error: {e}")
    return pools, doc




HEALTHY_TTL = float(os.environ.get("KEYPOOL_HEALTHY_TTL", "300"))

# Event-driven poller wakeups: reloads / failures notify instead of polling.
_poller_cond = threading.Condition()


def wake_poller():
    """Wake the health poller immediately (e.g. after a reload)."""
    with _poller_cond:
        _poller_cond.notify_all()


def _health_poller(pools_getter, ttl: float = HEALTHY_TTL):
    """Probe unknown / expired-down / TTL-stale-healthy keys.

    Event-driven: sleeps on a Condition until the next healthy-key TTL
    expiry or an explicit wake_poller() — no fixed-interval timer.
    Previously healthy keys were NEVER revalidated, so a provider-side
    revocation left them green forever.
    """
    import time as _t
    _t.sleep(1.5)  # let the server socket bind first
    while True:
        now = _t.monotonic()
        next_wake = None
        try:
            pools = pools_getter()
            for pname, pool in pools.items():
                for ks in list(pool.keys):
                    needs = (
                        ks.state == "unknown"
                        or (ks.state == "down" and ks.is_parked() is False)
                        or ks.needs_revalidation(ttl)
                    )
                    if needs:
                        ok = pool.probe_and_update(ks)
                        log(f"poller: {pname}/{ks.name} -> "
                            f"{'healthy' if ok else 'down'}")
                for ks in list(pool.keys):
                    if ks.state == "healthy" and ks.last_probe_at > 0:
                        expiry = ks.last_probe_at + ttl - now
                        if next_wake is None or expiry < next_wake:
                            next_wake = expiry
        except Exception as e:
            log(f"poller error: {e}")
        with _poller_cond:
            wait_s = max(1.0, next_wake) if next_wake is not None else 30.0
            _poller_cond.wait(timeout=wait_s)

def main():
    if "--selftest" in sys.argv:
        from . import selftest
        sys.exit(selftest.run())

    pools, _ = build_pools()
    proxy.POOLS = pools
    proxy.ALERTS = alerts.Alerts(AUDIT_PATH)

    def reload_all(signum=None, frame=None):
        log("reload")
        try:
            fresh, _ = build_pools()
            proxy.POOLS = fresh
            persist.write_json(HEALTH_PATH, _snap(fresh))
            wake_poller()
        except Exception as e:
            log(f"reload failed: {e}")

    def _snap(pools):
        return {n: {"breaker": p.breaker.snapshot(),
                    "affinity_size": p.affinity.size(),
                    "keys": [k.public() for k in p.keys]}
                for n, p in pools.items()}

    signal.signal(signal.SIGHUP, reload_all)
    signal.signal(signal.SIGUSR1, reload_all)

    def bg():
        while True:
            try:
                for p in pools.values():
                    p.affinity.gc()
                persist.write_json(HEALTH_PATH, _snap(pools))
            except Exception as e:
                log(f"bg error: {e}")
            time.sleep(10)

    threading.Thread(target=bg, daemon=True, name="keypool-bg").start()

    def _get_pools():
        return dict(proxy.POOLS)

    threading.Thread(target=_health_poller, args=(_get_pools, 10.0),
                     daemon=True, name="keypool-health").start()

    srv = ThreadingHTTPServer(LISTEN, proxy.Handler)
    log(f"listening on {LISTEN[0]}:{LISTEN[1]} (pools: {', '.join(sorted(pools))})")
    srv.serve_forever()


if __name__ == "__main__":
    main()
