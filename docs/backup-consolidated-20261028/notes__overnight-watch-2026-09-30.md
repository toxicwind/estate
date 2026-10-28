# Overnight watch 2026-09-30 — Grackle-II probe log

## 06:42 MDT probe — serve layer all green
- yote-conn bridge exec: OK (up 1d 3h, load 4.66/16 cores)
- squawk ws :25147 / feed :25135: alive, fleet traffic flowing
  (ferrous-warden drift alerts, Kestrel doc review, Waxwing provider sweep, Forge, Warden)
- pitchfork: all daemons running EXCEPT sovereign/redis (stopped),
  bidder-forge and bidder-scout (stopped)
- herd :25100 /v1/models: OK (model list served)
- sovereign router :25104 /health: ok, v3.2 hybrid
- keypool :25109 /health: ok (openrouter-free 2/2 healthy, gemini 7/7 healthy)
- model-guard :25101 /health: 200
- browserless CDP :9223 /json/version: Chrome/148 OK
- noVNC :6080: 200; Xvnc :99 + websockify running
- GPU RTX 3090: 32% util, 10496/24576 MiB, 33C
- disk 75% (928G total, 236G free); mem 28/62G used
- KB: registered docs/fleet/crews/grackle-ii.md; rollup 114 crews
- KB + fleet-knowledgebase served from origin/main (checkout on main)

## ANOMALY 1 — /home/toxic/.secrets line 210 syntax error (NEEDS Chris)
- Every pitchfork invocation prints:
  `/home/toxic/.secrets: line 210: syntax error near unexpected token '('`
- Line 210 is MOONBOX_DRIVE9_TOKEN, appended by the moonbox-live
  ingestion 2026-09-30 ~06:35 local; the value holds an unquoted paren
  pair and a space, so bash aborts sourcing at line 210.
- Consequence: 27 variables on lines 211-265 never load into any
  pitchfork-built environment, including GOOGLE_API_KEY,
  MOONBOX_GITHUB_PAT_MAIN, MOONBOX_GITHUB_PAT_PUSH,
  MOONBOX_TAILSCALE_AUTHKEY, MOONBOX_VNC_PASSWORD.
- Latent, not live: every current daemon started 2026-09-29
  (before the corruption) and still holds its pre-corruption env.
  Any daemon RESTART via pitchfork after 06:35 launches with those
  envs missing — including gatehouse-serve.sh, which sources .secrets
  at daemon start.
- Repair is one line: quote the value on line 210. The file is
  credential-shaped, so I did NOT touch it — Chris's call.
- Follow-up for main Ember: the moonbox-live ingestion script appends
  raw unquoted values to .secrets; the next ingestion will re-corrupt
  the file the same way. Root-cause fix belongs in the ingestion writer.

## ANOMALY 2 — sovereign/redis stopped
- valkey-server :25199 got SIGTERM 03:32:36 UTC ("user requested
  shutdown"); pitchfork shows it stopped, no auto-restart observed.
- No live project source references :25199/$REDIS_PORT except the
  pitchfork.toml daemon manifest itself — nothing on the estate is
  currently broken for lack of it. Flagging for the brief in case a
  consumer expects it.

## ANOMALY 3 — cell /tmp full (512M tmpfs)
- 100% full on the cell; my first crew-file write failed on it and one
  yote-conn exec output spill failed with ENOSPC. Cell-side cleanup
  needed — main Ember's lane, not yote's.

## Still open at handoff
- redis + bidder-forge/bidder-scout stopped (low impact, logged)
- .secrets line 210 quoting (Chris)
- morning-brief cron fires ~09:11 MDT; watch continues until then
