# Task 1 — Duration String Parser

Implement a small utility that converts human-readable duration strings into seconds.

## Function to implement

In `duration_parser.py`:

```python
def parse_duration(s: str) -> float:
    """Parse a duration string and return the total number of seconds as a float."""
```

## Specification

- Supported units and their multipliers (in seconds):

  | unit | seconds |
  |------|---------|
  | `ns` | 1e-9 |
  | `us`, `µs` (U+00B5 MICRO SIGN) | 1e-6 |
  | `ms` | 1e-3 |
  | `s` | 1 |
  | `m` | 60 |
  | `h` | 3600 |
  | `d` | 86400 |
  | `w` | 604800 |

- A duration string is one or more `<number><unit>` terms concatenated, e.g. `"1h30m"`, `"2.5h"`, `"90s"`.
- Whitespace may appear around the whole string and between terms: `" 1h 30m "` is valid.
- Numbers may be integers or decimals (`"1.5h"`); an optional leading `-` makes the whole value negative (`"-5s"` → `-5.0`). A `+` sign is also accepted (`"+5s"` → `5.0`).
- Units are case-insensitive: `"1H"`, `"1Ms"`, `"2D"` are valid.
- The number may also appear in scientific notation: `"1e3ms"` → `1.0`.
- The result is the sum of all terms as a `float`.

## Errors

Raise `ValueError` for any malformed input, including (but not limited to):

- empty string or whitespace-only string
- unknown units (`"1x"`, `"1sec"`)
- a number with no unit (`"5"`)
- a unit with no number (`"h"`, `"1h m"`)
- malformed numbers (`"1.5.2s"`, `"--5s"`)
- any other trailing or leading garbage (`"1h!"`)

## Examples

```
parse_duration("1h30m")   -> 5400.0
parse_duration("2.5h")    -> 9000.0
parse_duration("90s")     -> 90.0
parse_duration("1w2d3h")  -> 788400.0
parse_duration("-1m30s")  -> -90.0
parse_duration("500µs")   -> 0.0005
parse_duration("1e3ms")   -> 1.0
```

## Notes

- Only the standard library may be used.
- The hidden acceptance tests check the examples above plus many edge cases; implement exactly to this spec.
- Resource limits: `limits.json` in this directory.
