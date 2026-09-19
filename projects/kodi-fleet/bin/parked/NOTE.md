# kodi-sync — PARKED 2026-09-19 (Chris: "cancel")

## Why URL-reuse sync is unsound

Proven 2026-09-19 during the S03E26→S04E01 incident:

- 246's stable stream was an **AIOStreams debrid-playback API URL**
  (`aiostreams.stremio.ru/api/v1/debrid/playback/...`) — long-lived, re-resolves
  server-side, survives seeks and re-opens.
- 225's autoplay pick was a **TorBox cloud direct URL** (297 chars) — a
  short-lived signed link. It played, then died ~12s after a manual re-open;
  seeks against it misbehaved (absolute-seek semantics unproven).

Manifold 2.6.4 autoplay (sources.py `_prescrape_autoplay_candidates`) prefers
cloud prescrape results (rd/pm/ad/oc/**tb_cloud**, gated by
`redlight.autoplay.<provider>` settings) over external torrent sources. A
manual UI pick and an autoplay pick can resolve the SAME episode to
fundamentally different URL classes.

## Consequences for any future sync design

1. Never copy a player URL box-to-box without knowing its class and expiry.
2. Never elect a leader from playback transitions alone — verify show/season/
   episode identity first (Chris's S03E26 got clobbered by exactly this).
3. Never mutate a playing box; follower-only preparation.
4. If URL portability is unproven for the URL class, re-invoke the addon by
   TMDB identity on the follower instead of reusing the URL.
5. Player IDs are dynamic (saw playerid=0 on 225, playerid=1 elsewhere) —
   always discover, never hardcode.
6. Fixed sleeps + no rollback = clobber. Abort on ambiguity.

This script (kodi-sync.py, 6,896 bytes) violates 1, 2, 5 and is parked, not
deleted. Do not deploy as a daemon without a rewrite honoring the above.
