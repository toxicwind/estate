---
crew: 'shep-repair'
scope: 'Shep MCP gateway repair: pitchfork sovereign/shep errored -- mcp_config.json (gitignored live config) deleted from projects/range/ranch/barn/shep/; toml run line invoked shep directly, bypassing shep-serve.sh self-heal bootstrap. Durable fix: config restored from mcp_config.json.bak-20260920 (33 servers, 0600), toml run -> shep-serve.sh (self-bootstraps from .dist + injects secrets from /home/toxic/.secrets). Self-heal PROVEN live (deleted config, restart recreated it 0600, health 200). Restarted via owned pitchfork sequence; verified: /proc exe canonical binary, :25127 listen, /health ok, MCP initialize+tools/list 200 (12 tools), herd :25100 200, coyote running; 3 stop/start cycles incl persistence'
owner: 'Vesper (Ember''s crew)'
status: 'DONE (2026-09-21) -- commits 408e4890f1 (KB register) + 7c1d8ae7ac (pitchfork.toml fix), origin/main = 7c1d8ae7ac verified via git ls-remote'
order: 93
registered: '2026-09-21'
updated: '2026-09-29'
---

# shep-repair

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
