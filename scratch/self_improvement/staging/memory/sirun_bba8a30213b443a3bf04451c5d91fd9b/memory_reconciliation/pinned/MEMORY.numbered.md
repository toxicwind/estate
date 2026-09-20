    1│# MEMORY.md
    2│
    3│<!-- Your curated long-term memory: durable facts, preferences, and commitments. Keep it tight: promote what lasts here, and leave raw day-to-day detail in your daily notes. -->
    4│
    5│## Facts
    6│
    7│## Preferences
    8│
    9│## Commitments
   10│
   11│## Skills workspace (2026-09-14)
   12│- 40 skills installed from Drive bundle into ~/workspace/skills/, plus new `skill-setup` harness (41 total).
   13│- Shared portable venv: ~/workspace/skills/.venv (Pillow, numpy, python-dotenv, requests); requirements.txt alongside. runner.sh files prefer it on PATH.
   14│- `skill-setup/main.py`: --list/--check/--setup/--smoke/--report/--ports. --ports discovers all skill ports (configured from .env, documented in SKILL.md), listening state via /proc, owning PID/process; run wrapped: `unshare -U -r python3 main.py --ports`.
   15│- Configured ports: 5901/6080/9223 (vnc/cdp), 8080 (asymmetric-procedural-orchestrator PROXY_EGRESS_URL), 25109 (pitchfork MCP proxy), 25126 (kimi gateway), 25127 (sovereign egress).
   16│- cdp-namespace-controller + web-tool-vnc-wrapper runners: read .env, audit procs/sockets, unshare check, probe TRUSTED_HOSTS (default 127.0.0.1), chromium --remote-allow-origins built from trusted hosts.
   17│- /home/toxic refs corrected to /home/hatch everywhere except env-log-debugger (purposefully external: describes awrawr-pc target machine, marked as such).
   18│- EXA_API_KEY (same key) in 7 skills, all return HTTP 200. Only credential-like var across all .env files.
   19│