#!/bin/bash
set -a; source "$HOME/estate/config/.secrets" 2>/dev/null || true; set +a
exec vansrouter "$@"
