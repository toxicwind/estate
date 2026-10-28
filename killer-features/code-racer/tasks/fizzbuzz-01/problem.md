# FizzBuzz — sample code-racer task

Write a Python module `solution.py` exposing:

```python
def fizzbuzz(n: int) -> list[str]: ...
```

Rules:
- `fizzbuzz(n)` returns a list of length `n` (for `n >= 0`).
- Element `i` (1-based) is:
  - `"FizzBuzz"` if `i` is divisible by 15,
  - `"Fizz"` if divisible by 3 (but not 15),
  - `"Buzz"` if divisible by 5 (but not 15),
  - otherwise `str(i)`.
- `fizzbuzz(0)` returns `[]`.
- Negative `n` raises `ValueError`.

Examples:
- `fizzbuzz(3)` → `["1", "2", "Fizz"]`
- `fizzbuzz(5)` → `["1", "2", "Fizz", "4", "Buzz"]`
- `fizzbuzz(15)[-1]` → `"FizzBuzz"`

Output your solution as a single ```python fenced code block. No other code.
