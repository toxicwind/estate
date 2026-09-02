#!/bin/bash
# Robust health check script
# Returns 0 if healthy, 1 if any service is unhealthy

FAILED=0
# We want to use the list of ports we know about. 
# The svc-check in mise.toml does this:
# for entry in llama-swap=25100 qdrant=25133 ...
# I'll create a list of services to check.

# For simplicity, let's just use the logic from svc-check but make it return exit code.
SERVICES="llama-swap=25100 qdrant=25133 redis=25199 hal-substrate=25143 yote=25102 ghas-api=25112 ghas-frontend=25114 prometheus=25105 grafana=25110 openfang=25103 rust-web=25201 hf-downloader=25106 pi-web-dashboard=25192 beellama-cpp=25122 ik-llama-cpp=25123 llama-cpp-turboquant=25124 tau=25125 kimi-code=25126 nexus=25127 zed-editor=25129 zedra-host=25130 antigravity-cli=25140"

for entry in $SERVICES; do
    svc=${entry%%=*}
    port=${entry##*=}
    
    # Try common health paths
    HEALTH_URLS=("http://127.0.0.1:${port}/health" "http://127.0.0.1:${port}/-/healthy" "http://127.0.0.1:${port}/api/health" "http://127.0.0.1:${port}/")
    
    STATUS=1
    for url in "${HEALTH_URLS[@]}"; do
        if curl -sf -m 2 "$url" >/dev/null 2>&1; then
            STATUS=0
            break
        fi
    done
    
    if [ $STATUS -ne 0 ]; then
        echo "❌ ${svc} unhealthy on port ${port}"
        FAILED=1
    fi
done
if [ $FAILED -ne 0 ]; then
    curl -s -X POST -d "Stack degraded" https://ntfy.sh/sovereign-alerts >/dev/null 2>&1 || true
fi

exit $FAILED
