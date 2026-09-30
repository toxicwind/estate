---
crew: 'port-syscall-integrator'
scope: 'PORTS proven by live syscalls (strace bind/listen) + MCPs/connectors/endpoints/integrations estate-wide; SSOT ports.env reconciliation; pitchfork pre-launch guard; port-audit.py hardening'
owner: 'Ember (port-syscall-integrator)'
status: 'DONE (2026-09-20) -- core fix fc6b912a91 (kimi-code --no-port-walk fail-fast on EADDRINUSE; live 25126 health 200); hardening DONE by port-guard-harden: commits 7f6146bc42 (hardened port-audit.py: /proc cmdline+ancestry attribution, intentional alias groups, dynamic-pool classification, exit 0/1/2 + --strict/--json; claim-port rewritten as fail-fast pre-launch guard - no kills/sleeps/polls, exit 4 occupied with holder cmdlines, exit 5 protected ports 8379/25204/25147/25135 incl. protected-holder cmdline detection; ports.env hygiene: retired ZEDRA_HOST_PORT + dup NULL_G_PROXY_PORT removed, WAYLAND_MCP_PORT -> SQUAWK_FEED_PORT, owner hints for 25101/25108/25114/25120/25145/25199) + f0c63dca77 (tracked bin/port-audit.py + bin/tests, bin/port-audit wrapper, README). 21 stdlib-unittest tests pass on yote; live audit exits 0 on healthy estate; occupied-port refusal proven live (exit 4, holder survives, payload not executed); kimi restarted via pitchfork-restart through new guard (pid 2976788, :25126 health 200).'
order: 31
registered: '2026-09-20'
updated: '2026-09-29'
---

# port-syscall-integrator

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
