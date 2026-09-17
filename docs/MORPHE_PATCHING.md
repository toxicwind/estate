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
# flagship worked examples from the audit below (paths under patches/src/main/kotlin/app/morphe/patches/)
ls /home/toxic/projects/morphe-patches/patches/src/main/kotlin/app/morphe/patches/youtube/video/playerresponse/  # finalize-time hook multiplexer
ls /home/toxic/projects/morphe-patches/patches/src/main/kotlin/app/morphe/patches/shared/misc/proto/             # method-clone trampoline
ls /home/toxic/projects/morphe-patches/patches/src/main/kotlin/app/morphe/patches/shared/misc/litho/filter/      # litho filter core + accumulator
ls /home/toxic/projects/morphe-patches/patches/src/main/kotlin/app/morphe/patches/youtube/misc/chapters/         # interface implantation
```

## YouTube patches audit (288 files)

Seven-agent audit (2026-07-28) of every `.kt` under `youtube/` (215), `shared/` (68), and the 5 root files in `/home/toxic/projects/morphe-patches/patches/src/main/kotlin/app/morphe/patches/`. All citations below are relative to that base; `EXT` = the patch's extension class. Ordered by cleverness, descending.
Raw per-agent reports: `~/.kimi-code/sessions/wd_toxic_240656b67e56/session_07d0d779-fc98-4f65-89fc-0ef33e8c47ea/agents/main/tool-results/AgentSwarm-tool_j5w56scYA2j2d13SeRj9iq4j-*.txt` (923 lines).

### 1. Native protobuf synthesis in injected smali — writing new logic in the target's own type system

Extension Java can't construct obfuscated proto classes, so the patch replays YouTube's own parse pipeline in smali.

- `youtube/layout/buttons/navigation/NavigationBarPatch.kt:249-310` — extension returns serialized `[B`; injected smali does `sget-object type->a:type` (default instance) → `parseByteArray` (ref from `fixProtoLibraryPatch`) → `check-cast` → `new-instance` + `invoke-direct/range` with the *original constructor reference harvested from the fingerprint match*; which ctor parameter is `MessageLite` is computed at patch time (`parameterTypes.indexOfFirst`, :257-258) and its register backed up with `move-object/16` to dodge 4-bit limits. `PivotBarRendererListFingerprint` (:312-338) then re-fingerprints the proto-list builder from a matched field's type and splices the synthesized renderers into the real button list.
- `shared/misc/spoof/SpoofVideoStreamsPatch.kt:192-306` — `patch_setStreamingData` (11 regs) does a full builder round-trip (`createBuilder → mergeFrom([B) → build → iget → iput`) with refs harvested from five fingerprints, emitting the `check-cast` only when the resolved types differ — version-adaptive codegen.
- `youtube/misc/contexthook/ClientContextHookPatch.kt:72-115` — proto-builder field surgery: `clientInfo`/`osName`/builder refs harvested positionally from four fingerprints; the synthesized helper walks `invoke-virtual builder → iget → check-cast → iget` per endpoint class.
- `shared/misc/fix/proto/FixProtoLibraryPatch.kt` — when the target's protobuf classes lack methods the extension needs, the patch *adds them* (cloned `MessageLite.writeTo` with retyped param, synthesized `getEmptyRegistry`) and exports the refs via `internal lateinit var` for other patches' codegen.

### 2. Interface implantation — the compile-time FFI bridge over obfuscation

Make obfuscated classes implement extension-defined interfaces; synthesize `patch_*` accessors; extension code programs against stable Java types. Top-3 pick for 5 of 7 agents.

- `youtube/video/information/VideoInformationPatch.kt:554-627` — implants `PlaybackController` on the player class; `patch_seekTo(J)Z` hardcodes `sget-object $seekSourceEnum->a`, exploiting that an enum's first constant is always field `a` under obfuscation. Also `PlaybackSpeedMenuInterface` (:260-331, computes a ctor param's p-register arithmetically as `registerCount - parameters.size + index`) and `VideoQualityInterface` (:369-424, field accessors synthesized by type-uniqueness: `fields.single { it.type == "I" }`).
- `youtube/interaction/reload/ReloadVideoButtonPatch.kt:101-164` — class located *through a method reference from another fingerprint's last match*; adds interface + two de-obfuscation thunk ImmutableMethods + `invoke-static { p0 }, EXT->initialize(...)` injected before the ctor's final `RETURN_VOID` — the extension receives a live, statically-typed handle into YouTube internals.
- `youtube/layout/player/fullscreen/OpenVideosFullscreenHookPatch.kt:48-119` — interface + synthesized `patch_enter/exitFullscreen` (two-instruction bodies invoking obfuscated methods by runtime-resolved reference) + instance handoff via the `NextGenWatchLayout` ctor that check-casts the class.
- `shared/misc/litho/context/ConversionContextPatch.kt:106-186` — the adaptive variant: when YT 20.41 moved fields behind an abstract superclass, it *reverse-fingerprints the subclass getters from their field refs* and implants the interface on the superclass, bridging via `invoke-virtual`. Injection site chosen by inspecting the class hierarchy at patch time.
- `youtube/misc/chapters/ChaptersHookPatch.kt:49-119` — TimelineMarker proto class gets the extension interface + three two-instruction iget accessors over fields mined via `findFieldFromToString`; arrays cross the boundary typed as `[Lext/TimelineMarker;`.
- `youtube/layout/flyout/AddToQueuePatch.kt:88-155` — inline heuristic fingerprints find the impl targets ("the only byte array accessed in the method", "the only string field initialized to empty string"), then `patch_getBuffer()[B` / `patch_getVideoId()String` are synthesized on the resolved proto classes.

### 3. finalize-time hook multiplexing — miniature compiler passes

- `youtube/video/playerresponse/PlayerResponseMethodHookPatch.kt:86-146` — N patches register sealed-class `Hook`s during execute; `finalize` injects all at index 0 with each category `asReversed()` so final bytecode order matches registration priority (ProtoBufferParameter hooks deliberately land first so later hooks can query is-Short). When 17 params push p13 past the 4-bit window (`registerCount - paramCount + paramIndex > 15`, :70-71) it rebases args into v0–v3 with `move/from16`, and tracks `numberOfInstructionsAdded` so the extension-modified proto param is written back exactly after the last hook.
- `youtube/misc/contexthook/ClientContextHookPatch.kt:39-237` — two-phase smali-accumulator DSL: `addOSNameHook`/`addClientVersionHook`/`addClientFormFactorHook` append iget/invoke/iput *text fragments* to an enum's mutable `smaliInstructions`; `finalize` synthesizes one `patch_setClientContext` helper per endpoint class and splices calls before every `return-void`. Generated bytecode depends on both version flags and which other patches are included.
- `shared/misc/litho/filter/LithoFilterPatch.kt:54-64,344-359` — collaborative codegen in the extension's own `<clinit>`: `addLithoFilter(descriptor)` appends `new-instance`/`aput-object` per consumer patch; `finalize` seals with an exactly-sized `const/16 count; new-array; return-object`. N independent patches → one deterministic runtime registry, zero ordering constraints (helper exists to dodge an AGP 8.3.0 register bug).

### 4. Method-clone trampoline — the universal register-starvation fix

- `shared/misc/proto/ElementProtoParserHookPatch.kt:38-61` — clones the parser as `patch_parseNewElement`, reduces the original to a 3-instruction trampoline (`invoke-static {p0}, $clone; move-result p0; return p0`); other patches' `hookElement` then injects at the *constant index 2* of the known trampoline shape.
- `shared/misc/debugging/EnableDebuggingPatch.kt:95-122` — flag getter cloned to `patch_getBooleanFeatureFlag`; original becomes call-clone → move-result → `EXT->isBooleanFeatureFlagEnabled(ZJ)Z` → return; wide-arg variants reshuffle p-regs into low v-regs for `invoke-static/range`.
- `shared/misc/audio/tracks/ForceOriginalAudioPatch.kt:99-141` — `cloneMutable(additionalRegisters = 4)` + swap-replace in `classDef.methods`, plus a `volatile Boolean` cache field so the extension is consulted once per model instance.
- `youtube/video/quality/PrioritizeVideoQualityPatch.kt:33-54` — cheaper variant: `cloneParameters()` then *offsets its own match indices* by `numberOfParameterRegistersLogical` to compensate for the moves it just injected. Self-adjusting mutation (also `youtube/layout/returnyoutubedislike/ReturnYouTubeDislikePatch.kt:197-199`, "21.05 clobbers p0").

### 5. Cross-class transplantation & dead-code resurrection — rebuilding deleted features

- `youtube/video/speed/custom/CustomPlaybackSpeedPatch.kt:192-306` — rebuilds the removed old speed menu on 21.12+ by *stealing three method references from the sibling audio-track bottom-sheet class* (same base class → same obfuscated member names), rewriting definingClass by string replace, locating fields by type-uniqueness, synthesizing `patch_showOldPlaybackSpeedMenu`, gated on an extension check with `return-void` suppressing the new menu.
- `youtube/layout/shortsautoplay/ShortsAutoplayPatch.kt:128-192` — Google deleted the autoplay path in 20.09; the patch manufactures a private 7-register `patch_handleAutoPlay(Ljava/lang/Enum;)Ljava/lang/Enum;` from refs harvested from `ReelPlaybackFingerprint`, where the null return doubles as control flow *and* eliminates the free-register hunt at the insertion site.
- `youtube/interaction/swipecontrols/SwipeControlsPatch.kt:139-161` — splices the extension's `SwipeControlsHostActivity` *into MainActivity's inheritance chain* (`wrapper.setSuperClass(target.superclass); target.setSuperClass(wrapper.type)`) and strips FINAL across the hierarchy — whole-activity capability injection through one pointer swap, zero instructions of MainActivity touched.

### 6. toString debug-string anchoring — the field-reordering oracle

The most pervasive fingerprint trick: `toString` literals are never obfuscated, so they identify data classes and the declaration order of their fields.

- `youtube/video/quality/Fingerprints.kt:80-88` — `name="toString"` + `", initialPlaybackVideoQualityFixedResolution="`; `youtube/misc/auth/Fingerprints.kt:21-22` — `", getPageId="` / `", isIncognito="`; `youtube/misc/chapters/Fingerprints.kt:18` — `"TimelineMarker[title="`; `shared/misc/audio/tracks/Fingerprints.kt:29-63` — `"id;displayName;isAutoDubbed;isDefault"`; `youtube/layout/hide/updatescreen/HideUpdateScreenPatch.kt:33-36` — one `const/4 p1, 0x0` kills the undismissable update screen, anchored via `"AppBlockingCheckResult{intent="`.
- Comma-prefixed partial fragments survive field reordering: `"ConversionContext{"` + `", identifierProperty="` (`shared/misc/litho/context/Fingerprints.kt:14-25`); `StringComparisonType.STARTS_WITH` + positional inference — "first method call after Locale is the video ID" (`youtube/video/information/Fingerprints.kt:223-233`).
- `findFieldFromToString` / `findMethodFromToString` then mine `instructionMatches[i]` for the IGET/IPUT adjacent to each matched string — obfuscated field refs recovered in declaration order (`youtube/misc/auth/AuthHookPatch.kt:33-39`).

### 7. Two-stage runtime-constructed fingerprints — match output feeding match input

Fingerprints parameterized on data extracted from a previous fingerprint's match; resolution chains up to five hops.

- `youtube/video/quality/RememberVideoQualityPatch.kt:76-88` — `findFieldFromToString` recovers the obfuscated field, then `Fingerprint(classFingerprint=…, name="<init>", filters=[fieldAccess(IPUT_OBJECT, reference=initialResolutionField)])` is built *inline inside execute* — string → field ref → constructor hook.
- `youtube/interaction/dialog/RemoveViewerDiscretionDialogPatch.kt:99-110` — fieldAccess smali strings derived from a previous match's `reference.toString()`; `methodCall(definingClass = AdultContentRunnableFingerprint.method.definingClass)` (:70) matches an invoke against whatever class the first fingerprint resolved to.
- Fingerprint factories: `youtube/video/information/Fingerprints.kt:54-68` `getChannelIdFingerprint(playerResponseType)` — the type pulled from a `matchAll(2..3)` parameter (`VideoInformationPatch.kt:489-495`); `youtube/misc/chapters/Fingerprints.kt:21-28` — `returnType = "[$timelineMarkerClassName"` (array-of-obfuscated-type); `youtube/misc/auth/Fingerprints.kt:35-92` — getter-finders generated around a recovered field ref; `shared/misc/audio/tracks/Fingerprints.kt:130-147` — a `custom` predicate referencing a runtime-discovered type.
- Enum-type threading: `<clinit>` matched by constant-name strings (survive R8 for `Enum.valueOf`) — `"SEEK_SOURCE_SEEK_TO_NEXT_CHAPTER"` (`youtube/interaction/doubletap/Fingerprints.kt:6-12`), `"UNKNOWN_FORM_FACTOR"…` (`youtube/misc/contexthook/Fingerprints.kt:73-89`) — then the resolved enum type becomes the *parameter filter* of the next fingerprint (`youtube/video/information/Fingerprints.kt:81-109`).
- The deepest chain: `youtube/layout/hide/relatedvideos/HideRelatedVideosPatch.kt:59-233` — field ref from shared fingerprint → resultsClass → fingerprint its `<init>` → model class from a CHECK_CAST → anonymous fingerprint parameterized on three resolved refs → harvest two more fields → chain a sixth off a debug format string. Nothing anchored directly; five levels of derived identity.
- Also: `youtube/misc/fix/likebutton/FixLikeButtonPatch.kt:44-64` — fingerprints built at patch time from a prior match (method name + abstract interface), the two implementations discriminated by `instructions.count() > 7` vs `< 7`.

### 8. Litho / protobuf component filtering

- The core gate: `shared/misc/litho/filter/LithoFilterPatch.kt:208-307` — anchored on `"Element missing correct type extension"`; at the component-builder's RETURN_OBJECT it re-encodes the Upb buffer (`instance-of`/`check-cast`/`jniEncode` with empty-array fallback), pulls accessibilityId/Text through interface calls (registers default-initialized with `const-string ""` at the earlier null-check branch so both paths define them), calls `EXT->isFiltered(ContextInterface,[B,String,String)Z`, and returns a recovered `EmptyComponent` singleton if filtered — original code always runs when unfiltered (comment: avoids memory leaks).
- Registration APIs: `addLithoFilter` (11 callsites in layout alone; `youtube/ad/HideAdsPatch.kt:73` — the patch class doubles as filter), `hookTreeNodeResult` for lazily-converted elements (`youtube/layout/buttons/action/HideVideoActionButtonsPatch.kt:113`), `hookElement("EXT->m([B)[B")` — serialized proto in, rewritten bytes out, filtering at the parse layer before any UI exists (`youtube/ad/HideAdsPatch.kt:117`).
- Tree-node list mutation at `instructions.lastIndex` so extensions physically remove entries (`shared/misc/litho/node/TreeNodeElementHookPatch.kt:66-80`); text-component hook sharing with auto-incrementing insert index so stacked hooks compose (`shared/misc/textcomponent/TextComponentPatch.kt:26-65`).
- Covert channel: `youtube/ad/HideAdsPatch.kt:246-266` — `addOSNameHook` on six endpoints rewrites the osName proto field per endpoint and downstream filters read the marker — data smuggled through an existing request pipe.
- RYD litho depth: the TextComponent span *cache* site chosen over the creation site because the cache covers all code paths (`youtube/layout/returnyoutubedislike/ReturnYouTubeDislikePatch.kt:136-215`), plus four rolling-number hooks (iget→EXT→iput field rewrite, measured-width `(String,F)F` so layout accounts for an added separator, static-label measure, setText interception in both TextView and animation method).
- Proto plumbing as beacon: `youtube/interaction/reload/Fingerprints.kt:23-29` locates a command-endpoint handler by its proto-decode failure log (`"…decoding MiniAppMetadata…"`), with an alternative string for the renamed proto field.

### 9. Proto varint / feature-flag / resource literal anchors

Constants survive obfuscation; three literal families do most of the anchoring in the corpus.

- Proto field-ID varints (Litho/protobuf element ids, extremely stable): `youtube/shared/Fingerprints.kt:281-304` chains three (`49399797L`, `51779735L`, `46659098L`) interleaved with SGET/IGET/CHECK_CAST structural filters; `youtube/video/speed/custom/Fingerprints.kt:66-81` — `45719140L`/`45731126` keyed on literal only; `youtube/layout/buttons/navigation/Fingerprints.kt:257,315` — `117501096L`/`120823052L`.
- A/B feature flags (the dominant idiom): `literal(<8-digit>L)` + `returnType="Z"` + `[]` is a whole fingerprint — `youtube/interaction/seekbar/Fingerprints.kt:34` (three-level narrowing: literal → class → method, children differ only by `literal(1)` or access flags), `youtube/layout/theme/Fingerprints.kt:13-23`, `youtube/misc/backgroundplayback/Fingerprints.kt:85-111` (comment: flag "used in ~100 locations" — the anchor finds the declaration, not the uses). Comments carry folklore: "breaks playback/Shorts if spoofing" (`shared/misc/spoof/Fingerprints.kt:230-279`), dead flags kept because older targets still use them (`youtube/layout/miniplayer/Fingerprints.kt:37`).
- Resource literals: `resourceLiteral(TYPE, name)` resolves `@layout/foo` → compiled int via `resourceMappingPatch` — immune to R8 const-inlining, version-fragile to resource removal (`youtube/ad/Fingerprints.kt:37,77`; `youtube/misc/gms/Fingerprints.kt:16-17` pairs drawable+string to pin one controller; `youtube/layout/buttons/navigation/Fingerprints.kt:172-181` stacks two ATTR literals).
- Fingerprint-free global literal scans: `youtube/ad/HideAdsPatch.kt:186-227` — `classDefForEach` + lazy `mutableClassDefBy` (mutation proxies only for classes containing the literal), verifying the next instruction is `INVOKE_VIRTUAL findViewById`; `youtube/layout/branding/header/ChangeHeaderPatch.kt:61-70` — hooks *every* use of two attr ids app-wide because attr references are scattered.

### 10. Extension-class protocol shapes

Bytecode patch = minimal hook; extension = all logic. The recurring wire shapes:

- Boolean gate at index 0: `invoke-static {} EXT->x()Z / move-result v0 / if-eqz :show / return-void / :show nop` — the trailing `nop` anchors the label so later insertions don't re-target it (ubiquitous; `youtube/ad/HideAdsPatch.kt:102-112`, ~8 uses in interaction alone). Inverted form: gate *preserves* the original return when the patch is disabled (`youtube/misc/backgroundplayback/BackgroundPlaybackPatch.kt:80-94`).
- Value laundering: `EXT->f(T)T` overwrites the param/result register in place — disabled setting = identity passthrough (`youtube/interaction/doubletap/DisableChapterSkipDoubleTapPatch.kt:54-60` rewrites `p1` at index 0; `youtube/misc/backgroundplayback/BackgroundPlaybackPatch.kt:65-77` rewrites *every* RETURN via reversed-index scan + `addInstructionsAtControlFlowLabel`).
- ExternalLabel body-skip: the branch target is the *existing instruction object* captured before insertion — zero label bookkeeping (`youtube/interaction/seekbar/DisablePreciseSeekingGesturePatch.kt:29-52`; `youtube/misc/fix/playbackspeed/FixPlaybackSpeedWhilePlayingPatch.kt:39-56`; reusing YouTube's own error path as the hide path at `youtube/layout/hide/general/HideLayoutComponentsPatch.kt:406-429`).
- Call-site replacement: swap a virtual call for a same-signature extension static, receiver becomes arg 0, registers forwarded verbatim (`fiveRegisters(index)` splats all 5 registers, `youtube/layout/hide/player/flyoutmenu/HidePlayerFlyoutMenuComponentsPatch.kt:93-139`; global `Vibrator.vibrate` trampoline multiplexing both overloads, `youtube/interaction/hapticfeedback/DisableHapticFeedbackPatch.kt:104-130`; every `getSupportedHdrTypes` call, `youtube/video/codecs/DisableVideoCodecsPatch.kt:51-59`).
- Register passing: `invoke-static/range { p1 .. p1 }` single-register range idiom dodges 4-bit limits (`youtube/video/information/VideoInformationPatch.kt:712-719`); emit-width chosen by `if (register < 16)` (`shared/misc/media/MediaFetchPlayerConfigHookPatch.kt:43-47`); wide pairs passed as `{ v$reg, v${reg+1} }` (`youtube/interaction/livestream/LivestreamDVRPatch.kt:64-75`).
- Static state: setters stash live objects in extension statics during normal execution (`setMainActivity`, `setSettingsController`, `setProtoBuffer(ByteBuffer)` at index 0 — `shared/misc/litho/filter/LithoFilterPatch.kt:163-166`); synthesized `INSTANCE` self-capture adds a static field onto an obfuscated class (`youtube/video/speed/custom/CustomPlaybackSpeedPatch.kt:153-171`).
- Extension self-fingerprints: patches fingerprint *their own extension class* and rewrite it — `returnEarly(constant)` bakes patch-time facts into runtime code (`shared/misc/proxy/BaseNetworkProxyPatch.kt:57-59`, `shared/misc/gms/GmsCoreSupportPatch.kt:208`); `getSpanType`'s `instance-of CharacterStyle` is retargeted to the obfuscated `CustomCharacterStyle` — target-class type bleeding into extension bytecode (`shared/misc/spans/InclusiveSpanPatch.kt:82-92`).
- Self-exclusion predicates: `custom = { !classDef.type.startsWith("Lapp/morphe/") }` so global scans don't re-match injected code (`youtube/video/codecs/Fingerprints.kt:14-16`; `youtube/interaction/hapticfeedback/DisableHapticFeedbackPatch.kt:117-119` — load-bearing: the vibrate scan would re-match the extension's own shim).
- Enum smuggling: obfuscated enums cross the boundary as `Ljava/lang/Enum;` — instance captured from `<clinit>`'s first SGET (`youtube/layout/shortsautoplay/ShortsAutoplayPatch.kt:71-83`), or an int is mapped to a stable semantic string by calling YouTube's *own* obfuscated mapper from injected smali (`youtube/layout/player/fullscreen/DisableFullscreenGesturesPatch.kt:55-88`).
- Calling back into obfuscated code from injected smali using match-harvested names: a `Point` constructed at index 0 of `onTouchEvent` and filled via the app's own `updatePoint` interface method, then a three-hop iget field-path traversal with refs from another fingerprint's matches (`youtube/interaction/seekbar/SeekbarThumbnailPreviewPatch.kt:53-81`).

### 11. Cross-patch parameterization — patches as platform

- Patches taking patches/params as arguments: `youtube/ad/HideAdsPatch.kt:90` `hideFullscreenAdsPatch(PreferenceScreen.ADS)`; `youtube/audio/DisableDRCAudioPatch.kt:12-25` passes version flags as *lambdas* (`useLegacyNormalizationFlag={ !is_21_19_or_greater }`) evaluated lazily inside the shared patch's execute; `youtube/misc/gms/GmsCoreSupportPatch.kt:17-35` orchestrates three other patches (hide dead cast button, spoof streams); `youtube/layout/theme/ThemePatch.kt:37-259` `baseThemePatch(extensionClass, includeLightThemeOption, block, executeBlock)` with lambdas closing over version checks; a *nested parameterized patch instance as a dependency* (`shared/misc/spoof/SpoofVideoStreamsPatch.kt:90-98`).
- Hook-registry pattern: one patch resolves method+index, stores `WeakReference<MutableMethod>` + running insert counter, exports `addXHook(descriptor)`; consumers never touch bytecode (`youtube/video/information/VideoInformationPatch.kt:72-103` consumed by 4+ patches; `shared/layout/theme/LithoColorHookPatch.kt:18-30` bumps `insertIndex += 2` per registrant; `highPriority` flag picks index-0 vs accumulated offset, `youtube/misc/imageurlhook/CronetImageURLHook.kt:86-95`). WeakReferences deliberately avoid pinning the mutable DEX graph beyond patch lifecycle.
- Phase-ordering via anonymous dependency patches: `dependsOn(bytecodePatch { finalize { addTopControl(...) } })` — an unnamed one-shot forcing work into the finalize phase (`youtube/interaction/reload/ReloadVideoButtonPatch.kt:75-84`); aggregators that are pure `dependsOn` (`youtube/interaction/seekbar/SeekbarPatch.kt:7-27`).
- Shared-fingerprint invalidation: `clearMatch()` + re-match after another patch mutated the method — "Fingerprint is shared and indexes may no longer be correct" (`youtube/layout/sponsorblock/SponsorBlockPatch.kt:258-262`); the cheaper alternative is a fresh fingerprint instance per use (`youtube/misc/contexthook/ClientContextHookPatch.kt:150-152`); `clearMatch()` also lets two fingerprints legitimately resolve to one method (`youtube/interaction/hapticfeedback/DisableHapticFeedbackPatch.kt:88-89`).
- Cross-patch coexistence choreography: a `nop` inserted *solely so RYD's patch lands after this patch's control-flow label* (`youtube/layout/hide/rollingnumber/DisableRollingNumberAnimationPatch.kt:43-56`); comments documenting coincidental-but-critical load order (`youtube/layout/livering/OpenChannelOfLiveAvatarPatch.kt:90-96`); `nop`ing out an extension call to "prevent duplicate hooking" before generic machinery re-inserts (`youtube/video/information/VideoInformationPatch.kt:219-231`).

### 12. Settings / preference plumbing

- Group accumulation: module-level `mutableSetOf<BasePreference>()` filled by sub-patches in their own `execute`, parent emits one category (`youtube/video/quality/VideoQualityPatch.kt:15` + remember/advanced/hidePremium/prioritize; `youtube/layout/captions/CaptionsPatch.kt:12-34`); null-out-after-emit in `finalize` with deliberate fail-fast if the patch wasn't included (`youtube/layout/buttons/overlay/PlayerOverlayButtonsSettings.kt:11-38`).
- Lexicographic ordering by dummy sort key: `"morphe_01_video_key"` (quality first) vs `"morphe_zz_video_key"` (speed last) — settings order controlled by key-naming convention.
- `tag` as class-name channel: `NonInteractivePreference(tag = "…LivestreamDVRPreference")` — the extension class FQN carries settings-UI behavior with zero patcher changes (`youtube/interaction/livestream/LivestreamDVRPatch.kt:40,45`; `youtube/layout/sponsorblock/SponsorBlockPatch.kt:48-49` — an empty category populated at runtime by the extension).
- Runtime-populated preferences: `ListPreference(entriesKey=null, entryValuesKey=null)` — entries set by extension code from the actual speeds available (`youtube/video/speed/RememberPlaybackSpeedPatch.kt:46-49`).
- Graceful tombstones: a working `ListPreference` swapped for a `NonInteractivePreference` "not available" marker on targets where the feature is gone (`youtube/layout/miniplayer/MiniplayerPatch.kt:76-80`).
- Options as cross-patch API: `booleanOption` declared `internal` so other patches read the value; a resource patch conditionally deletes XML nodes based on it but still verifies the node exists when off (`youtube/layout/hide/shorts/HideShortsComponentsPatch.kt:47-59,136`).
- Resource-side plumbing: DOM-editing `res/values/arrays.xml` — clearing stock arrays and repopulating with untranslatable string refs because ARSCLib breaks on literal numbers (`youtube/interaction/doubletap/DoubleTapLengthPatch.kt:35-64`); the same preference set serialized three times (icons / bold / none) because preference layout can't be swapped post-inflation (`shared/misc/settings/SettingsPatch.kt:137-169`); sort-mode smuggled in the key string because extensions ignore the key value (`shared/misc/settings/preference/PreferenceScreenPreference.kt:30-36`).

### 13. Version-resilience patterns

- `matchOrNull` fallbacks: modern/legacy/both may coexist or vanish — `matchOrNull()?.let` per account-menu fingerprint (`youtube/layout/hide/general/HideLayoutComponentsPatch.kt:1006,1023,1037`); "Match may be null, as it may have already been replaced by another fingerprint" (`youtube/layout/hide/ambientmode/AmbientModePatch.kt:87-94`); graceful `return@execute` + log instead of throw (`shared/misc/proxy/BaseNetworkProxyPatch.kt:42-44`); whole-feature bail `return@execute` when below the affected version so fingerprints never run where they'd fail (`youtube/misc/fix/likebutton/FixLikeButtonPatch.kt:30-32`).
- Multi-fingerprint strategies: twin modern/legacy pairs selected by version flags — including two *different class-anchor strategies* for one logical hook (`youtube/interaction/seekbar/SeekbarThumbnailPreviewPatch.kt:95-110`); fingerprint *lists* where whichever matches gets patched (`youtube/shared/Fingerprints.kt:306-323`); `anyInstruction(...)` alternation for literal/string drift — int→float at 21.03 (`youtube/layout/miniplayer/Fingerprints.kt:204-211`), int→long flag type change (`youtube/layout/theme/Fingerprints.kt:31-35`), a log string gaining `%s` (`youtube/interaction/downloads/Fingerprints.kt:18-22`).
- Cheapest multi-version marker: byte-identical fingerprints differing only in filter *order* — 21.02 moved `getAction` before the string constant (`youtube/layout/hide/ambientmode/Fingerprints.kt:38-67`).
- `matchAll(range)` multiplicity: `matchAll(2..4)`/`matchAll(1..2)` expected-count ranges hook all overloads and fail loudly out of range (`youtube/layout/flyout/AddToQueuePatch.kt:321`); `matchAll(2..2)` ordinal slice hooks only the 3rd of identical-structure matches (`youtube/misc/gms/AccountCredentialsInvalidTextPatch.kt:26`).
- Deliberately under-specified signatures: returnType omitted where it changed ("boolean up to 19.39, and void with 19.39+", `youtube/video/information/Fingerprints.kt:179`); same 16-param skeleton across generations, the 20.26+ variant adds a 17th `Lj$/time/Duration;` param (`youtube/video/playerresponse/Fingerprints.kt:36-88`); param-shape OR in one `custom` predicate (`shared/misc/privacy/Fingerprints.kt:69-74`).
- Structural predicates over names: method/field/instruction counts (`classDef.methods.count() == 17 || == 16` covering two app generations at once, `youtube/video/videoid/Fingerprints.kt:50-54`; `instructions.count() == 3` disambiguating identical-signature siblings, `youtube/video/information/Fingerprints.kt:160-165`); inverted twin predicates splitting primary/secondary variants (`Consumer` field `!= null` vs `== null`, `youtube/misc/contexthook/Fingerprints.kt:96-112`); superclass whitelists (`youtube/shared/Fingerprints.kt:140-143`); negative interface checks.
- Anchors that can't be obfuscated: framework/SDK-only filters (a 10-filter `MatchAfterImmediately` ladder through `ResolveInfo`→`activityInfo`→`packageName`, `youtube/layout/sharesheet/Fingerprints.kt:19-62`); vendored OSS by upstream error strings with a GitHub permalink to the exact source line (Lottie, `youtube/layout/seekbar/Fingerprints.kt:101-122`); generated proto class names (`StreamingDataOuterClass$StreamingData`, `youtube/video/quality/Fingerprints.kt:90-110`); enum constant names in `<clinit>`; a hardcoded fallback version string `"10.29"` (`youtube/misc/contexthook/Fingerprints.kt:59`); an int hashcode constant (`youtube/layout/seekbar/Fingerprints.kt:57-66`).
- Global-rewrite with callsite-context whitelists: every `Context;->getPackageName()` call app-wide, then per-callsite filters (skip if method contains `"gcore_"`, require `StringBuilder.append` two instructions later) — `shared/misc/spoof/UserAgentClientSpoofPatch.kt:32-69`; 600+ const-string permission/action rewrites for MicroG (`shared/misc/gms/GmsCoreSupportPatch.kt:95-189`).
- Central version SSOT: ~38 `is_2X_YY_or_greater` vars via `Delegates.notNull()` — throws if read before `versionCheckPatch` runs, i.e. dependency-order enforcement by construction (`youtube/misc/playservice/VersionCheckPatch.kt:10-87`); signing-cert hashes as the compatibility key (`youtube/Constants.kt:13-18`); comments as institutional memory on every gate ("flag removed in 21.15+", "21.21+ removed reel/create_reel_items").

### 14. Synthesized helpers, register discipline & smaller gems

- `patch_*` helpers implanted into obfuscated classes get private-field access and `p0`: `youtube/layout/captions/CaptionCookiesPatch.kt:45-108` (the helper contains the gate itself and adds Cookie/User-Agent headers); full hand-written smali iterator loops (`:loop`/`:exit`, `Iterator;->remove()`, `instance-of` guards) filtering collections in place (`youtube/layout/hide/general/HideLayoutComponentsPatch.kt:763-837`, `youtube/misc/fix/preference/FixPreferenceIconPatch.kt:50-135`, `youtube/layout/hide/relatedvideos/HideRelatedVideosPatch.kt:135-233`).
- Free-register discipline: `findFreeRegister(insertIndex, excluded...)` / `getFreeRegisterProvider` before any multi-instruction insert, with non-overlapping register sets across two injection points in the same method (`shared/misc/litho/filter/LithoFilterPatch.kt:177-307`); borrowing a dead register justified by dataflow instead of allocating (`youtube/interaction/loop/LoopVideoPatch.kt:56-57` — reuses the SGET's destination register as scratch); siphoning a value via a *second* `move-result` after the original (`youtube/layout/returnyoutubedislike/ReturnYouTubeDislikePatch.kt:262-275`).
- Index arithmetic as hook-composition protocol: auto-incrementing `playerInitInsertIndex++` so N patches stacking hooks on the same method never collide and ordering follows call order (`youtube/video/information/VideoInformationPatch.kt:644-710`).
- Patch-time param discovery: which ctor parameter is which type via `parameterTypes.indexOfFirst`, its register as `startRegister + index + 1` — survives constructor signature reorders (`youtube/layout/buttons/navigation/NavigationBarPatch.kt:257-258`); param-to-field flow tracking finds a field by scanning the ctor for the `IPUT_OBJECT` whose source register is p2 (`shared/misc/litho/node/TreeNodeElementHookPatch.kt:88-134`).
- Opcode-skeleton fingerprints (zero strings): 24-25-opcode sequences pinning one boolean decision method (`youtube/misc/backgroundplayback/Fingerprints.kt:17-43`); pure dataflow shape recognizing "elapsed = now − start" arithmetic (`youtube/layout/hide/time/Fingerprints.kt:12-34`); tap-slop math via `Math;->hypot` (`youtube/layout/hide/shorts/Fingerprints.kt:86-99`); double `MONITOR_EXIT…RETURN_VOID` tail encoding a synchronized method's try/finally (`youtube/video/videoid/Fingerprints.kt:38-49`); two consecutive `ADD_INT_2ADDR` as an onMeasure anchor (`youtube/ad/Fingerprints.kt:56-62`).
- Conjunctive non-unique strings: "None of these strings are unique" — signature + the conjunction of three individually-ambiguous strings is the anchor (`youtube/layout/shortsplayer/Fingerprints.kt:10-43`); deliberate same-method convergence, three fingerprints intentionally matching one method from different patches (`youtube/layout/player/overlay/Fingerprints.kt:11-19`, `youtube/layout/sponsorblock/Fingerprints.kt:30-41`).
- Mutation minimalism: measurement-nulling instead of view-hiding — conditionally `const/4` zeroing width/height locals in onMeasure because the later protected call can't be intercepted (`youtube/ad/HideAdsPatch.kt:138-160`); single-instruction method kill (`return-void` at index 0, `youtube/interaction/reload/ReloadVideoButtonPatch.kt:166-169`); constant rewrite instead of a hook — `replaceInstruction` with `const/16 v$reg, 170`, the floor discovered empirically (`youtube/layout/miniplayer/MiniplayerPatch.kt:276-285`); brute-force `const/4 v$reg, 0x0` after the final MOVE_RESULT (`youtube/misc/fix/verticalscroll/FixVerticalScrollPatch.kt:28-37`).
- Enum exploitation beyond anchoring: force-returning the `DISABLED_BY_SABR_STREAMING_URI` constant located by its `<clinit>` SPUT (`shared/misc/spoof/SpoofVideoStreamsPatch.kt:372-401`); passing the resolved enum *and* its valueOf-style factory across the boundary so the extension knows which flyout button is being built (`youtube/layout/flyout/AddToQueuePatch.kt:231-238`).
- Transitive callee hooking: filter all `Z`-returning calls inside a matched method, take `booleanCalls[1]` (ordinal pick), resolve it, and inject the gate into the *callee* rather than the matched method (`youtube/misc/backgroundplayback/BackgroundPlaybackPatch.kt:105-112`); `getMethodCalled()` on a matched invoke to fingerprint the target next (`youtube/layout/hide/endscreensuggestedvideo/HideEndScreenSuggestedVideoPatch.kt:37-58`).

### 15. The swarm's TOP-3 picks, distilled (7 agents × 3)

- agent-0 (ad/shared/video): ① `PlayerResponseMethodHookPatch` — reversed-order, register-rebasing, finalize-time hook multiplexer, "a miniature compiler pass disguised as a patch"; ② `VideoInformationPatch` — interface implants incl. the enum-first-constant-is-always-field-`a` exploit; ③ `CustomPlaybackSpeedPatch:192-306` — sibling-class method transplantation predicated entirely on obfuscation symmetry.
- agent-1 (interaction): ① `ReloadVideoButtonPatch:101-164` — obfuscated-class → extension-interface bridge yielding a live typed handle; ② `SwipeControlsPatch:139-161` — extension activity spliced into MainActivity's inheritance chain; ③ `SeekbarThumbnailPreviewPatch:53-81` — calling YouTube's internal geometry API from injected smali + 3-hop iget field-path traversal.
- agent-2 (layout A): ① `NavigationBarPatch:249-310` — native proto button synthesis in the target's own type system; ② `HideRelatedVideosPatch:59-233` — five-level transitive fingerprint chain plus continuation-nuking to kill follow-up API spam; ③ interface implantation as a complete patch-time FFI layer.
- agent-3 (layout B): ① `OpenVideosFullscreenHookPatch:48-119` — interface graft + synthesized vtable bridge; ② `ShortsAutoplayPatch:128-192` — dead-code resurrection with a synthesized helper; ③ `DisableFullscreenGesturesPatch:55-88` — obfuscated int → stable semantic string via YouTube's own enum mapper.
- agent-4 (misc A): ① `ChaptersHookPatch:49-119` — compiler-free adapter pattern grafted onto an obfuscated proto class; ② `ClientContextHookPatch` — two-phase smali-accumulator DSL over proto builders; ③ `BackgroundPlaybackPatch:105-112` — transitive callee hooking via an ordinal `booleanCalls[1]` pick, encoding knowledge no static analysis would give you.
- agent-5 (misc B): ① method-clone trampoline defeating register pressure while preserving signature and call sites; ② version-aware accumulating endpoint-hook DSL — generated bytecode depends on version flags *and* which patches are included; ③ interface implantation with abstract-superclass fallback chosen by inspecting the hierarchy at patch time.
- agent-6 (shared): ① interface-implant + trampoline combo for obfuscated-class interop; ② the litho filter accumulator — patch-time collaborative codegen inside the extension's own `<clinit>`; ③ the method-clone trampoline as a universal register-starvation fix, composable via the trampoline's known constant index.

Cross-agent consensus: interface implantation (top-3 for 5 of 7 agents) and the method-clone trampoline (top-3 for 2) are the corpus's flagship techniques. The meta-pattern underlying all of it: **resolve everything at patch time, know nothing at build time** — every name, field, method, and register in injected code is derived from a match, never hardcoded.

---
*Researched 2026-07-28 via gh api + shallow clones of MorpheApp org. Maintainer: toxic*
