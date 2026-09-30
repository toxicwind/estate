"""Pattern 6: SWITCH / SURFACE / SOFT error taxonomy.

  SWITCH   park the key, fail over (401,402,403,404,429,5xx)
  SURFACE  return upstream body unchanged; key is fine (400,422)
  SOFT     try next key but do NOT park (timeouts, 200+error body)
"""
SWITCH = "switch"
SURFACE = "surface"
SOFT = "soft"


def classify(
    status: int,
    body: bytes = b"",
    exception: BaseException | None = None,
    *,
    fail_status: frozenset[int] = frozenset(),
    surface_codes: frozenset[int] = frozenset(),
    soft_codes: frozenset[int] = frozenset(),
) -> str:
    if exception is not None:
        return SOFT
    if status in surface_codes:
        return SURFACE
    if status in soft_codes:
        return SOFT
    if status in fail_status:
        return SWITCH
    if 200 <= status < 300:
        if body and _looks_like_error(body):
            return SOFT
        return SOFT
    if 400 <= status < 500:
        return SURFACE
    if 500 <= status < 600:
        return SWITCH
    return SOFT


def _looks_like_error(body: bytes) -> bool:
    head = body.lstrip()[:64].lower()
    return head.startswith(b'{"error') or head.startswith(b"error")
