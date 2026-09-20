# Task 4 — LRU Cache

Implement a least-recently-used (LRU) cache in `lru_cache.py`.

## Class to implement

```python
class LRUCache:
    def __init__(self, capacity: int): ...
    def get(self, key, default=None): ...
    def put(self, key, value): ...
    def __len__(self): ...
    def __contains__(self, key): ...
    def keys(self): ...
```

## Specification

- `capacity` must be an integer `>= 1`; otherwise raise `ValueError`.
- `put(key, value)`:
  - If `key` is already present, update its value **and** mark it most-recently-used.
  - Otherwise insert it as most-recently-used; if the cache now holds more than
    `capacity` entries, evict the **least**-recently-used entry.
- `get(key, default=None)`:
  - On a hit, return the value and mark the key most-recently-used.
  - On a miss, return `default` and do **not** insert anything.
- `__len__` returns the number of entries currently stored.
- `__contains__(key)` returns `True`/`False` and must **not** change recency order.
- `keys()` returns a `list` of keys ordered **most-recently-used first**.
- Keys may be any hashable; values may be anything (including `None` — a stored
  `None` must be distinguishable from a miss via `__contains__` / `keys()`).

## Examples

```
c = LRUCache(2)
c.put("a", 1); c.put("b", 2)
c.get("a")          # 1 ; order now: a, b
c.put("c", 3)       # evicts "b" ; order: c, a
"b" in c            # False
c.keys()            # ["c", "a"]
len(c)              # 2
```

## Notes

- Only the standard library may be used.
- Aim for O(1) `get`/`put` — the hidden tests include a 50k-operation
  performance check (must finish well under the test time limit).
- The hidden acceptance tests check eviction order precisely; implement exactly
  to this spec.
- Resource limits: `limits.json` in this directory.
