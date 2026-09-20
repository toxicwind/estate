#!/usr/bin/env bash
# Rebuild /home/toxic/.awrawr-mcp-venv from the frozen requirements.
# Created 2026-09-20 after pyarrow/pandas corruption broke audit-export and refusal-nightly.
set -euo pipefail
VENV=/home/toxic/.awrawr-mcp-venv
TS=20260920-161006
if [ -d "" ]; then mv "" ".bak-"; echo "old venv -> .bak-"; fi
python3 -m venv ""
"/bin/pip" install -q -r /home/toxic/awrawr-mcp-venv.requirements.txt
"/bin/python" -c "import pyarrow, pandas; print(\"venv-ok pyarrow\", pyarrow.__version__)"
