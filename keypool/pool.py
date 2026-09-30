"""Pool: one upstream, N keys, all patterns wired together."""
import threading
import urllib.error
import urllib.request

from . import (affinity, capacity, circuit, clock, errors, ratelimit,
               scoring, state as _state)


class Pool:
    def __init__(self, name: str, cfg: dict, secrets: dict):
        self.name = name
        self.upstream = (cfg.get("upstream") or "").rstrip("/")
        self.protocol = cfg.get("protocol", "openai")
        self.interactions_path = cfg.get("interactions_path", "/v1beta/interactions")
        health = cfg.get("health") or {}
        self.health_method = health.get("method", "GET")
        self.health_path = health.get("path", "/v1/models")
        self.health_ok = set(health.get("ok", [200]))
        self.fail_status = frozenset(cfg.get("fail_status",
                                             [400, 401, 402, 403, 404, 429]))
        self.surface_codes = frozenset(cfg.get("surface_codes", [400, 422]))
        self.soft_codes = frozenset(cfg.get("soft_codes", []))
        self.probe_timeout = float(cfg.get("probe_timeout", 5))
        self.request_timeout = float(cfg.get("request_timeout", 180))
        self.cooldown = {int(k): float(v) for k, v in (cfg.get("cooldown") or {}).items()
                         if str(k).isdigit()}
        self.cooldown_default = float((cfg.get("cooldown") or {}).get("default", 120))

        self.keys: list[_state.KeyState] = []
        for entry in cfg.get("keys") or []:
            if isinstance(entry, dict):
                kname = entry.get("name")
                free_only = bool(entry.get("free_only"))
            else:
                kname = str(entry)
                free_only = "FREE" in kname
            if not kname:
                continue
            v = secrets.get(kname)
            if v:
                self.keys.append(_state.KeyState(kname, v, free_only=free_only))

        self.lock = threading.Lock()
        self.breaker = circuit.Circuit(
            failure_threshold=int((cfg.get("circuit") or {}).get("failure_threshold", 5)),
            recovery_timeout=float((cfg.get("circuit") or {}).get("recovery_timeout", 120)),
        )
        cap = cfg.get("capacity") or {}
        self.capacity = capacity.Capacity(
            optimal=int(cap.get("optimal", 2)),
            maximum=int(cap.get("max", 8)),
        )
        aff = cfg.get("affinity") or {}
        self.affinity = affinity.AffinityMap(
            ttl=float(aff.get("ttl", affinity.DEFAULT_TTL))
        )
        self._rl_floor = int((cfg.get("ratelimit") or {}).get("preempt_remaining", 2))
        self._rl_window = float((cfg.get("ratelimit") or {}).get("preempt_window", 60))
        self._headers_seen: dict[str, ratelimit.Limit] = {}
        self._health_map = None  # selftest hook

    # ── health probe
    def _probe(self, ks):
        if self._health_map is not None:
            r = self._health_map.get(ks.name, (False, 9999.0))
            return bool(r[0]), float(r[1])
        url = self.upstream + self.health_path
        req = urllib.request.Request(url, method=self.health_method)
        up = self.upstream.rstrip("/")
        if up.endswith("/openai"):
            req.add_header("Authorization", "Bearer " + ks.value)
        elif "generativelanguage.googleapis.com" in up:
            req.add_header("x-goog-api-key", ks.value)
        else:
            req.add_header("Authorization", "Bearer " + ks.value)
        t0 = clock.mono()
        try:
            with urllib.request.urlopen(req, timeout=self.probe_timeout) as r:
                return r.status in self.health_ok, (clock.mono() - t0) * 1000
        except urllib.error.HTTPError as e:
            return e.code in self.health_ok, (clock.mono() - t0) * 1000
        except Exception:
            return False, (clock.mono() - t0) * 1000

    def probe_and_update(self, ks) -> bool:
        ok, ms = self._probe(ks)
        with self.lock:
            ks.latency.record(ms)
            if ok:
                ks.revive()
                self.breaker.record_success()
            else:
                ks.park(self.cooldown_default, "probe_failed")
                self.breaker.record_failure()
        return ok

    # ── selection
    def _eligible(self, model_id):
        is_free = bool(model_id) and (
            model_id == "openrouter/free" or model_id.endswith(":free")
        )
        out = []
        with self.lock:
            snap = list(self.keys)
        for ks in snap:
            if ks.is_parked():
                continue
            if not is_free and ks.free_only:
                continue
            lim = self._headers_seen.get(ks.name)
            if lim and ratelimit.should_preempt(lim, self._rl_floor, self._rl_window):
                continue
            out.append(ks)
        return out

    def _score(self, ks, is_free):
        return scoring.score(
            health=self.breaker.snapshot()["state"] == "closed" and 1.0
                   or (0.5 if self.breaker.snapshot()["state"] == "half_open" else 0.0),
            p95_ms=ks.latency.p95(),
            variance=ks.latency.variance(),
            quota=None,
            is_free=is_free or ks.free_only,
        )

    def pick(self, model_id=None, session=None):
        if not self.breaker.allow_request():
            return None

        if session:
            bound = self.affinity.get(session)
            if bound:
                for ks in self.keys:
                    if ks.name == bound and not ks.is_parked():
                        return ks
                self.affinity.unbind(session)

        eligible = self._eligible(model_id)
        if not eligible:
            with self.lock:
                parked = [k for k in self.keys if k.state == "down"]
            for ks in parked:
                if self.probe_and_update(ks):
                    eligible.append(ks)
                    break
            if not eligible:
                return None

        is_free = bool(model_id) and (
            model_id == "openrouter/free" or model_id.endswith(":free")
        )
        pairs = [(ks.name, self._score(ks, is_free)) for ks in eligible]
        chosen_name = scoring.weighted_pick(pairs)
        chosen = next((k for k in eligible if k.name == chosen_name), eligible[0])
        if session:
            self.affinity.bind(session, chosen.name)
        return chosen

    # ── outcomes
    def on_success(self, ks, headers, latency_ms):
        with self.lock:
            ks.latency.record(latency_ms)
            ks.revive()
        self.breaker.record_success()
        try:
            self._headers_seen[ks.name] = ratelimit.parse(headers)
        except Exception:
            pass

    def on_failure(self, ks, kind, status, headers, session=None):
        wait = None
        if headers is not None:
            try:
                wait = ratelimit.wait_seconds(headers)
            except Exception:
                pass
        if kind == errors.SWITCH:
            cd = wait if wait is not None else self.cooldown.get(status, self.cooldown_default)
            with self.lock:
                ks.park(cd, f"http:{status}")
            self.breaker.record_failure()
            if session:
                self.affinity.unbind(session)
        elif kind == errors.SOFT:
            self.breaker.record_failure()
        # SURFACE: no key change

    def classify(self, status, body, exc=None):
        return errors.classify(
            status, body, exc,
            fail_status=self.fail_status,
            surface_codes=self.surface_codes,
            soft_codes=self.soft_codes,
        )
