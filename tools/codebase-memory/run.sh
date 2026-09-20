#!/bin/bash
# run.sh — supervise codebase-memory-mcp under pitchfork.
#
# The binary's UI daemon (--cbm-daemon-internal) is spawned as a CHILD of the
# main stdio-mode process; run standalone it exits with "invalid internal
# process arguments". The main process exits on stdin EOF, so we hold stdin
# open with an infinite pipe (event-driven, no polling). Pitchfork tracks the
# main process; if it dies, the daemon child dies too and pitchfork retries.
#
# UI port comes from the persisted config:
#   codebase-memory-mcp config set ui_port <port>
set -u
exec /home/toxic/.local/bin/codebase-memory-mcp < <(sleep infinity)
