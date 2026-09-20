#!/bin/sh
# Mock `kimi` binary: ignores kimi-style args, runs the mock backend server.
exec bun "$MOCK_BACKEND_TS" --port "$3"
