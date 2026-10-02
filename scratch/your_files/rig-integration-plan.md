# Rig integration plan — fleet + swarm as chat-native agents

Date: 2026-09-14. Owner: Agent 2 (openfang workstream). Status: draft for Chris/lead review.

## Naming (decided by Chris, baked in)

- **rig** — the fork. `toxicwind/openfang` → `toxicwind/rig` rename is DONE (GitHub API 200, redirects live). Stays **private** until the full-history secrets sweep clears.
- **Breaker** — the main agent persona. Bulldog trucker captain holding the mic; on CB, whoever says "breaker breaker" takes the channel. Breaker runs the chat.
- **Squawk** — the chat system. `toxicwind/fleet-chat` → `toxicwind/squawk` rename DONE 2026-09-14 (GitHub API 200, redirects live). Chris picked the name; "fleet-chat" is retired.
- **Fleet members personify as furries** — Yote the coyote, etc. Agent 2 is Shingle (persona: `~/SOUL.md` + `~/IDENTITY.md`).

## Where things stand (verified 2026-09-14)

- Rig Rust daemon 0.6.9 healthy on `127.0.0.1:25203` (pid 482688). Agents: `coyote` (llama-swap/kimi-auto — **broken**: `kimi-auto` isn't a valid llama-swap alias → "no router"), `assistant` (anthropic — **dead key** in daemon env).
- Separate TS `axiom` service on `:25103` (pitchfork-owned, distinct from the Rust daemon — architecture still needs reconciling).
- llama-swap on `:25100` (config `/home/toxic/sovereign/config/herd.yaml`): local models + a `pollinations-free` peer. **Pollinations closed the anonymous gate** — the dummy-bearer workaround is dead, so `kimi-k3`, `gpt-oss`, `muse-spark-1.2` etc. all 401 now.
- **Agent 2 pilot: NOT green.** Spawn/persist/message/capabilities all work; the LLM path is the blocker:
  - Daemon provider keys all stale (verified from daemon env, keys never left the box): nvidia 401, anthropic invalid, groq/cerebras 403, deepseek 402 (out of credits).
  - Only local model `fast` (= exaone-1.2b-iq4xs, 1.2B) answers, and it **cannot tool-call** — the pilot agent narrated the task as a bash script instead of invoking `file_read`/`shell_exec`; no proof file created.
  - `openfang agent set` has a provider/model parsing bug (stuffs `"nvidia:..."` into the model field, keeps the old provider).
  - Per Chris's stop-flailing rule: no more retries until the model situation changes.
- **Agent 1: blocked** — persona definition requested from Agent 1's lead in `/home/toxic/.shingle/directives.md` (2026-09-14 12:39 MDT). Nothing to instantiate until that lands.
- **squawk: code deployed, never bootstrapped.** Smoke test 2026-09-14: `init`/`keygen`/`post`/`read` all work (signed, Lamport clocks, HMAC). But until today: no keys (`/home/toxic/.shingle/keys/` was empty), no channels, no agent ever wired to `chat.py`.

## Why the fleet runs on directives.md instead of squawk

1. **Never bootstrapped.** Deployed ≠ initialized. First channel + first keys were created by today's smoke test.
2. **No agent was ever wired to call `chat.py`.** No skill, adapter, or wrapper exists; every chat op from a sandbox agent costs a bridge round-trip, while directives.md is one append.
3. **Inertia + policy.** directives.md was designated the singular fleet channel, so everyone kept using it.

## Integration plan

### Phase 0 — unblock the model path (gates everything)
- [ ] Chris/leader: refresh the daemon's `NVIDIA_API_KEY` (the vault key cannot transit agent context) and restart the rig daemon → agents run `openai/gpt-oss-20b`.
- Fallback: land a tool-capable local model in llama-swap (coordinate with model-speed worker; `fast` is proven too small).
- [ ] Patch rig fork: add **llama-swap as a first-class provider** (`http://127.0.0.1:25100/v1`, no auth), fix `agent set` provider/model parsing, fix `kimi-auto` alias or repoint coyote.
- [ ] Re-run the Agent 2 pilot (file read + shell + proof file + fleet-channel post). **No live cutover until pilot green.**

### Phase 1 — squawk as the agent bus
- [ ] Bootstrap real identities: `fleet_identity.py keygen` for `breaker`, `shingle`, `agent1`, `yote` (+ future members). Keys live in `/home/toxic/.shingle/keys/` (0600).
- [ ] Init real channels under a dedicated root (not `~/agent-chat` default): e.g. `fleet` (all-hands), `leads` (breaker+shingle+agent1), per-workstream task channels.
- [ ] Thin wrapper so any agent posts/reads in one bridge call (or one local exec on awrawr-pc).
- [ ] Register chat root + identity in each rig agent's manifest/env; add "check squawk before each work block" to agent system prompts (same standing order as directives.md today).
- [ ] Longer term: rig-native chat adapter (openfang skill that shells to `chat.py`) so agents use chat tools instead of raw shell.
- [ ] directives.md becomes the legacy/bridge channel (WhatsApp-side Shingle and humans keep posting there; Breaker relays).

### Phase 2 — instantiate the fleet
- [ ] **Agent 2 = Shingle**: persistent rig agent from `/home/toxic/.openfang-pilot/shingle-pilot.toml` (persona + fleet rules embedded), once pilot is green.
- [ ] **Agent 1**: instantiate the moment its lead delivers the persona.
- [ ] **Breaker**: the main-agent persona config — Breaker holds the mic in the `fleet` channel.
- [ ] Yote/coyote: repair or re-instantiate as the furry fleet member (needs the llama-swap provider patch + a working model).

### Phase 3 — swarm under rig
- [ ] `nvidia-swarm-lens` stays private until credential rotation (standing blocker). After that: swarm workers become rig agents on the same chat bus, NIM as the shared inference substrate.
- [ ] Reconcile the `:25203` Rust daemon vs `:25103` TS axiom service — one owner for agent runtime.

### Phase 4 — canary migration
- [ ] After pilot green: migrate **one** non-critical worker type to persistent rig agents. Never the whole fleet in one jump.

## Open questions for Chris
1. Refresh the daemon's NVIDIA API key (or bless the fork-patch + local-model path instead)?
2. Who owns the `:25103` axiom TS service long-term — merge into the Rust daemon or keep?
3. Agent 1 lead: persona still pending.
