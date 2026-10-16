# mbx — default build dispatch skill

This skill documents the estate's default build path: `mise run <task>` /
`mise exec -- <cmd>` with `mbx-cache` (mise remote task cache, :25148).
The old `flicker` job daemon is retired; the skill directory keeps the
`flicker` name so agents searching the old name land on the redirect.

- `SKILL.md` — the dispatch doc (canonical).
- `prompt_context.md` — condensed prompt context (mirrors SKILL.md).
- `skill.toml` — skill metadata (`prompt_context` embedded).

Live facts: pitchfork daemon `estate/mbx-cache`, port `MBX_CACHE_PORT=25148`
(`config/ports.env`), launcher `ops/mbx-cache/run.sh`, client config
`mise/conf.d/15-remote-cache.toml`. KB §7 documents the retirement.
