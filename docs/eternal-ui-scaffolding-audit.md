# Eternal Skin/Helper — UX/UI Scaffolding Audit (2026-11-06)

> Critical audit of the eternal skin + helper scaffolding. Upstream (Zaxxon709 /
> FENtastic) code is treated with disgust: the goal is a Bun lib that
> regenerates this scaffolding from a declarative schema, replacing the
> hand-edited monoliths. This audit documents what's wrong, quantitatively.

## 1. The numbers (why this is unmaintainable)

| Metric | Value | Verdict |
|---|---|---|
| XML files in `skin.eternal/xml/` | **143** | Monolithic sprawl |
| Total XML size | **1.6 MB** | One hand-edited blob |
| `Variables.xml` | **91 KB / 172 vars / 533 conditionals** | God-file |
| `Includes_Home.xml` | **85 KB** | God-file |
| `Home.xml` | **69 KB / 90 controls / 158 includes** | God-file |
| `Skin.HasSetting()` conditions in `Home.xml` | **122** | Every pixel gated |
| Hardcoded pixel controls in `Home.xml` | **37** | Layout not data-driven |
| Bare `except:` in helper modules | **14** | Silent error swallowing |
| `cpath_maker.py` (helper) | **1208 lines** | God-module |
| Docs | **README = "# test"** | Nonexistent |

## 2. Concrete anti-patterns (upstream quality)

### 2.1 Condition-spaghetti
Every UI element is gated behind 5+ nested `Skin.HasSetting(...)` conditions.
`Home.xml` has 122 of them; a single toggle (`ClassicEternal`) fans out into
dozens of duplicated control groups (focused/unfocused, classic/plus). The
"Eternal Plus focused layout" comment is literally duplicated verbatim.

### 2.2 Hardcoded pixels
Layout coordinates (`<left>2</left><top>50</top>`) are inline literals, not
variables. 37 in Home.xml alone. Resize/theme = edit 37 numbers by hand.

### 2.3 Silent exception swallowing
The helper has 14 bare `except:` blocks that discard errors. A failed UI
action fails silently — no log, no user feedback, no recovery.

### 2.4 God-files / god-modules
`Variables.xml` (533 conditionals), `cpath_maker.py` (1208 lines). No
separation of concerns; one file owns layout, theming, and behavior.

### 2.5 No docs
The addon README is literally `# test`. No schema, no component inventory,
no theme contract, no build pipeline.

## 3. What a Bun lib fixes (the plan)

A **Bun lib** (`@estate/eternal-ui`) that treats the skin as **data**, not
hand-edited XML:

1. **Declarative schema** — a typed TS schema for controls, layout, themes.
   The 143 XML files become generated output, not source.
2. **Component library** — reusable UI components (hero, widget row, menu,
   dialog) instead of 122 condition-gated copies.
3. **Theme system** — colors/layout as typed tokens, not 37 hardcoded pixels.
4. **Generative pipeline** — `bun build-skin` emits the XML from the schema
   (extends the existing `skin-settings-gen.ts` doctrine).
5. **Hot-reload** — wired to the existing `skin-hot-reload.ts` (150ms UX loop).
6. **Error contract** — no bare `except:`; every helper action logs + recovers.

## 4. Fork candidates

No established node/bun lib generates Kodi skins. The closest reusable pieces:
- **`xml-js` / `fast-xml-parser`** — XML↔JS round-trip (fork for the emitter).
- **`@kodi-fleet`** (estate's own) — the eternal/redlight addons; the schema
  lives here, not upstream.
- **`skin-settings-gen.ts`** — the seed generative pattern (estate-owned).

Build the lib in **`pens/flux`** (build pen) as a standalone product repo.