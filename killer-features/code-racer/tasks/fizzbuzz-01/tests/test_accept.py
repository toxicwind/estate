"""Acceptance tests for fizzbuzz-01. The strategy never sees this file."""
import pytest

from solution import fizzbuzz


def test_basic():
    assert fizzbuzz(3) == ["1", "2", "Fizz"]
    assert fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]


def test_fifteen():
    out = fizzbuzz(15)
    assert len(out) == 15
    assert out[-1] == "FizzBuzz"
    assert out[2] == "Fizz" and out[4] == "Buzz" and out[5] == "Fizz"


def test_thirty_spot():
    out = fizzbuzz(30)
    assert out[14] == "FizzBuzz" and out[29] == "FizzBuzz"
    assert out[9] == "Buzz" and out[11] == "Fizz"


def test_zero():
    assert fizzbuzz(0) == []


def test_negative():
    with pytest.raises(ValueError):
        fizzbuzz(-1)


def test_types():
    out = fizzbuzz(20)
    assert all(isinstance(x, str) for x in out)


def test_length_and_content_100():
    out = fizzbuzz(100)
    assert len(out) == 100
    assert out[0] == "1" and out[99] == "Buzz"
    assert sum(1 for x in out if x == "FizzBuzz") == 6
