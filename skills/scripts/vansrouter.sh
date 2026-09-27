#!/bin/bash
set -a; source "$HOME/sovereign/config/.secrets" 2>/dev/null || true; set +a
exec vansrouter "$@"
