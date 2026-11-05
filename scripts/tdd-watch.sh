#!/usr/bin/env bash
# tdd-watch — dual-lane TDD watcher (2026-11-05)
# `mise watch A B` does NOT union sources: it passed the second task name as an
# argument to the first task's script. Run one watcher per lane instead.
set -u
mise watch kappa-tdd &
PID1=$!
mise watch tau-tdd &
PID2=$!
trap 'kill $PID1 $PID2 2>/dev/null' EXIT INT TERM
wait
