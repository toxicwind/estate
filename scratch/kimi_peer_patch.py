#!/usr/bin/env python3
"""Insert the openrouter-kimi peer into herd.yaml (sovereign worktree)."""
import sys

PATH = "/home/toxic/wt-kimi-routing-sov/config/herd.yaml"

PEER_BLOCK = """  # Track K — OpenRouter Kimi/Moonshot models (kimi-auto routing).
  # Added 2026-09-14: Pollinations began requiring a real API key
  # (their free tier now 401s), so the pollinations-free kimi-k3 id is
  # dead. OpenRouter serves the real Kimi models with OPENROUTER_API_KEY.
  # NOTE: proxy is https://openrouter.ai/api (no /v1): the router joins
  # the proxy path with the request path (/v1/chat/completions).
  openrouter-kimi:
    proxy: https://openrouter.ai/api
    apiKey: ${env.OPENROUTER_API_KEY}
    models:
      - moonshotai/kimi-k3
      - moonshotai/kimi-k2.5
      - moonshotai/kimi-k2-0905
      - moonshotai/kimi-k2.6
      - moonshotai/kimi-k2-thinking
      - moonshotai/kimi-k2.7-code
      - moonshotai/kimi-k2
    timeouts:
      connect: 30
      keepalive: 30
      responseHeader: 120
      tlsHandshake: 10
      idleConn: 90

"""

ANCHOR = "  # Track C \u2014 Cloudflare AI Gateway Custom Provider (optional, not blocking v1)"

with open(PATH, encoding="utf-8") as fh:
    text = fh.read()

if "openrouter-kimi:" in text:
    print("already present; no change")
    sys.exit(0)

if ANCHOR not in text:
    print("ANCHOR NOT FOUND", file=sys.stderr)
    sys.exit(1)

text = text.replace(ANCHOR, PEER_BLOCK + ANCHOR, 1)

with open(PATH, "w", encoding="utf-8") as fh:
    fh.write(text)

print("peer inserted")
