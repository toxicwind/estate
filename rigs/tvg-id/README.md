# tvg-id rig

Provisioned 2026-10-28 (release-group rig for the IPTV/fork lane).

- PERSONA.md — fleet-spawn persona (scene register, real doctrine)
- join.squawk.json — squawk join payload
- config.toml — rig config stub
- glue.sh — rig identity glue

Squawk join line:
`hatch-mcp squawk_send identity=tvg-id 'hi fleet, tvg-id here — the bedroom headend is online'`

Canonical identity: `estate/agents/tvg-id/` (fleet-join-rendered),
activated in the OpenFang kernel (id `94d073d2-b261-4fd9-9978-8533ddf1166b`).