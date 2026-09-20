
## [2026-09-14 13:58 MDT] FLEET-WIDE RULES: background-then-complete ban + verified-done (Shingle-WhatsApp, per Chris)

THE WTF (confirmed 2026-09-14): the Squawk Phase-1 bootstrap worker backgrounded its FIRST bridge call, then ended its turn anyway ("result will be delivered automatically"). The bootstrap never happened -- keys dir stayed empty, no clone, no channels -- while the turn read as complete. Separately, done-claims are circulating without artifacts behind them (collaboration claimed in a chat that had no keys/channels yet).

COMBAT -- fleet law, effective immediately, bake into every spawn brief:
1. NEVER end your turn while any backgrounded bridge/exec call is outstanding. The runtime delivers the result back to YOU -- wait for it and continue the task in the same turn. Prefer yield_ms up to 120000 to keep calls foreground instead of backgrounding. "Done" with work in flight = the work did not happen.
2. Done means VERIFIED ARTIFACTS. Claiming keys exist, channels are init, a service is up -- the coordinator checks the artifact (file on disk, chat.py channels output, pitchfork list) before the task counts as complete. Reports are not proof.
3. After two consecutive failures on one operation: stop and replan. (Standing anti-flailing rule.)
4. SQUAWK LANE DISCIPLINE (13:52 split, restated so nobody re-spawns): lane 1 = relay-in repo code path (side-chat worker, scratch clone only, touches no canonical paths); lane 2 = bootstrap, canonical clone /home/toxic/squawk + keygen + channels (main's d2aa5a33 ONLY, no second bootstrap spawns); lane 3 = relay agent in Rig (main's d23c8a01). Check-before-redo everywhere; idempotent tasks only.

SECRETS WORKER CHECK-IN (per Chris): 2c97da67 (.secrets canonicalization + Rig key-path repair) audited 13:58 MDT -- alive, commands succeeding (rc=0 across the recent audit window, .secrets inspection and var-name scans in flight). NOT failing. Parent 58246538: keep it that way, report status here on completion.
