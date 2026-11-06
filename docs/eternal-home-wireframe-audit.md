# Eternal Home Wireframe Audit (2026-11-06) — with disgust

> The eternal skin's home screen is a Zaxxon-era wireframe that does NOT
> resemble Netflix. This audit documents what's wrong, then the redesign.

## The wireframe (what's actually there)

`xml/Home.xml` = **1428 lines, 90 controls, 22 widget groups**:

- **Sidebar** (`id=9000`): a fixedlist at `left=25, width=492`, items **95px tall**
  with 110px icons, 422px banner highlights, and 5+ condition-gated groups per
  item (ClassicEternal / NoIconMainMenu / NoHighlightMainMenu / ControlGroup(700)).
- **22 widget groups** (`id 2000-28000, 7000-17000`): each a separate
  `grouplist` panel, all condition-gated, stacked on the right at `left=462`.
- **No hero banner** — the "hero" is just the fanart background.
- **No coherent hierarchy** — 22 parallel widget rows, no visual priority.

## Why it's ass (Zaxxon-era anti-patterns)

1. **492px sidebar** — Netflix's sidebar is ~300px, clean icon+label rows.
   This one is wide, cluttered, with 95px-tall items and giant icons.
2. **22 parallel widget groups** — Netflix has a hero + a few rows. This has
   22 condition-gated panels, no hierarchy, no focus.
3. **Condition-spaghetti** — every menu item is gated behind 5+ settings.
   The "Eternal Plus focused layout" comment is duplicated verbatim.
4. **No red accent** — Netflix's #E50914 is absent; the theme uses a muddy
   `button_focus` color.
5. **No hero** — no large backdrop + title + play button on the home screen.

## The Netflix redesign (coherent, not piecemeal)

| Element | Now | Netflix |
|---|---|---|
| Sidebar | 492px, 95px items, giant icons | ~300px, 52px clean rows, red accent bar |
| Hero | none (just fanart) | large backdrop + title + play button |
| Rows | 22 parallel grouplists | hero + a few focused rows |
| Accent | muddy button_focus | #E50914 red |
| Hierarchy | flat (22 groups) | hero dominates, rows secondary |

The redesign is a **single coherent change** to Home.xml: narrow the sidebar,
add the hero, simplify the rows, apply the red accent — not incremental tweaks.