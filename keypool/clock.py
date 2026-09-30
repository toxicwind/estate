"""Pattern 9: monotonic time for all interval math.

Wall-clock steps (NTP, VM suspend, manual date) must never invert a
cooldown. Store deadlines as monotonic timestamps; convert to wall only
for display.
"""
import time as _t

_M0 = _t.monotonic()
_W0 = _t.time()


def mono() -> float:
    """Monotonic seconds. All interval math uses this."""
    return _t.monotonic()


def wall() -> float:
    """Wall-clock seconds. Display and audit only."""
    return _t.time()


def mono_to_wall(m: float) -> float:
    return _W0 + (m - _M0)


def wall_to_mono(w: float) -> float:
    return _M0 + (w - _W0)
