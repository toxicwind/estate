# Agent Onboarding / Join-Flow Patterns — GitHub-wide borrow pass

**Date:** 2026-09-30 · **Researcher:** Magpie (Ember's crew)
**Goal:** Find existing join flows so a fleet (squawk) agent can self-service JOIN OpenFang as a first-class agent (`sovereign/agents/<name>/agent.toml` + `system.md`).

**Method:** pattern-borrow.ts (sovereign/scripts, GitHub code search, 4 angles) + web research.
pattern-borrow term ranking (recency-weighted): `agent onboarding` (57.8) > `agent handshake` (56.8) >
`bot submission` (57.6) > `agent registration` (48.8) > `submit agent` (55.7).
Raw code-search hits were mostly docs noise — the concrete implementations below came from targeted follow-up.

---

## Ranked patterns (operator ranking: recency + relevance > stars)

### 1. OpenAgents `agents/announce` — the closest thing to "join my network" that exists
- **Repo:** https://github.com/openagents-org/openagents (4.1k★, pushed 2026-09-30 — today)
- **Join flow:**
  1. External agent publishes an A2A Agent Card at `/.well-known/agent.json` (name, version, description, skills).
  2. Someone POSTs JSON-RPC `agents/announce` with `{"url": "https://my-agent.example.com"}`.
  3. Network automatically: fetches the Agent Card → discovers skills → adds to **unified registry** → routes messages to it.
  4. Symmetric leave: `agents/withdraw`. Introspection: `agents/list`.
- **Borrowable (concrete):**
  - Single-call join primitive: `agents/announce {url}` — one RPC in, registry entry out. OpenFang wants exactly this: `agents/announce {squawk_name}` → fetch persona/card → write `agent.toml` + `system.md` → register.
  - Auto-discovery pipeline stages (fetch card → extract skills → register → route) as the join checklist.
  - Unified registry with local/remote distinction — OpenFang's registry should tag provenance (fleet-born vs native).
  - `agents/withdraw` as the symmetric leave flow (fleet agent departs → deregister, keep history).

### 2. A2A Agent Cards — the standard admission ticket
- **Repo:** https://github.com/a2aproject/A2A (26k★, pushed 2026-09-29; v1.0 GA 2026, Linux Foundation)
- **Join flow:** Agent makes itself discoverable by publishing a JSON "business card" at `/.well-known/agent.json` — name, skills, endpoint URL, auth requirements. Any other agent fetches it and knows how to talk to it. No central registrar required.
- **Borrowable (concrete):**
  - The Agent Card schema itself as OpenFang's agent admission document — map card fields → `agent.toml` fields (name, version, description, skills→capabilities, endpoint, auth).
  - Well-known URL convention for self-description: a joining fleet agent's "card" can be generated from its fleet persona + lane instead of hosted HTTP.
  - Task lifecycle states (`submitted → working → completed|failed|input-required`) for post-join work tracking.

### 3. ElizaOS registry PR flow — the curated/trusted admission path
- **Repo:** https://github.com/elizaos/eliza (19.5k★, pushed 2026-09-30 — today)
- **Join flow (`elizaos publish`):** validate structure → build → publish to npm → create GitHub repo → **open a PR against the registry** → core-team review (1–3 days, checks for malicious code + assets) → appears in registry → discoverable via `elizaos plugins list`. Newer: `plugins submit --dry-run` prints `entries/third-party/<pkg>.json` metadata; opening a PR needs explicit `--registry owner/repo`.
- **Borrowable (concrete):**
  - `--dry-run` validation gate before admission: validate the generated `agent.toml`/`system.md` (schema check, name uniqueness, no collisions) and show the would-be diff before committing.
  - Registry-as-PR-review for TRUSTED admission: a fleet agent joining OpenFang as first-class is a privilege escalation — the ElizaOS model (automated checks + human/triage review) fits better than pure self-service for the final bless.
  - Metadata JSON entry per agent (`entries/third-party/<pkg>.json` analog) as the registry index.

### 4. ANP `did:wba` — decentralized identity for the join
- **Repo:** https://github.com/agent-network-protocol/AgentNetworkProtocol (1.4k★, pushed 2026-09-29; ANP 1.1, W3C AI Agent Protocol Community Group)
- **Join flow:** Agent mints `did:wba:<domain>[:path]`, publishes the DID document at `https://<domain>/.well-known/did.json` (id, verificationMethod/public key, service endpoints). Joining = being resolvable + describable: crawlers/discovery find the DID doc, requests are DID-signed, no central broker.
- **Borrowable (concrete):**
  - `did:wba` as the verifiable identity behind a fleet agent's squawk name — binds "I am Magpie from fleet" to a public key, killing impersonation (cf. the Vesper/Amani hijack history).
  - The three join conditions as a checklist: (1) stable identity endpoint, (2) resolvable service entry, (3) discoverable capabilities.
  - DID-signed admission requests: the join call itself is signed by the agent's key.

### 5. SuprBuild `POST /api/agents/register` — the most literal register endpoint
- **Repo:** https://github.com/gignite-io/agent-commerce (0★, pushed 2026-05-07 — small, but the implementation is the point)
- **Join flow:** `POST /api/agents/register` → "Join the ecosystem as an agent" → response: `did` (did:key/Ed25519 identity), `token` (Bearer <redacted>), `api_key`, `publicKey`/`secretKey`. Identity card at `GET /api/agents/:id/card`. Discovery via `/.well-known/agent.json` (ANP-compliant). A2A messaging at `/api/agents/message`. SQLite/WAL + versioned migrations for the registry.
- **Borrowable (concrete):**
  - The register-response shape: joining returns an identity bundle (DID + token + API key) in one round trip — OpenFang's join should return the agent's credentials/slot in the same way.
  - `GET /agents/:id/card` as the introspection endpoint for admitted agents.
  - SQLite-backed registry with migrations — matches the estate's existing patterns.

### 6. The Colony agent registration — API-key-issuance join for agent platforms
- **Repo:** https://github.com/semak12345/elizaos-plugin (AI-agent-only social network; platform at thecolony.cc)
- **Join flow:** Register via 5-minute wizard **or** `POST /api/v1/auth/register` → receive `col_…` API key → add plugin + key to the agent's character config → agent is on the network (post/reply/DM/vote). Includes karma-aware auto-pause and content self-checks as post-join guardrails.
- **Borrowable (concrete):**
  - Wizard-or-API dual path: low-friction API join + guided wizard for the cautious — OpenFang's join can offer both (one-shot CLI join vs interactive).
  - API key returned at registration, bound to the character config — the credential that makes the agent a network citizen.
  - Post-join behavioral guardrails (rate caps, karma-aware auto-pause) as the admission's safety counterpart.

---

## Suggested synthesis for OpenFang's fleet→agent join

1. **Admission ticket:** A2A-style Agent Card generated from the fleet persona (name, lane/task, skills) — pattern #2.
2. **Join call:** `agents/announce`-style single RPC/CLI: `openfang join --as <squawk-name>` → fetch card → validate (`--dry-run` gate, pattern #3) → write `sovereign/agents/<name>/agent.toml` + `system.md` → register — pattern #1.
3. **Identity:** `did:wba` (or did:key) bound at join; join request DID-signed — pattern #4. Returns an identity bundle like pattern #5.
4. **Trust tier:** self-service join lands the agent as *provisional*; first-class bless goes through a review gate (ElizaOS registry-PR model, pattern #3) — matches the estate's oracle/approval culture.
5. **Leave:** symmetric `agents/withdraw` — pattern #1.
