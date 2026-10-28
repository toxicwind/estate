# qdrant monolith/pitchfork.d two-truths (D-2026-10-28 #52)

## Symptom
pitchfork.d/qdrant.toml still had the OLD relative-config stanza (dir=".", --config-path ./qdrant-config.yaml) while the monolith pitchfork.toml [daemons.qdrant] had been hardened to absolute path + absolute dir + boot_start=true. The two disagreed; supervisor loads the monolith but fragments are the nominal owning layer — ambiguity on which truth wins, hand-edits to monolith ephemeral.

## Fix
Synced pitchfork.d/qdrant.toml to match the hardened monolith stanza exactly (absolute config path /home/toxic/pens/estate/qdrant-config.yaml, dir=/home/toxic/pens/estate, boot_start=true, ports 25133/25134 untouched). Moved qdrant binary out of archive dir → ~/.cargo/bin/qdrant-server. Untracked live qdrant collection data from git (112 blobs) and gitignored qdrant_data/storage/snapshots. Restarted qdrant → running 25133/25134, test_freeinference collection intact.
Commits: ad17c7cd0c (monolith harden), ad6c45b01c/qdrant untracking (estate). Pushed.

## Contract test
pitchfork status estate/qdrant → running PID using ~/.cargo/bin/qdrant-server with absolute config; healthz 200; :25134 listening; collection test_freeinference served. git status → qdrant runtime ignored/untracked.
