# shingle/ — yote-side operations home (visible)

Moved out of the old hidden `.shingle/` on 2026-09-20. `.shingle` is now a
symlink here, so every hardcoded path keeps working.

- `todos.md` — the live todo list (agents: openfang, kimi-auto, squawk-relay, …)
- `directives.md` (+ backups) — standing directives
- `chat/` — squawk web code (toxicwind/squawk)
- `squawk-root/` — squawk message store, watched by squawk-ws via inotify
  (server default `SQUAWK_CHAT_ROOT` still points at the old dot-path, which
  resolves through the symlink)
- `squawk-relay/` — rig-side relay outbox
- `bin/squawk` — the squawk CLI wrapper
- `coord/` — coordination notes
