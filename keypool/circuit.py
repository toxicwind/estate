"""Pattern 2: per-pool circuit breaker.

CLOSED -> normal. OPEN -> fail fast. HALF_OPEN -> one probe allowed.
Doubling recovery_timeout on repeated opens (cap max_recovery_timeout).
"""
import threading
from dataclasses import dataclass, field
from . import clock

CLOSED, OPEN, HALF_OPEN = "closed", "open", "half_open"


@dataclass
class Circuit:
    failure_threshold: int = 5
    recovery_timeout: float = 120.0
    max_recovery_timeout: float = 1800.0
    half_open_max_probes: int = 1

    state: str = CLOSED
    failures: int = 0
    open_until: float = 0.0
    probes_in_flight: int = 0
    current_recovery: float = field(init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        self.current_recovery = self.recovery_timeout

    def allow_request(self) -> bool:
        with self._lock:
            if self.state == CLOSED:
                return True
            if self.state == OPEN:
                if clock.mono() >= self.open_until:
                    self.state = HALF_OPEN
                    self.probes_in_flight = 1
                    return True
                return False
            if self.probes_in_flight < self.half_open_max_probes:
                self.probes_in_flight += 1
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            self.failures = 0
            if self.state == HALF_OPEN:
                self.state = CLOSED
                self.probes_in_flight = 0
                self.current_recovery = self.recovery_timeout

    def record_failure(self) -> None:
        with self._lock:
            self.failures += 1
            if self.state == HALF_OPEN or self.failures >= self.failure_threshold:
                self.state = OPEN
                self.open_until = clock.mono() + self.current_recovery
                self.probes_in_flight = 0
                self.current_recovery = min(
                    self.max_recovery_timeout, self.current_recovery * 2
                )

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "state": self.state,
                "failures": self.failures,
                "recover_in_s": round(max(0.0, self.open_until - clock.mono()), 1),
            }
