#!/bin/bash
set -euo pipefail
echo "Running tests..."
cd /home/toxic/sovereign
python3 tests/test_e2e.py
