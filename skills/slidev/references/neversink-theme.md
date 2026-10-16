# Themes

## Primary: neversink

The neversink theme is the default. It is education-oriented with whimsical
elements. Install it:

```bash
npm install slidev-theme-neversink
```

Headmatter for neversink decks:

```yaml
---
theme: neversink
layout: cover
class: text-center
fonts:
  sans: Poppins
  mono: Source Code Pro
  weights: '200,400,600'
---
```

Neversink provides:
- Rich color schemes applied per-slide via `color:` frontmatter
- Custom layouts: `top-title`, `side-title`, `two-cols-title`, `top-title-two-cols`, `quote`, `section`, `intro`, `credits`, `full`
- The `neversink_slug` frontmatter field for branding
- Alignment controls via `align:` frontmatter

See [neversink-layouts.md](neversink-layouts.md) and [neversink-colors.md](neversink-colors.md)
for detailed layout and color reference.

## Secondary: the-unnamed

Use the-unnamed for a darker, more minimal aesthetic. Install it:

```bash
npm install slidev-theme-the-unnamed
```

Headmatter:

```yaml
---
theme: the-unnamed
title: Talk Title
---
```

The-unnamed provides:
- Deep navy background with customizable accent colors
- Layouts: `cover`, `center`, `section`, `two-cols`, `about-me`, `default`
- Full `themeConfig` customization for brand colors

See [the-unnamed.md](the-unnamed.md) for detailed customization options.


# Neversink Layouts

Neversink provides custom layouts beyond Slidev's defaults. All layouts support
the `color:` frontmatter for color scheme application.

## cover

Title slide. Use for the first slide and optionally for major section starts.

```yaml
---
layout: cover
class: text-center
color: amber
---
```

## intro

Introduction slide with large text. Good for setting context after the title.

```yaml
---
layout: intro
color: blue
---
```

## default

Standard content slide. Inherits from Slidev default but with neversink
styling applied.

```yaml
---
layout: default
color: amber
---
```

## top-title

Content slide with a title bar at the top. The workhorse layout for most
content.

```yaml
---
layout: top-title
color: amber
align: lt
---
```

Alignment options via `align:` frontmatter:
- `lt`: left-top
- `lm`: left-middle
- `lb`: left-bottom
- `ct`: center-top
- `cm`: center-middle (default)
- `cb`: center-bottom
- `rt`: right-top
- `rm`: right-middle
- `rb`: right-bottom

## top-title-two-cols

Title bar plus two columns below.

```yaml
---
layout: top-title-two-cols
columns: is-6
align: l-lt-lt
---

::title::

# Title

::left::

Left content

::right::

Right content
```

## two-cols-title

Title area plus two columns. Similar to `top-title-two-cols` but with more
flexible title placement.

```yaml
---
layout: two-cols-title
columns: is-6
align: l-lt-lt
---

::title::

# Title

::left::

Left content

::right::

Right content
```

## side-title

Title in a sidebar with main content beside it.

```yaml
---
layout: side-title
side: left
color: violet
titlewidth: is-4
align: rm-lm
---

::title::

# Sidebar Title

::content::

Main content here
```

Options:
- `side:` `left` or `right`
- `titlewidth:` `is-1` through `is-12` (Bootstrap-style grid)
- `align:` combines title alignment and content alignment, e.g., `rm-lm` means
  right-middle title, left-middle content

## quote

Quotation display with author attribution.

```yaml
---
layout: quote
color: zinc
quotesize: text-m
authorsize: text-s
author: 'Bill James'
---

# "the search for objective knowledge about baseball"
```

Options:
- `quotesize:` `text-xs`, `text-s`, `text-m`, `text-l`, `text-xl`
- `authorsize:` same options
- `author:` attribution text

## section

Section divider. Big text, minimal content.

```yaml
---
layout: section
color: dark
---

# What is Bayes?
```

## full

Full-screen content with no padding. Use for custom layouts or when you need
complete control.

```yaml
---
layout: full
---

Custom content here
```

## credits

Credits / acknowledgments slide.

```yaml
---
layout: credits
---

# Acknowledgments

- Collaborator names
- Funding sources
- Tool credits
```

## Alignment Quick Reference

Neversink uses a two-letter alignment code:

| | Left | Center | Right |
|---|------|--------|-------|
| Top | `lt` | `ct` | `rt` |
| Middle | `lm` | `cm` | `rm` |
| Bottom | `lb` | `cb` | `rb` |

For layouts with two elements (like `side-title`), concatenate two codes:
`rm-lm` means right-middle for the first element, left-middle for the second.


# Neversink Color Schemes

Neversink uses Tailwind-like color schemes arranged in monochromatic pairs.
Apply a color to any slide via the `color:` frontmatter:

```yaml
---
color: amber
---
```

## B&W Schemes

| Color | Description |
|-------|-------------|
| `black` | White text on black background |
| `white` | Black text on white background |
| `dark` | Light gray text on dark gray background |
| `light` | Dark gray text on light gray background |

## Preferred Regular Schemes

Based on usage patterns, these are the most effective:

| Color | Best For |
|-------|----------|
| `amber` | Default content slides. Warm, neutral, professional |
| `violet` | Technical depth, math, algorithms |
| `blue` | Data, methodology, process slides |
| `zinc` | Quotes, reflective content, citations |
| `stone` | Earthy, grounded content. Good for examples |
| `dark` | Section dividers, dramatic transitions |
| `black` | Image-heavy slides where image must dominate |
| `navy` | Deep, serious content. Alternative to dark |

## Light Variants

Use `-light` variants for calm, airy slides with softer contrast:

| Color | Best For |
|-------|----------|
| `amber-light` | Gentle introductions, background material |
| `sky-light` | Open, optimistic content |
| `cyan-light` | Fresh, innovative ideas |

## All Available Colors

**Regular:** `red`, `orange`, `amber`, `yellow`, `lime`, `green`, `emerald`,
`teal`, `cyan`, `sky`, `blue`, `indigo`, `violet`, `purple`, `pink`, `rose`,
`fuchsia`, `slate`, `gray`, `zinc`, `neutral`, `stone`, `navy`

**Light:** `red-light`, `orange-light`, `amber-light`, `yellow-light`,
`lime-light`, `green-light`, `emerald-light`, `teal-light`, `cyan-light`,
`sky-light`, `blue-light`, `indigo-light`, `violet-light`, `purple-light`,
`pink-light`, `rose-light`, `fuchsia-light`, `slate-light`, `gray-light`,
`zinc-light`, `neutral-light`, `stone-light`, `navy-light`

## Color as Structure

Use color to signal structure, not for decoration:

```md
---
layout: section
color: dark
---

# Part 1: Introduction

---
layout: top-title
color: amber
---

# Content slide in intro section

---
layout: section
color: dark
---

# Part 2: Methods

---
layout: top-title
color: violet
---

# Math-heavy methods slide
```

In this example, `dark` signals section boundaries while `amber` and `violet`
carry the content. The audience learns that color change means "pay attention,
structure shift."

## Custom CSS Binding

For custom elements, use neversink's CSS variables:

```html
<div class="neversink-amber-scheme ns-c-bind-scheme">
  This div uses the amber color scheme
</div>
```

Available CSS variables per scheme:
- `--neversink-bg-color`
- `--neversink-bg-code-color`
- `--neversink-fg-code-color`
- `--neversink-fg-color`
- `--neversink-text-color`
- `--neversink-border-color`
- `--neversink-highlight-color`
