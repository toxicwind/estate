#!/usr/bin/env bash
# Sovereign Tailscale Service Wrapper
exec /usr/bin/tailscaled --state=/home/toxic/sovereign/.state/tailscaled.state --socket=/home/toxic/sovereign/.state/tailscaled.sock
