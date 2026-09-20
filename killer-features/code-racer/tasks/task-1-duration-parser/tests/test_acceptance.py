"""Hidden acceptance tests for task-1-duration-parser.

HIDDEN from candidate strategies: adapters must not read tests/.
Conforms to code-racer INTERFACE.md v1: `from solution import ...` works in
the harness testbed (solution.py sits flat next to this file).
"""
import math

import pytest

from solution import parse_duration


@pytest.mark.parametrize("text,expected", [
    ("1h30m", 5400.0),
    ("2.5h", 9000.0),
    ("90s", 90.0),
    ("1w2d3h", 788400.0),
    ("-1m30s", -90.0),
    ("500µs", 0.0005),
    ("1e3ms", 1.0),
    ("0s", 0.0),
    ("1ns", 1e-9),
    ("1us", 1e-6),
    ("1µs", 1e-6),
    ("1ms", 1e-3),
    ("1m", 60.0),
    ("1h", 3600.0),
    ("1d", 86400.0),
    ("1w", 604800.0),
    (" 1h 30m ", 5400.0),
    ("1H30M", 5400.0),
    ("2D", 172800.0),
    ("1Ms", 1e-3),
    ("+5s", 5.0),
    ("-5s", -5.0),
    (".5h", 1800.0),
    ("1.h", 3600.0),
    ("1H 30M 45S", 5445.0),
    ("100ms200ms", 0.3),
    ("1w 2d 3h 4m 5s 6ms 7us 8ns",
     604800 + 172800 + 10800 + 240 + 5 + 0.006 + 0.000007 + 0.000000008),
])
def test_valid(text, expected):
    got = parse_duration(text)
    assert isinstance(got, float), f"expected float, got {type(got).__name__}"
    assert math.isclose(got, expected, rel_tol=1e-9, abs_tol=1e-12), f"{text!r}: {got} != {expected}"


@pytest.mark.parametrize("text", [
    "",
    "   ",
    "1x",
    "1sec",
    "5",
    "h",
    "1h m",
    "1.5.2s",
    "--5s",
    "1h!",
    "!1h",
    "1h 30",
    "1 hh",
    "1.2.3.4h",
    "m1",
    "1 m m",
    "1ss",
    "1. h",
    "e5s",
    "1e",
    "nan s",
    "infh",
    "1h,30m",
    "1h;30m",
])
def test_invalid_raises_value_error(text):
    with pytest.raises(ValueError):
        parse_duration(text)


def test_negative_decimal():
    assert math.isclose(parse_duration("-2.5h"), -9000.0, rel_tol=1e-9)


def test_repeated_units_sum():
    assert math.isclose(parse_duration("1h1h"), 7200.0, rel_tol=1e-9)


def test_result_is_float_not_int():
    assert type(parse_duration("1s")) is float
