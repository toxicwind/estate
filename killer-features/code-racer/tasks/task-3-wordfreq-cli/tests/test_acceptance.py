"""Hidden acceptance tests for task-3-wordfreq-cli.

HIDDEN from candidate strategies. Conforms to code-racer INTERFACE.md v1:
the candidate's program is collected as solution.py and sits flat next to
this file in the harness testbed; the CLI is exercised as a real subprocess.

In the corpus working dir the program is wordfreq.py; in the harness testbed
it is solution.py. The test discovers whichever exists.
"""
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))


def find_cli():
    for name in ("wordfreq.py", "solution.py"):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("no CLI program found (wordfreq.py/solution.py)")


CLI = find_cli()


def run_cli(args, stdin_data=None, cwd=HERE):
    return subprocess.run(
        [sys.executable, CLI] + args,
        input=stdin_data,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=20,
    )


def test_basic_top2_stdin():
    p = run_cli(["--top", "2"], stdin_data="b a b\nA c b")
    assert p.returncode == 0, p.stderr
    assert p.stdout == "b 3\na 2\n"


def test_tie_broken_alphabetically():
    p = run_cli(["--top", "3"], stdin_data="zebra apple mango zebra apple mango")
    assert p.returncode == 0, p.stderr
    assert p.stdout == "apple 2\nmango 2\nzebra 2\n"


def test_tokenization_lowercase_and_punctuation():
    p = run_cli([], stdin_data="Hello, HELLO! don't stop.")
    assert p.returncode == 0, p.stderr
    lines = p.stdout.splitlines()
    assert lines[0] == "hello 2"
    # "don't" -> don, t
    assert "don 1" in lines
    assert "t 1" in lines


def test_min_len_filters():
    p = run_cli(["--min-len", "3"], stdin_data="a bb ccc dddd a bb ccc")
    assert p.returncode == 0, p.stderr
    assert p.stdout == "ccc 2\ndddd 1\n"


def test_default_top10_truncates():
    words = " ".join(f"w{i:02d}" for i in range(15))
    p = run_cli([], stdin_data=words)
    assert p.returncode == 0, p.stderr
    assert len(p.stdout.splitlines()) == 10


def test_top0_prints_nothing():
    p = run_cli(["--top", "0"], stdin_data="a a b")
    assert p.returncode == 0, p.stderr
    assert p.stdout == ""


def test_empty_input():
    p = run_cli([], stdin_data="")
    assert p.returncode == 0, p.stderr
    assert p.stdout == ""


def test_file_input(tmp_path):
    f = tmp_path / "essay.txt"
    f.write_text("the cat and the dog and the cat")
    p = run_cli(["--top", "2", str(f)])
    assert p.returncode == 0, p.stderr
    assert p.stdout == "the 3\nand 2\n"


def test_missing_file_exit2_and_stderr():
    p = run_cli(["/nonexistent-dir-xyz/nope.txt"])
    assert p.returncode == 2
    assert p.stderr.strip() != ""


def test_help_exit0():
    p = run_cli(["--help"])
    assert p.returncode == 0
    assert "top" in p.stdout.lower()


def test_bad_arg_exit2():
    p = run_cli(["--top", "abc"])
    assert p.returncode == 2


def test_negative_top_exit2():
    p = run_cli(["--top", "-1"], stdin_data="a b")
    assert p.returncode == 2


def test_case_insensitive_counting():
    p = run_cli([], stdin_data="Apple APPLE apple")
    assert p.returncode == 0, p.stderr
    assert p.stdout == "apple 3\n"


def test_digits_are_word_chars():
    p = run_cli([], stdin_data="abc123 456 abc123")
    assert p.returncode == 0, p.stderr
    assert p.stdout.splitlines()[0] == "abc123 2"


def test_top_larger_than_vocab():
    p = run_cli(["--top", "100"], stdin_data="x y x")
    assert p.returncode == 0, p.stderr
    assert p.stdout == "x 2\ny 1\n"


def test_cli_is_executable_program():
    # The deliverable must be runnable as `python3 <file> ...` (has a main guard).
    with open(CLI, "r", encoding="utf-8") as f:
        src = f.read()
    assert '__main__' in src
