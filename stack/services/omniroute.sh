#!/usr/bin/env bash
# OmniRoute upstream image (diegosouzapw/omniroute). Pitchfork owns the
# lifecycle. Docker restart policy stays "no" so this is the only supervisor.
# Host port is OMNIROUTE_PORT (20130). Container port stays 20128, which is
# also VansRouter's default — they must not share the host port.
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-/home/toxic/estate}"
source "$SOV/stack/lib-ports.sh"
require_port OMNIROUTE_PORT

NAME="${OMNIROUTE_CONTAINER:-omniroute-gateway}"
if ! docker inspect "$NAME" >/dev/null 2>&1; then
  echo "OmniRoute container $NAME is not created." >&2
  exit 1
fi

host_port="$(docker inspect -f '{{(index (index .NetworkSettings.Ports "20128/tcp") 0).HostPort}}' "$NAME" 2>/dev/null || true)"
# NetworkSettings.Ports is empty until the container has been started once
# after create. Fall back to HostConfig.PortBindings.
if [[ -z "$host_port" ]]; then
  host_port="$(docker inspect -f '{{(index (index .HostConfig.PortBindings "20128/tcp") 0).HostPort}}' "$NAME")"
fi
if [[ "$host_port" != "$OMNIROUTE_PORT" ]]; then
  echo "OmniRoute host port is $host_port, want $OMNIROUTE_PORT (VansRouter owns 20128)." >&2
  exit 1
fi

docker update --restart=no "$NAME" >/dev/null
if [[ "$(docker inspect -f '{{.State.Running}}' "$NAME")" == "true" ]]; then
  exec docker attach --sig-proxy=true "$NAME"
fi
exec docker start -a "$NAME"
