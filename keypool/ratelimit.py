"""Patterns 1 & 7: header parsing + proactive preemption.

Formats handled:
  Retry-After: 30                          (seconds)
  Retry-After: Wed, 21 Oct 2026 07:28:00 GMT  (HTTP-date)
  retry-after-ms: 30000                    (OpenAI)
  x-ratelimit-reset-requests: 6m0s         (Go duration)
  x-ratelimit-reset: 1699999999            (epoch)
"""
import re
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Mapping

_DUR = re.compile(r"(\d+(?:\.\d+)?)(ms|s|m|h)", re.I)
_UNIT = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}


@dataclass
class Limit:
    remaining: int | None = None
    reset_at: float | None = None  # seconds from now


def parse_retry_after(v: str) -> float | None:
    if not v:
        return None
    v = v.strip()
    try:
        return max(0.0, float(v))
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(v)
        return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())
    except Exception:
        return None


def parse_duration(v: str) -> float | None:
    """Go-style duration: '6m0s', '1h30m', '500ms'."""
    if not v:
        return None
    v = v.strip()
    total = 0.0
    for tok, unit in _DUR.findall(v):
        total += float(tok) * _UNIT[unit.lower()]
    return total if total > 0 else None


def parse_epoch_or_iso(v: str) -> float | None:
    if not v:
        return None
    v = v.strip()
    try:
        import time as _t
        return max(0.0, int(v) - _t.time())
    except ValueError:
        pass
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())
    except Exception:
        return None


def wait_seconds(headers: Mapping[str, str]) -> float | None:
    """Best-effort wait hint from any known rate-limit header."""
    lc = {k.lower(): v for k, v in headers.items()}
    # Directives first
    for h in ("retry-after", "retry-after-ms"):
        v = lc.get(h)
        if v:
            if h == "retry-after-ms":
                try:
                    return max(0.0, float(v) / 1000.0)
                except ValueError:
                    pass
            else:
                s = parse_retry_after(v)
                if s is not None:
                    return s
    # Reset hints
    for h in ("x-ratelimit-reset-requests", "x-ratelimit-reset-tokens"):
        s = parse_duration(lc.get(h, ""))
        if s:
            return s
    s = parse_epoch_or_iso(lc.get("x-ratelimit-reset", ""))
    if s:
        return s
    return None


def parse(headers: Mapping[str, str]) -> Limit:
    lc = {k.lower(): v for k, v in headers.items()}
    rem = None
    for h in ("x-ratelimit-remaining-requests", "x-ratelimit-remaining"):
        v = lc.get(h)
        if v is not None:
            try:
                rem = int(v)
                break
            except ValueError:
                try:
                    rem = int(float(v))
                    break
                except ValueError:
                    pass
    return Limit(remaining=rem, reset_at=wait_seconds(headers))


def should_preempt(lim: Limit, floor: int, window: float) -> bool:
    if lim.remaining is None or lim.remaining > floor:
        return False
    if lim.reset_at is None:
        return True
    return lim.reset_at <= window
