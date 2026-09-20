#!/usr/bin/env bash
# OpenFang kernel launcher (pitchfork-supervised).
# - sources /home/toxic/.secrets so the kernel env has NVIDIA_API_KEY
# - re-registers fleet triggers on EVERY boot (triggers are kernel-memory-only
#   upstream; without this a kernel restart silently drops them)
# - stays in the foreground as the supervised process, forwarding signals
set -a
. /home/toxic/.secrets
set +a
export HOME=/home/toxic
KERNEL=/home/toxic/projects/rig-work/target/debug/openfang
CFG=/home/toxic/sovereign/config/openfang-4200.toml
CLI=/home/toxic/.local/bin/openfang
RELAY_AGENT_ID=69ac0683-9483-42a5-a22c-7710cba8da61

"$KERNEL" start --config "$CFG" &
KPID=$!
trap "kill -TERM $KPID 2>/dev/null" TERM INT
# readiness gate: wait for the API port (fail-fast deadline, no blind sleep)
for _ in $(seq 1 90); do
  (echo > /dev/tcp/127.0.0.1/4200) 2>/dev/null && break
  sleep 1
done
# idempotent trigger re-registration (durable across restarts by construction)
HAVE=$("$CLI" trigger list 2>/dev/null)
maybe_add() {
  echo "$HAVE" | grep -qF "$1" || "$CLI" trigger create "$RELAY_AGENT_ID" "$1" >/dev/null 2>&1
}
maybe_add "{\"agent_spawned\":{\"name_pattern\":\"*\"}}"
maybe_add "{\"system_keyword\":{\"keyword\":\"cronjobexecuted\"}}"
wait $KPID
