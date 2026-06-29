#!/bin/bash
set -euo pipefail
echo "Pulling model..."
hf download "$1" --local-dir /home/toxic/models/hf/"${1//\//_}"
echo "Model pulled"
