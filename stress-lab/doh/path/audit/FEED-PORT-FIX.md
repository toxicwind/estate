# squawk-feed port fix — root cause, deployed, git blocked

## Root cause (proven)
squawk_feed.py hardcoded `--port default=25131`, ignoring `SQUAWK_FEED_PORT=25135`
that pitchfork injects (ranch/squawk pitchfork.d/squawk-feed.toml, registered 2026-10-22).
Consequence: the feed bound SOV_GHAS's `:25131`, left `:25135` (its canonical port) refused,
so squawk-ui (`:25136`) proxy to `:25135` 500'd HTML -> no `/fleet/health` JSON ->
tunnel-monitor.sh never saw `cell_primary` -> cell ssh(:22)/kite-connector(:18301) listeners
never restored -> kite cell appeared/audits unreachable.

## Fix (deployed live)
`squawk_feed.py:409` now: `--port default = int(os.environ["SQUAWK_FEED_PORT"], "25135")`.
Pitchfork `squawk-feed` restarted -> process binds `:25135` (pid 657213), releases `:25131`.

## Verified post-fix
- `:25135 /squawk-feed/ping` -> 200 `{"seq":...}` (public, no auth)
- `:25135 /squawk-feed/seq` -> 200
- `:25136 /fleet/ping` -> 200 (UI proxy works)
- `:25136 /fleet/health` -> clean 404 (tunnel DOWN, feed reachable) — was 500-HTML before
(fix (a) of CELL-UNREACHABLE-DIAGNOSIS.md is DONE).

## Git landpath blocked (pre-existing, owned by another writer)
delendai reference-transaction hook is broken: `Module not found
ranch/borrowed/delendai/packages/cli/src/index.ts` aborts ANY branch/commit creation in
the squawk repo. Same guard board flagged for corral/tau (repaired there); squawk's
borrowed/delendai copy is stale. The squawk working tree also carries 100+ uncommitted
files from the in-flight fleet/market migration (not mine). Per one-writer + additive-only
I will not patch borrowed/delendai or sweep the tree. The code fix is live; the git
checkpoint needs the guard repair (repair borrowed/delendai symlink -> corral build, then
`delendai work publish` the squawk_feed.py change).
