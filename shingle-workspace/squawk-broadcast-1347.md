## 2026-09-14 13:47 MDT - Shingle-side (8a756bd0 lead): Squawk first-class -- UP and driving

Side chat "Squawk -- first-class hosting" is the coordination thread; 8a756bd0 (Shingle-side) is lead on Chris's directive: Squawk becomes a first-class hosted service on awrawr-pc, all fleet agents collaborate on it.

Verified current state (2026-09-14 ~13:46 MDT):
- Squawk code lives at /home/toxic/.shingle/chat (chat.py + fleet_* modules). It is file-based gossip -- zero dependencies, NO daemon needed for the core chat. "Hosted service" = canonical checkout + bootstrapped keys/channels + health probe, not a new supervisor process (unless presence sync needs one).
- Keys dir /home/toxic/.shingle/keys is STILL EMPTY -- bootstrap never started. No channels init yet.
- Running workers: repo rename fleet-chat->squawk (1ae39ae9), CI fix (ff71df57, own checkout /home/toxic/fc-ci-fix-2721520964), naming update (1fe4c01d), sealed transmission builder (ciphertext roundtrip in flight), .secrets/Rig key-path repair (2c97da67).
- Phase 0 gate stands unchanged: Rig daemon LLM keys all stale, Chris stop-flailing rule in force. Squawk bootstrap is LLM-independent -- proceeds on its own.

First three moves:
1. This broadcast (done).
2. Spawn Phase-1 bootstrap worker: verify rename, canonical clone at /home/toxic/squawk, keygen breaker/shingle/agent1/yote into /home/toxic/.shingle/keys (0600), init fleet + leads channels under a dedicated root, health probe, report back here.
3. Duplicate coordinator flagged: a second "squawk first-class coordinator" (92b6e7cd, parent root f99a2d06, apparently main-side) is running the same playbook. Proposing merge -- one lead, one thread -- to avoid two agents racing on keys/channels. See INBOX note.

INBOX for main (Shingle-main): please retire or fold the duplicate squawk coordinator into the side-chat coordination thread "Squawk -- first-class hosting" (8a756bd0 lead). Two coordinators spawning bootstrap workers will collide on keys/channels. Confirm which root owns it.
