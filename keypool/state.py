"""KeyState: one credential + its health, latency, cooldown."""
import hashlib
from dataclasses import dataclass, field
from . import clock, scoring


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


@dataclass
class KeyState:
    name: str
    value: str
    free_only: bool = False
    fp: str = field(init=False)
    state: str = "unknown"       # unknown | healthy | down
    down_until: float = 0.0      # monotonic
    last_probe_at: float = 0.0   # monotonic; 0 = never probed
    last_error: str = ""
    latency: scoring.LatencyTracker = field(default_factory=scoring.LatencyTracker)

    def __post_init__(self):
        self.fp = fingerprint(self.value)

    def is_parked(self) -> bool:
        return self.state == "down" and clock.mono() < self.down_until

    def park(self, seconds: float, why: str):
        self.state = "down"
        self.down_until = clock.mono() + seconds
        self.last_error = why
        self.last_probe_at = clock.mono()

    def revive(self):
        self.state = "healthy"
        self.down_until = 0.0
        self.last_error = ""
        self.last_probe_at = clock.mono()

    def needs_revalidation(self, ttl_s: float) -> bool:
        """True if this healthy key's last probe is older than ttl_s."""
        return (
            self.state == "healthy"
            and self.last_probe_at > 0
            and clock.mono() - self.last_probe_at >= ttl_s
        )

    def public(self) -> dict:
        return {
            "name": self.name,
            "free_only": self.free_only,
            "fingerprint": self.fp,
            "state": self.state,
            "last_error": self.last_error,
            "recover_in_s": round(max(0.0, self.down_until - clock.mono()), 1)
                if self.state == "down" else 0.0,
            "p95_ms": round(self.latency.p95(), 1),
        }
