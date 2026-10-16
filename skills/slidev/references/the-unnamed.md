# The-Unnamed Theme

A dark, minimal theme based on the VS Code theme of the same name. Use as an
alternative to neversink when you want a sleeker, more modern aesthetic.

## Installation

```bash
npm install slidev-theme-the-unnamed
```

## Basic Usage

```yaml
---
theme: the-unnamed
title: Talk Title
---
```

## Layouts

| Layout | Purpose |
|--------|---------|
| `cover` | Title slide with optional background image |
| `center` | Centered content with optional background |
| `section` | Section divider with optional background |
| `two-cols` | Two columns with `::right::` separator |
| `about-me` | Speaker introduction slide |
| `default` | Standard content slide |

### Cover Layout

```yaml
---
layout: cover
background: /images/bg.jpg  # optional
---

# Title

Subtitle
```

### About Me Layout

```yaml
---
layout: about-me
helloMsg: Hello!
name: Chris Fonnesbeck
imageSrc: /images/photo.jpg
job: Principal Scientist
line1: PyMC Labs
line2: Nashville, TN
social1: https://github.com/fonnesbeck
social2: https://fosstodon.org/@fonnesbeck
social3: https://www.fonnesbeck.com
---
```

## Theme Customization

The-unnamed is highly customizable via `themeConfig`:

```yaml
---
theme: the-unnamed
themeConfig:
  color: "#F3EFF5"
  background: "#161C2C"
  code-background: "#0F131E"
  code-border: "#242d34"
  accents-teal: "#44FFD2"
  accents-yellow: "#FFE45E"
  accents-red: "#FE4A49"
  accents-lightblue: "#15C2CB"
  accents-blue: "#5EADF2"
  accents-vulcan: "#0E131F"
---
```

## When to Choose The-Unnamed Over Neversink

Choose the-unnamed when:
- You want a dark theme by default (neversink is light by default)
- The audience is technical and prefers minimal aesthetics
- You need strong code syntax highlighting contrast
- You want a more "product demo" or "startup pitch" feel

Choose neversink when:
- You want per-slide color variety
- Your talk is academic or educational
- You need neversink's rich layout ecosystem
- You want whimsical elements (sticky notes, bubbles)
