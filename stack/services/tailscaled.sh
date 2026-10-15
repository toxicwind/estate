#!/usr/bin/env bash
# Estate Tailscale Service Wrapper
exec /usr/bin/tailscaled --state=/home/toxic/estate/.state/tailscaled.state --socket=/home/toxic/estate/.state/tailscaled.sock
