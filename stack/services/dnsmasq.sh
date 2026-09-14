#!/usr/bin/env bash
# dnsmasq — LAN DNS for sovereign (openclaw domains + caching forwarder)
# Managed by pitchfork. Raw systemd dnsmasq.service is disabled in favor of this.
set -euo pipefail

# dnsmasq binds port 53 (privileged); run via sudo like stack/services/kafka.sh does.
exec sudo /usr/bin/dnsmasq -k -C /etc/dnsmasq.conf
