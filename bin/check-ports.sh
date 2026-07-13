set -euo pipefail
source config/ports.env
for v in LLAMA_SWAP_PORT OPENFANG_PORT RUST_WEB_PORT YOTE_PORT PROMETHEUS_PORT HF_DOWNLOADER_PORT WATCHDOG_PORT LANDING_PORT;do p="${!v}";if (( p >= LLAMA_START_PORT && p <= LLAMA_END_PORT ));then echo "COLLISION $v=$p in $LLAMA_START_PORT-$LLAMA_END_PORT";exit 1;fi;done
echo "ports OK"
