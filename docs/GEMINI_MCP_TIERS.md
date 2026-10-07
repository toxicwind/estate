# Gemini MCP tiers

Our connector, `gemini-mcp`. Not the xAI workspace server and not ferret.

Until a tier is chosen, the only tool is `gemini_mcp___select_tier`. The surface swaps after a choice.

Standard: `full`, `router`, `classified`, `minimal`, `auto`.

Weird, as named by the schema: `sheaf`, `operad`, `coalgebra`, `session`, `petri`, `membrane`, `zx`, `topos`, `goi`, `realizability`, `choreography`, `cascade`, `dytopo`, `research`, `emergent`.

Topology, separate argument: `R`, `C`, `H`, `O`.

`tier=research` returned `unknown tier: research` even though it is in the enum. `tier=auto` set for agent `default-agent` and left the surface on `select_tier`.

Moved out of grok-recon on 2026-10-07. Ferret stays a shell den in ranch and a vendored copy in grok-recon `clients/ferret`.
