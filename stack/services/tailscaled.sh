#!/usr/bin/env bash
# Estate Tailscale Service Wrapper
exec /usr/bin/tailscaled --state=/home/toxic/pens/estate/.state/tailscaled.state --socket=/home/toxic/pens/estate/.state/tailscaled.sock
