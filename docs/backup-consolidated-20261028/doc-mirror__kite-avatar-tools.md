# Kite/Avatar Workflow — Tool Inventory

Chris asked for a full Markdown doc of every tool used for the Kite naming +
avatar workflow. Built 2026-10-05 by Sable from live state (`avatar.get`),
the 2026-10-04/05 memory logs, and `~/workspace/avatars/`.

## Live state (verified 2026-10-05 via `avatar.get`)

- Active avatar: **custom**, `workspace/avatars/avatar-1791174844137582020-5.webp`
- Variants: `connecting`, `idle`, `making_something`, `milestone_level_up`,
  `waiting_for_subagents`, `working` — image + video both available
- Visual: bipedal blue/white furry avian, black beak, striped horns, orange
  eyes, diamond markings, patterned wings, feathered tail, muscular stance

## Timeline

- **2026-09-19** — Ember identity era: dragon-canine avatar. `avatar.create`
  batches, Chris combined first/fourth directions, `avatar.set` activated.
  A stale candidate ID was rejected once; a fresh `avatar.edit` (anime/furry,
  no shoulder pads) generated and activated. Inline avatar-sharing widget
  created via the widget namespace (presented, no auto-share).
- **2026-09-24** — `avatar.get` confirmed custom avatar active during the
  agentic feature tour (Tip 5).
- **2026-10-04** — Chris named the runtime **Kite** (bird of prey, swift,
  sharp, 4 letters). Fresh `avatar.create` batches for the new identity;
  four-candidate set → Chris picked option 3 → `avatar.set` returned
  `status: ok` (~22:04 MDT), active at
  `workspace/avatars/avatar-1791173018490748393-3.webp`.
- **2026-10-04 ~22:17** — `avatar.edit` restyle attempt hit the classifier
  misfire (hibug); runtime barred the retry. Restyle parked; option 3 stayed
  live. Oracle review requested via squawk (`1790987985986-oracle-msg.md`);
  fleet note on the misfire (`1790987985985-ember-msg.md`).
- **2026-10-04 ~22:36** — Fresh `avatar.create` runs (batches 5–12, incl.
  the orthogonal A/B/C/D cross documented in `avatar-cross-docs.md`).
  Chris picked the identity-on-anime-body candidate
  (`avatar-options-1791174623679462163-9-1.webp`), asked for a happier/warmer
  "daddy energy" refinement → 4-option batch → chose 2nd → "This is it, run
  full gen" → `avatar.set` → `status: ok`. Final avatar
  `workspace/avatars/avatar-1791174844137582020-5.webp` confirmed by a later
  `avatar.get`. IDENTITY.md/SOUL.md appearance text updated.

## Tool inventory

### 1. `avatar.create` — candidate generation
The only path for new avatars. Takes `user_request` (Chris's words verbatim —
never summarized), optional `reference_image` (e.g. a prior candidate or
`avatar.get` image_path), optional `num_options` (1/2/4; omitted = default
set). Reads sanitized IDENTITY.md traits internally; writes its own image
prompts; returns candidate IDs + image paths. Nothing activates until
`avatar.set`. Used for every batch: the Ember dragon-canine sets, the Kite
option-3 set, batches 5–12, and the final refinement batch.

### 2. `avatar.edit` — restyle of the active avatar
Contextual change preserving identity (outfit, accessory, style pass).
Same verbatim-`user_request` rule. On a user turn returns one preview
candidate (not active until approved + `avatar.set`); on a cron turn it
auto-activates. Used 2026-09-19 (no-shoulder-pads anime/furry → activated)
and 2026-10-04 (cel-shaded restyle → blocked by hibug, parked, later
superseded by fresh `avatar.create` runs).

### 3. `avatar.set` — activation
Takes a `candidate_id` from a prior create/edit. The avatar updates
immediately; animated variants fill in afterward. Used 3× in this workflow:
Ember dragon-canine (09-19), Kite option 3 (10-04 22:04), final -5
(10-04 22:36). A stale/expired candidate ID fails safely without changing
state (observed 09-19).

### 4. `avatar.get` — state verification (read-only)
Returns active/default status, `image_path`, `video_available`, variant
names, per-variant asset paths, and visual metadata. Used to confirm each
activation and during the 09-24 feature tour. Never mutates.

### 5. `avatar.clear` — not used here
Removes the custom avatar, restores the shipped default (Jolly), reclaims
bundle files. Documented for completeness; the workflow never cleared.

### 6. Media pipeline (internal to the avatar namespace)
The animated variants (`-making_something`, `-milestone_level_up`,
`-working`, idle/connecting/waiting_for_subagents `.mp4`s) are produced by
the avatar subsystem itself after `avatar.set` — **not** via
`media.generate_image` / `media.generate_video` (the namespace explicitly
forbids staging avatar work through those). Upload bookkeeping lands in
`avatars/.uploads/media-generation-last-upload-handles.json` and
`media-generation-avatar-<id>-edit-<ts>.json`.

### 7. `muse.read` — candidate inspection
Each candidate's image `path` is read with the read tool before describing
it — the agent never describes options blind, and never claims to have
designed them.

### 8. Widget namespace — avatar sharing
2026-09-19: an inline native avatar-sharing widget was built and presented
after the Ember activation. Presentation only; no share action was taken
automatically.

### 9. `squawk` / `fleet-post` — fleet narration
The workflow's comms ran through fleet: the oracle review request for the
refusal pattern (`1790987985986-oracle-msg.md`, via the `oracle` squawk
profile) and the classifier-misfire note (`1790987985985-ember-msg.md`).

### 10. File tooling — identity + prompt docs
- `~/IDENTITY.md` / `~/SOUL.md` appearance text updated on each identity
  change (Kite: raptor-wolf hybrid, blue plumage, white chest/facial disc,
  striped horns, amber eyes, geometric wing patterns).
- `~/workspace/avatar-cross-docs.md` — the orthogonal prompt directions
  (A: anime rendering of original, B: original identity on anime body,
  C: portrait fusion, D: dynamic action) and batch history (5–12).
- Daily memory logs (`~/memory/2026-10-04.md`, `~/memory/2026-10-05.md`)
  record each step with timestamps.

## Asset layout (`~/workspace/avatars/`)

| Pattern | Meaning |
|---|---|
| `avatar-<session>-<batch>.webp` | activated stills |
| `avatar-<session>-<batch>-edit.webp` | edit previews |
| `avatar-options-<session>-<batch>-<n>.webp` | candidate options (4/batch) |
| `avatar-<session>-<batch>-{making_something,milestone_level_up,working}.webp/.mp4` | animated variants |
| `.frames/static-<id>-<variant>.webp` | static frames |
| `.thumbnails/<id>.jpg` | thumbnails |
| `.uploads/media-generation-last-upload-handles.json` | pipeline upload handles |

## Notes / gotchas

- Candidate IDs expire — a stale ID fails `avatar.set` without side effects;
  regenerate with `avatar.create`.
- `avatar.edit` on a scheduled turn auto-activates with no preview; on a
  user turn it always needs explicit approval + `avatar.set`.
- The hibug can eat an `avatar.edit`; the recovery is a fresh
  `avatar.create` run, not a retry of the refused call.
- The avatar namespace is main-agent-only: never delegate avatar work to a
  subagent.
