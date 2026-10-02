# MEMORY.md

<!-- Your curated long-term memory: durable facts, preferences, and commitments. Keep it tight: promote what lasts here, and leave raw day-to-day detail in your daily notes. -->

## Facts
- Chris's other machine is a CachyOS Linux desktop named awrawr-pc (home directory /home/toxic, 62GB RAM). This came from the awrawr-pc diagnostics bundle pulled from Google Drive when the user asked for skill bundle audit and port discovery, recorded 2026-09-14.

## Preferences
- Chris rejected the Semantic Scholar API-key signup as a dead end (gatekept academic-email/essay review form) and wants obtuse, non-mainstream, keyless literature alternatives instead of key-gated sources.

## Commitments

## Skills workspace (2026-09-14)
- 40 skills installed from Drive bundle into ~/workspace/skills/, plus new `skill-setup` harness (41 total).
- Shared portable venv: ~/workspace/skills/.venv (Pillow, numpy, python-dotenv, requests); requirements.txt alongside. runner.sh files prefer it on PATH.
- `skill-setup/main.py`: --list/--check/--setup/--smoke/--report/--ports. --ports discovers all skill ports (configured from .env, documented in SKILL.md), listening state via /proc, owning PID/process; run wrapped: `unshare -U -r python3 main.py --ports`.
- Configured ports: 5901/6080/9223 (vnc/cdp), 8080 (asymmetric-procedural-orchestrator PROXY_EGRESS_URL), 25109 (pitchfork MCP proxy), 25126 (kimi gateway), 25127 (sovereign egress).
- cdp-namespace-controller + web-tool-vnc-wrapper runners: read .env, audit procs/sockets, unshare check, probe TRUSTED_HOSTS (default 127.0.0.1), chromium --remote-allow-origins built from trusted hosts.
- /home/toxic refs corrected to /home/hatch everywhere except env-log-debugger (purposefully external: describes awrawr-pc target machine, marked as such).
- EXA_API_KEY (same key) in 7 skills, all return HTTP 200. Only credential-like var across all .env files.
