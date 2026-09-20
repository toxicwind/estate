#!/usr/bin/env bash
# Collapse tests for the tau launcher.
# Tests each level of the fallback chain in isolation.
set -euo pipefail

LAUNCHER="${1:-/home/toxic/sovereign/projects/tau/launcher/bin/tau}"
PASS=0
FAIL=0

assert() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        echo "PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $desc"
        FAIL=$((FAIL + 1))
    fi
}

assert_output() {
    local desc="$1" expected="$2"; shift 2
    local out
    out="$("$@" 2>&1 || true)"
    if echo "$out" | rg -q "$expected"; then
        echo "PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $desc (expected '$expected', got: $(echo "$out" | head -c 200))"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== tau launcher collapse tests ==="
echo "launcher: $LAUNCHER"
echo

# Test 1: Launcher is executable
assert "launcher is executable" test -x "$LAUNCHER"

# Test 2: TAU_BIN override is honored (collapse level 1)
# Create a fake binary that prints a marker
FAKE_BIN="$(mktemp)"
printf '#!/bin/bash\necho "FAKE_BIN_MARKER"\n' > "$FAKE_BIN"
chmod +x "$FAKE_BIN"
assert_output "TAU_BIN override wins" "FAKE_BIN_MARKER" \
    env TAU_BIN="$FAKE_BIN" "$LAUNCHER" --version
rm -f "$FAKE_BIN"

# Test 3: Profile creation (default profile auto-created)
TEST_HOME="$(mktemp -d)"
mkdir -p "$TEST_HOME/.tau"  # pre-create so resolve_home honors TEST_HOME
assert_output "default profile created" "schema_version" \
    env HOME="$TEST_HOME" TEST_HOME="$TEST_HOME" TAU_PROFILE="default" \
    bash -c 'rm -rf "$TEST_HOME/.tau/profiles"; "$0" --help 2>&1 || true; cat "$TEST_HOME/.tau/profiles/default.yml"' "$LAUNCHER"

# Test 4: Profile migration v1 → v2
TEST_HOME2="$(mktemp -d)"
mkdir -p "$TEST_HOME2/.tau/profiles"
printf 'schema_version: 1\nllm:\n  model: test-model\n' > "$TEST_HOME2/.tau/profiles/old.yml"
env HOME="$TEST_HOME2" TAU_PROFILE="old" TAU_BIN="/bin/true" "$LAUNCHER" >/dev/null 2>&1 || true
assert_output "v1 profile migrated to v2" "schema_version: 2" \
    cat "$TEST_HOME2/.tau/profiles/old.yml"
assert_output "migration adds backend field" "backend:" \
    cat "$TEST_HOME2/.tau/profiles/old.yml"

# Test 5: --profile flag parsing
TEST_HOME3="$(mktemp -d)"
mkdir -p "$TEST_HOME3/.tau/profiles"
printf 'schema_version: 2\nllm:\n  backend: kimi\n' > "$TEST_HOME3/.tau/profiles/kimi.yml"
FAKE_BIN2="$(mktemp)"
printf '#!/bin/bash\necho "BACKEND=$TAU_LLM_BACKEND"\n' > "$FAKE_BIN2"
chmod +x "$FAKE_BIN2"
assert_output "--profile flag sets backend" "BACKEND=kimi" \
    env HOME="$TEST_HOME3" TAU_BIN="$FAKE_BIN2" "$LAUNCHER" --profile kimi
rm -f "$FAKE_BIN2"
rm -rf "$TEST_HOME" "$TEST_HOME2" "$TEST_HOME3"

# Test 6: No target → clean error (not a crash). Hermetic HOME (with .tau so
# resolve_home honors it) keeps the real dist/omp build artifact from
# satisfying level 5 — the test means "no launch target anywhere".
TEST_HOME6="$(mktemp -d)"
mkdir -p "$TEST_HOME6/.tau"
assert_output "missing everything gives clean error" "no launch target found" \
    env -u TAU_BIN HOME="$TEST_HOME6" TAU_PROFILE=nonexistent \
    bash -c 'cd "$1" && PATH=/usr/bin:/bin "$0"' "$LAUNCHER" "$TEST_HOME6"
rm -rf "$TEST_HOME6"

# Test 7: ./tau directory is NOT treated as an executable override (regression).
# [ -x ./tau ] matches directories; the level-3 override must be a regular file.
# Same hermetic HOME as test 6 so only the ./tau-dir behavior is under test.
TEST_HOME7="$(mktemp -d)"
mkdir -p "$TEST_HOME7/.tau" "$TEST_HOME7/work/tau"  # a directory named tau, not a file
assert_output "./tau directory is not exec'd as override" "no launch target found" \
    env -u TAU_BIN HOME="$TEST_HOME7" TAU_PROFILE=nonexistent \
    bash -c 'cd "$1" && PATH=/usr/bin:/bin "$0"' "$LAUNCHER" "$TEST_HOME7/work"
rm -rf "$TEST_HOME7"

echo
echo "=== $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
