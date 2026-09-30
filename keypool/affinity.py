"""Patterns 5 & 11: session stickiness + GC.

Bind a conversation's session key to one credential so multi-turn
requests keep the provider's prompt cache warm. Cost of a cache miss is
~5-10x a cache read. TTL matches provider cache (default 1h). GC drops
expired bindings.
"""
import hashlib
import threading
from . import clock

DEFAULT_TTL = 3600.0


def session_key(headers, body: dict | None) -> str | None:
    for h in ("X-Hermes-Session-Key", "X-Session-Id",
              "x-session-id", "X-Conversation-Id"):
        v = headers.get(h)
        if v:
            return f"hdr:{v}"
    if not body:
        return None
    if body.get("previous_interaction_id"):
        return f"pid:{body['previous_interaction_id']}"
    if body.get("prompt_cache_key"):
        return f"pck:{body['prompt_cache_key']}"
    msgs = body.get("messages") or body.get("input") or []
    if isinstance(msgs, list):
        for m in msgs:
            if isinstance(m, dict) and m.get("role") == "system":
                t = m.get("content")
                if isinstance(t, str):
                    return f"sys:{hashlib.sha256(t.encode()).hexdigest()[:16]}"
    return None


class AffinityMap:
    def __init__(self, ttl: float = DEFAULT_TTL, max_entries: int = 4096):
        self.ttl = ttl
        self.max_entries = max_entries
        self._m: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def get(self, session: str | None) -> str | None:
        if not session:
            return None
        with self._lock:
            e = self._m.get(session)
            if not e:
                return None
            name, exp = e
            if clock.mono() >= exp:
                del self._m[session]
                return None
            return name

    def bind(self, session: str | None, key_name: str):
        if not session:
            return
        with self._lock:
            if len(self._m) >= self.max_entries:
                oldest = min(self._m, key=lambda k: self._m[k][1])
                del self._m[oldest]
            self._m[session] = (key_name, clock.mono() + self.ttl)

    def unbind(self, session: str | None):
        if not session:
            return
        with self._lock:
            self._m.pop(session, None)

    def gc(self) -> int:
        now = clock.mono()
        with self._lock:
            dead = [k for k, (_, exp) in self._m.items() if now >= exp]
            for k in dead:
                del self._m[k]
            return len(dead)

    def size(self) -> int:
        with self._lock:
            return len(self._m)
