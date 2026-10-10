# tack vs roost — compare + merge recommendation (2026-10-02)

Author: Quill (Ember's crew) — read-only analysis, no merge executed.
Question from Chris: "Compare and merge tack and roost into flock?"

## Verdict: YES — merge, and it's mostly a deletion

**roost is already inside flock** (`flock/roost/`). The merge is: **delete the
duplicate `ranch/tack/` and repoint tau's one consumer at `@ranch/roost`.**
No code needs to move into flock — it's already there.

The rename Chris is asking about **already happened once**: on 2026-09-30,
commit `5d75050 "flock: rename Tack to Roost, nest as flock/roost/"` renamed
Tack → Roost and nested it under flock. The next day (2026-10-01), commit
`79a7a78 "feat(tack): sovereign provider wire-data authority (36 providers)"`
re-created `ranch/tack/` as a fresh duplicate. That directory is the entire
problem. Everything below is the evidence.

## The numbers

| | tack (`ranch/tack/`) | roost (`flock/roost/`) |
|---|---|---|
| providers | **36** | **75** |
| schema fields | 5 (`name, keyEnv, keyEnvAlt?, auth?, baseUrl?`) | 16 (`name, displayName?, baseUrl, keyEnv, keyEnvAlt?, adapter, modelsPath?, auth?, headerName?, queryParam?, extraHeaders?, staticModels?, noModelsReason?, seeds, enabled?, routerLocal?, contextLengths?`) |
| contract | `ranch-tack/live-catalog/v1` | `ranch-roost/live-catalog/v1` |
| created | 2026-10-01 (79a7a78) | 2026-09-30 rename (5d75050); actively maintained |
| commits 2026-10-02 | 0 | 3 (63→69→75 providers, baseUrl health sweep) |
| bun workspace member | **no** (orphan, not in ranch `package.json` workspaces) | yes |
| codegen | none | deterministic → `providers.json` / `.go` / `.rs` / `tau-models.yml`, sync-tested |

- **Coverage: all 36 tack providers exist in roost. Zero missing.** (`comm -23`
  on extracted name lists: empty.)
- **tau policy gate: all 36 `TAU_PROVIDER_POLICY` IDs exist in both.** Switching
  tau's source from tack to roost cannot add or drop a tau catalog provider —
  the policy is the gate, and it's fully covered.
- **Consumers of tack: exactly 1** — `/home/toxic/tau/packages/catalog/src/compat/tack.ts`
  (plus its ignored duplicate under `estate/ranch/tau/`; scratch-dir hits under
  `estate/var/scratch/` are junk).
- **Consumers of roost:** flock proxy (`proxy/src/roost_providers.rs` ← generated
  `providers.rs`), herd (generated `providers.go`), `flock/ts/astmatrix`,
  `flock/ts/strategy`, `flock/ts/bench`, `flock/ts/live-models`, Python tooling
  (generated `providers.json`).

## tack is not just duplicated — it's stale

tack's schema is a strict subset of roost's, and where they disagree, **roost
is the corrected one** (verified line-by-line in `flock/roost/src/data.ts`):

- `google`: tack says `keyEnv: GEMINI_API_KEY`. roost routes google through the
  local EAP keypool (`http://127.0.0.1:25109/gemini-eap-interactions`,
  `auth: "none"`, `keyEnv: ""`, `adapter: "static"`) with a comment explaining
  the old key 401'd every request. **tack gives tau a dead credential.**
- `commandcode`: roost `keyEnv: COMMAND_CODE_API_KEY`, tack's
  `COMMANDCODE_API_KEY` preserved as `keyEnvAlt`. roost corrected, tack stale.
- `huggingface`: roost `keyEnv: HUGGINGFACE_HUB_TOKEN`, tack's `HF_TOKEN` kept
  as `keyEnvAlt`. Same pattern.
- `meta`: roost `keyEnv: MODEL_API_KEY`, tack's `META_API_KEY` kept as
  `keyEnvAlt`. Same pattern.
- `nanogpt`: roost `keyEnv: NANO_GPT_API_KEY` with **no alt** — tack's
  `NANOGPT_API_KEY` would be silently lost if tau switches blindly. **This is
  the one gap to fix in roost before the merge** (one line: add
  `keyEnvAlt: "NANOGPT_API_KEY"`).

Both files claim to be the "single source of truth" in their header comments.
Only one of them is maintained. It's roost.

## What "merge into flock" concretely means

1. **Fix the nanogpt gap** in `flock/roost/src/data.ts`: add
   `keyEnvAlt: "NANOGPT_API_KEY"`. One line.
2. **Regenerate roost artifacts**: `bun run build` in `flock/roost/` (deterministic
   codegen; sync test diffs byte-for-byte).
3. **Repoint tau's consumer**: in `/home/toxic/tau/packages/catalog/src/compat/tack.ts`
   (rename file to `roost.ts` when convenient):
   - resolver candidates: `ROOST_PATH` env → `$HOME/estate/ranch/flock/roost/src/index.ts`
     via `os.homedir()` (relocatable — replaces the hardcoded `/home/toxic/…`
     path) → `@ranch/roost` package → relative dev path;
   - map roost `ProviderDef` → tau's view (`name/keyEnv/keyEnvAlt/auth/baseUrl`),
     **skipping `routerLocal` and `enabled === false` entries** (per roost's own
     docs: "Other consumers (herd, TAU, Python) skip these definitions");
   - regenerate the embedded fallback snapshot **from roost**, not tack
     (the current snapshot was hand-copied from tack and is already missing
     nothing, but it must track roost going forward — generate at build time).
   - `TACK_PATH` env (introduced 2026-10-01, nothing depends on it) can be
     dropped in favor of `ROOST_PATH`.
4. **Delete `ranch/tack/`**: `git rm -r tack/` in the ranch repo, commit, push.
   It's 2 files, 57 lines, 1 day old, zero live consumers.
5. **Fix the stale comment** in `flock/ts/astmatrix/src/providers.ts`
   ("providers carry Tack's seeds" — terminology left over from the rename).
6. **Rebuild + verify**: rebuild tau `dist/omp`, run `tau models`, confirm the
   36 policy providers resolve; commit + push `toxicwind/tau`; commit + push
   ranch.

## What breaks

Almost nothing — the full consumer list that must change:

- `/home/toxic/tau/packages/catalog/src/compat/tack.ts` — the only real tack
  consumer (resolver rewrite + roost field mapping + `routerLocal`/`enabled` filter).
- `flock/ts/astmatrix/src/providers.ts` — comment-only fix.
- `ranch/tack/` itself — deleted.

Not affected: flock proxy, herd, flock/ts/*, Python consumers (all already on
roost); tau's `TAU_PROVIDER_POLICY` (all 36 IDs covered by roost); tau's
embedded-snapshot mechanism (just re-sourced).

## Behavioral notes for the merge executor

- `google` in tau will inherit roost's keypool routing (`auth: "none"`). That is
  current estate reality (matches the 2026-10-02 oracle bidder repoint to the
  local EAP router). tau's catalog entry for google becomes unauthenticated —
  honest on this box.
- Do NOT surface roost's `routerLocal` providers (`nim-local`, `kimi-auto`) or
  `enabled: false` providers in tau.
- tack's contract string `ranch-tack/live-catalog/v1` dies with the directory;
  nothing references it outside tack's own header.

## Bottom line

tack/ is a 1-day-old, 36-provider, unmaintained, not-even-workspaced subset of
the 75-provider roost that already lives in flock and already feeds the proxy,
herd, and the TS routers. The 2026-09-30 rename was correct; the 2026-10-01
re-creation was the mistake. Merge = delete tack/, repoint tau at roost, fix
one nanogpt alt-var line first.

