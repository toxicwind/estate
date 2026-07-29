# Morphe Patching — Research SSOT (never redo)

**What**: Morphe is the community successor to ReVanced (hard fork, GPLv3 + Section 7 notice) — an Android APK patcher that modifies closed-source apps (YouTube, YT Music, X, Instagram) at the **bytecode level** without source.

**Org**: [MorpheApp](https://github.com/MorpheApp)
**Local clones** (depth 1, 2026-07-28): `/home/toxic/projects/morphe-patcher`, `/home/toxic/projects/morphe-patches`, `/home/toxic/projects/morphe-documentation`

| Repo | Role |
|---|---|
| `morphe-patcher` | Engine: fingerprints, instruction filters, patch DSL, APK/dex pipeline |
| `morphe-patches` | The actual patches (YouTube/Music/etc.) + `Fingerprints.kt` per patch |
| `morphe-manager` | Android app that runs the patcher on-device |
| `morphe-patches-library` / `-template` | Shared dev lib / template for custom patch bundles |
| `morphe-documentation` | Thin (project is new — the code IS the doc) |

---

## The zeitgeist: never hardcode, match resiliently, fail loud

App updates shift every offset, rename every method (obfuscation). A patch that hardcodes
an instruction index or a method name dies on the next release. Morphe's entire design is
the answer to that: **describe a location by a partial, resilient pattern, resolve it at
patch time, mutate relative to the match, and throw if it doesn't match.**

### 1. Fingerprint = partial description of a method

`morphe-patcher/.../Fingerprint.kt` — a fingerprint matches a method by any combination of:
- `definingClass` / `classFingerprint` (scope: find the class first, resolve inside it)
- `name`, `accessFlags`, `returnType`, `parameters` (exact or `StringComparisonType`)
- `filters`: ordered `InstructionFilter`s — opcode subsequence with optional reference/literal matching
- `strings`: string literals appearing anywhere in the method (any order, `contains`)
- `custom`: arbitrary predicate

Real example (`morphe-patches/.../music/ad/Fingerprints.kt`): three opcodes
(`MOVE_RESULT_OBJECT, INVOKE_VIRTUAL, IGET_OBJECT`) + one unique log-string. That's the
whole anchor — and it survives renames, inlining of neighbors, and recompilation.

### 2. Resolution = string-index first, then narrow, then match, then cache

`Fingerprint.matchOrNull()` resolution order:
1. If `classFingerprint` given → match that first, resolve within its class only.
2. If `definingClass` given → look up directly (or comparison-scan if not EQUALS).
3. **If any filter carries a string literal → use the string→classes index**
   (`getClassesFromOpcodeStringLiteral`) to only scan classes containing that string.
4. Partial-string fallback → all classes with strings; last resort → full class scan.
5. Match is cached (`_matchOrNull`) — resolve once, reuse everywhere.

No match anywhere → `patchException()` — **loud failure, never fuzzy-apply.**

### 3. InstructionLocation = ordered matching with distance tolerance

`InstructionFilter.kt`: filters match an **ordered subsequence**, not a contiguous block:
- `MatchAfterAnywhere` (default): next filter may match anywhere later
- `MatchFirst`: must be instruction 0
- `MatchAfterImmediately`: exactly the next instruction (for `MOVE_RESULT*` pairs)
- `MatchAfterWithin(n)`: at most n unmatched instructions between hits
- (`MatchAfterAtLeast`/`MatchAfterRange` are deprecated — doctrine: use filters unique
  enough that distance constraints are unnecessary)

Filter types: `OpcodeFilter`, `OpcodesFilter`, `LiteralFilter`, `MethodCallFilter`
(matches invoke by name/type), `FieldAccessFilter`, `StringFilter`, `NewInstanceFilter`,
`InstanceOfFilter`, `CheckCastFilter`, `AnyInstruction` (wildcard).

### 4. Mutation = relative to the match, never absolute

Patches (`bytecodePatch { ... }` DSL in `patch/Patch.kt`) mutate via indices **derived
from the match**: `HideGetPremiumFingerprint.instructionMatches.last().index` →
`replaceInstruction(insertIndex, ...)`, `addInstruction(insertIndex + 1, ...)`.
Anchors can be walked further with `MethodNavigator` (follow method-call references
forward/backward from the match — the call-graph equivalent of "trace this symbol").

### 5. Declare dependencies and compatibility

Every patch: `dependsOn(otherPatches...)` + `compatibleWith(packageName, versions)`.
The patcher topologically orders execution and refuses incompatible targets.

### 6. Extension classes = the shim layer

Bytecode patches insert tiny hooks (`if-eqz v0, :show`) that delegate to a bundled
"extension" class written in normal Java/Kotlin. **Patch minimally at the anchor, put
real logic in a clean shim.** (This is exactly our mcpproxy / byte-vision-proxy pattern.)

---

## Translation: Android/DEX → Linux / our stack

| Morphe (DEX) | Our world |
|---|---|
| `.dex` bytecode, smali instructions | Text/config/source files; lines & AST nodes |
| Fingerprint (partial method description) | `Edit.old_string`: unique content anchor, never line numbers |
| `strings` literal index → candidate classes | Grep unique string first → then structural match (ast-grep), then edit |
| `InstructionFilter` opcode subsequence | ast-grep pattern (`pattern`, `selector`, `strictness: relaxed`) |
| `InstructionLocation` (MatchAfterWithin…) | ast-grep `context_before/after/lines`; ordered multi-anchor edits |
| `classFingerprint` (scope narrowing) | Anchor the file/section first, then the hunk inside it |
| `MethodNavigator` (walk call refs) | ast-grep MCP `trace_symbol` (callers/re-exports/deps) |
| `_matchOrNull` cache | Read once, edit from that read; don't re-scan per edit |
| `patchException` on no-match | Edit tool's `old_string not found` — loud stop, no fuzzy apply |
| index-relative mutation (`matches.last().index + 1`) | Anchor ± context lines in `new_string` |
| `compatibleWith(pkg, versions)` | Check file state/version/health endpoint before patching |
| `dependsOn` ordering | Multi-file edit ordering (contracts → envelope → adapters → server) |
| Extension class shim | Sidecar proxies (mcpproxy, byte-vision-proxy), not invasive rewrites |
| dexlib2 mutable proxies | `/proc`, `sysctl`, `kallsyms` — resolve kernel symbols by name, never by address |
| Patcher flow (load → resolve → execute → finalize → write) | Our loop: read → match → edit → `kimi doctor`/typecheck → reload service |

## The backwards doctrine (why we edit bottom-to-top)

Morphe resolves **backwards from stable landmarks**: a string literal is the fixed point;
the method/class is derived from it. Sequential patching obeys the same law:

1. **Edits shift everything below them.** Apply multiple same-file edits **bottom-to-top**
   so earlier edits never invalidate the anchors of later ones. (Top-to-bottom editing is
   hardcoding offsets by stealth.)
2. **Anchor on the most stable content**: unique strings/keys > structural patterns >
   surrounding context > position. Obfuscated Android code ≈ minified JS ≈ generated
   config — treat position as volatile always.
3. **Fail loud.** A fingerprint that doesn't match means the target changed — stop and
   re-survey; never force-apply.
4. **Minimal hook at the anchor, logic in the shim.** Small diffs survive; big rewrites rot.

## Quick reference: reuse the clones

```bash
# fingerprints in practice
grep -rn "Fingerprint(" /home/toxic/projects/morphe-patches/patches/src/main/kotlin | head
# engine internals
ls /home/toxic/projects/morphe-patcher/src/main/kotlin/app/morphe/patcher/
# Fingerprint.kt (1229 lines): matchOrNull resolution order, matchAll, Match class
# InstructionFilter.kt: InstructionLocation classes + all bundled filters
```

---
*Researched 2026-07-28 via gh api + shallow clones of MorpheApp org. Maintainer: toxic*
