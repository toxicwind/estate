# Kite/Avatar Workflow — Full Tool Guide

_Built 2026-10-05 from live state (`avatar.get`), the 2026-10-04/05 memory logs,
`~/workspace/kite-avatar-tools.md`, `~/workspace/kite-tools/kite-tools.md`,
`~/workspace/avatar-cross-docs.md`, and `~/workspace/avatars/`. Chris asked for a
full Markdown doc of every tool used for the Kite/avatar workflow — this is it._

## The workflow in one paragraph

Chris renamed the runtime **Kite** on 2026-10-04 (`onboarding.update_identity`).
Fresh `avatar.create` batches generated the new identity's candidates; he picked
option 3 and `avatar.set` activated it (~22:04 MDT). A cel-shaded `avatar.edit`
restyle hit the classifier misfire (hibug) and was parked. More `avatar.create`
batches (5–12, including the orthogonal A/B/C/D cross) produced the anime
raptor-wolf; Chris picked the identity-on-anime-body candidate, asked for a
happier/warmer refinement, chose the 2nd of the refinement batch, said "This is
it, run full gen," and `avatar.set` activated the final avatar (~22:36 MDT):
`workspace/avatars/avatar-1791174844137582020-5.webp` with 6 animated variants.
Identity text in `IDENTITY.md`/`SOUL.md` was updated to match. The whole thing
was narrated in fleet via squawk.

## Phase 1 — Rename (2026-10-04)

### `onboarding.create_name_widget` → `onboarding.update_identity`
- **Purpose:** persist the assistant name Chris chose.
- **Order:** the name-picker UI ran first (Chris used it to pick); `update_identity`
  was called with `name="Kite"` after he chose it.
- **Input:** `name="Kite"` — Chris's exact words ("Kite", bird of prey: swift,
  sharp, 4 letters, easy to type).
- **Output:** `~/IDENTITY.md` updated; the name live in chat, squawk, and all
  agent briefs.
- **Note:** this is the only name-change tool in the workflow; everything avatar
  after it builds the visual identity for the name.

## Phase 2 — Candidate generation (`avatar.create`)

### `avatar.create` — the only path for new avatars
- **Purpose:** generate candidate avatar images from a text direction.
- **Input:** `user_request` (Chris's words verbatim — never summarized by the
  agent), optional `reference_image` (a prior candidate or the `avatar.get`
  image_path), optional `num_options` (1/2/4; omitted = default set). The tool
  reads sanitized `IDENTITY.md` traits internally and writes its own image
  prompts.
- **Output:** candidate IDs + image paths under `workspace/avatars/`
  (`avatar-options-<session>-<batch>-<n>.webp`). **Nothing activates until
  `avatar.set`.**
- **How it was used, in order:**
  1. **Ember era (2026-09-19):** batches for the dragon-canine avatar. Chris
     combined the first and fourth directions.
  2. **Kite option-3 set (2026-10-04):** fresh 4-candidate set for the Kite
     identity → `avatar-options-1791172922232319054-3-{1,2,3,4}.webp`. Chris
     picked **option 3**.
  3. **Batches 5–12 (2026-10-04, post-hibug):** cel-shaded raptor-wolf
     exploration. Batch 5 (1980s retro hand-drawn cel, superseded), batch 6
     (3D cel-shaded anime raptor-wolf — option 3 loved), batch 7 (single-prompt
     cross, converged, discarded), batches 8–11: the **orthogonal A/B/C/D
     cross** (documented in `~/workspace/avatar-cross-docs.md`):
     - **A** — anime rendering of the original (same design, anime style)
     - **B** — original identity on the anime body (the winner's direction)
     - **C** — close-up portrait fusion
     - **D** — dynamic action, mid-leap
     Chris picked the first candidate of direction B
     (`avatar-options-1791174623679462163-9-1.webp`), asked for a happier,
     warmer "daddy energy" refinement → 4-option refinement batch → chose the
     **2nd** → "This is it, run full gen."

### `muse.read` — candidate inspection
- **Purpose:** look at each candidate before describing it.
- **Rule:** the agent reads every candidate's image `path` with the read tool —
  never describes options blind, never claims to have designed them.

## Phase 3 — Activation (`avatar.set` + `avatar.get`)

### `avatar.set` — activation
- **Purpose:** make a candidate the live avatar.
- **Input:** `candidate_id` from a prior create/edit.
- **Output:** the avatar updates immediately; animated variants fill in
  afterward. Returns `status: ok`.
- **Used 3× in this workflow:**
  1. Ember dragon-canine (2026-09-19)
  2. Kite option 3 (2026-10-04 ~22:04 MDT) →
     `workspace/avatars/avatar-1791173018490748393-3.webp`
  3. Final -5 (2026-10-04 ~22:36 MDT) →
     `workspace/avatars/avatar-1791174844137582020-5.webp`
- **Gotcha:** a stale/expired candidate ID fails safely without changing state
  (observed 2026-09-19) — regenerate with `avatar.create`.

### `avatar.get` — state verification (read-only, never mutates)
- **Purpose:** confirm what is actually live.
- **Output:** active/default status, `image_path`, `video_available`, variant
  names, per-variant asset paths, visual metadata.
- **Used to:** confirm each activation (09-19, 10-04 22:04, 10-04 22:36),
  during the 09-24 agentic feature tour (Tip 5), and on 2026-10-05 to verify
  the final avatar is live.

## Phase 4 — The blocked restyle (`avatar.edit` + hibug)

### `avatar.edit` — restyle of the active avatar
- **Purpose:** contextual change preserving identity (outfit, accessory, style
  pass). Same verbatim-`user_request` rule as create.
- **Behavior:** on a user turn it returns one preview candidate (not active
  until approved + `avatar.set`); on a cron/scheduled turn it auto-activates.
- **Used 2026-09-19:** no-shoulder-pads anime/furry edit → generated and
  activated.
- **Used 2026-10-04 ~22:17:** Chris requested the cel-shaded correction (remove
  synthetic toy/nylon/grid qualities; organic avian raptor, chalk-white front
  plumage, midnight-navy/charcoal wings, bold hand-inked lines, flat matte
  colors, hard-edged 1980s cel shadows). The call hit the classifier misfire
  (hibug); the runtime barred the retry. No candidate was produced, no avatar
  state changed. **The restyle was parked.**
- **Recovery (the lesson):** the hibug eats an `avatar.edit`; the recovery is a
  **fresh `avatar.create` run, not a retry of the refused call.** That's exactly
  what happened — batches 5–12 superseded the parked edit ~20 minutes later.

### `avatar.clear` — not used here
- Removes the custom avatar, restores the shipped default (Jolly), reclaims
  bundle files. Documented for completeness; the workflow never cleared.

## Phase 5 — Variant pipeline (internal to the avatar namespace)

The 6 animated variants are produced by the avatar subsystem itself **after**
`avatar.set` — **not** via `media.generate_image` / `media.generate_video`
(the namespace explicitly forbids staging avatar work through those).

Final avatar variants (all present in `~/workspace/avatars/`):
`connecting`, `idle`, `making_something`, `milestone_level_up`,
`waiting_for_subagents`, `working` — image + video (`.webp` + `.mp4`).

Upload bookkeeping lands in:
- `avatars/.uploads/media-generation-last-upload-handles.json`
- `media-generation-avatar-<id>-edit-<ts>.json`

## Phase 6 — Identity text (file tools)

`~/IDENTITY.md` / `~/SOUL.md` appearance text was updated on each identity
change to match the selected avatar. Final (2026-10-04 22:36): raptor-wolf
hybrid — bright blue plumage, stark white feathered chest and facial disc,
striped horns sweeping back, warm amber eyes, happy expression, red/yellow/
black geometric wing patterns, diamond markings on face and arms, taloned
hands and feet.

## Phase 7 — Fleet narration (`squawk` / `fleet-post`)

The workflow's comms ran through fleet:
- Oracle review request for the benign-input refusal pattern:
  `1790987985986-oracle-msg.md` (via the `oracle` squawk profile)
- Classifier-misfire note: `1790987985985-ember-msg.md`

## Phase 8 — Sharing (widget namespace)

### `widget.create` + `widget.present`
- **2026-09-19:** an inline native avatar-sharing widget was built and presented
  after the Ember activation (widget ID `widget-d45096ac-4017-4c02-882d-0d91df08e62d`).
- Presentation only; no share action was taken automatically.

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

## Complete order of operations

```
onboarding.create_name_widget (name picker)
  → onboarding.update_identity (Ember → Kite)
    → avatar.create (Kite option-3 set, 4 candidates)
      → muse.read (inspect candidates)
        → avatar.set (option 3, 22:04 MDT) → avatar.get (confirm)
          → avatar.edit (cel-shaded restyle → hibug, parked)
            → avatar.create (batches 5–12, A/B/C/D cross)
              → muse.read (inspect)
                → avatar.create (refinement batch, 4 options)
                  → avatar.set (final -5, 22:36 MDT) → avatar.get (confirm)
                    → variant pipeline (6 animated variants)
                      → file edits (IDENTITY.md/SOUL.md appearance text)
                        → squawk/fleet-post (oracle review + hibug note)
```

## Gotchas

1. **Candidate IDs expire** — a stale ID fails `avatar.set` without side effects;
   regenerate with `avatar.create`.
2. **`avatar.edit` on a scheduled turn auto-activates with no preview**; on a
   user turn it always needs explicit approval + `avatar.set`.
3. **The hibug can eat an `avatar.edit`** — recovery is a fresh `avatar.create`,
   never a retry of the refused call.
4. **The avatar namespace is main-agent-only** — never delegate avatar work to
   a subagent.
5. **Never stage avatar work through `media.*`** — variants come from the avatar
   subsystem's own pipeline after `avatar.set`.
6. **Chris's words go into `user_request` verbatim** — never summarized.
