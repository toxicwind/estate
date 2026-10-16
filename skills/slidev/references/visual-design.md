# Core Design Principles

These rules are non-negotiable. They reflect what works for technical
audiences.

## One Idea Per Slide

Each slide communicates exactly one concept. If you find yourself wanting two
titles, split it. The presenter notes carry the nuance; the slide carries the
punchline.

## Visuals Dominate, Text Supports

When an image explains the concept, let it fill the slide. Text should be
minimal: a title, a short label, or a single equation. Never put a paragraph on
a slide.

## Color Signals Structure

Use color intentionally, not decoratively. A color change should tell the
audience "new section," "important point," or "contrast." Random color
variations create noise.

## Math Must Be Readable

Equations are central to data science talks. Default size is too small. Use
`$$\Huge ... $$` or `$$\Large ... $$` for displayed math. Inline math should be
rare; when used, keep it simple.

## Presenter Notes Are the Script

Write full talking points in HTML comments. Notes should contain:
- The complete verbal explanation of the slide
- Citations and sources
- Transition sentences to the next slide
- Answers to anticipated questions

Never leave notes empty or write one-word reminders like "explain this."


# Visual Design Principles for Technical Slides

## Typography

### Font Size Hierarchy

| Element | Size Guidance |
|---------|---------------|
| Slide title | `text-4xl` or larger. Must be readable from the back row |
| Section headers | `text-3xl` |
| Body text | Default (`text-xl` in neversink). Never smaller |
| Captions / labels | `text-lg` |
| Math equations | `\Huge` or `\Large` always |
| Code | Default is fine; line highlighting draws attention |

### Font Choices

Neversink defaults:
- Sans: Poppins (friendly, modern)
- Mono: Source Code Pro (clear distinction for code)

Override in headmatter:

```yaml
fonts:
  sans: Poppins
  mono: Source Code Pro
  weights: '200,400,600'
```

For the-unnamed, the theme handles fonts. Do not override unless you have a
specific brand requirement.

## Whitespace

Whitespace is not empty space. It is a design element that directs attention.

Rules:
- Never fill more than 60% of a slide with content
- Padding around images should be consistent (default theme padding is usually
correct)
- When using `layout: center`, the single element should have room to breathe

## Color and Contrast

### Contrast Requirements

All text must pass WCAG AA against its background:
- Normal text: 4.5:1 minimum
- Large text (18pt+): 3:1 minimum

Neversink color schemes are pre-calculated to meet these ratios. When using
`layout: image` with text overlay, ensure the image has dark areas where text
sits, or add a semi-transparent background:

```html
<div class="bg-black/50 p-4 rounded">
  Text on image
</div>
```

### Color Psychology for Data Science Talks

These are the only background colors used across the author's decks. Never use
red, green, or yellow as a full-slide `color:` background. They are harsh,
imply success/failure semantics, and fail accessibility checks for color
blindness.

| Color | Association | Use For |
|-------|-------------|---------|
| `amber` | Warmth, accessibility | Default content, introductions, explanations |
| `blue` | Trust, data, stability | Methods, results, data slides |
| `violet` | Intelligence, complexity | Algorithms, theory, math |
| `zinc` / `stone` | Neutrality, reflection | Quotes, citations |
| `dark` / `black` | Seriousness, transition | Section dividers, image-heavy slides |

For semantic emphasis within a slide (colored text, highlights, annotations),
use any Tailwind color via `\textcolor{name}{...}` in math or inline HTML
styles. Those are inline accents, not backgrounds, and are not subject to the
background-color restriction.

## Image Usage

### Full-Screen Images

Best for: photographs, complex diagrams, data visualizations that need space.

```md
---
layout: image
image: /images/plot.png
---

<div class="text-4xl font-bold bg-black/50 p-4 rounded">
  Figure Label
</div>
```

### Image Grids

For comparing multiple figures:

```md
<div class="grid grid-cols-2 gap-4">
  <img src="/images/a.png">
  <img src="/images/b.png">
  <img src="/images/c.png">
  <img src="/images/d.png">
</div>
```

Use `gap-4` minimum. Images should be the same aspect ratio for visual rhythm.

### Image Quality

- Minimum resolution: 1920x1080 for full-screen images
- Preferred formats: PNG for plots, JPG for photographs
- Use `backgroundSize: contain` when the full image must be visible
- Use `backgroundSize: cover` (default) when the image can be cropped

## Logo and Branding

Place the logo consistently, typically bottom-right:

```html
<div class="absolute right-80px bottom-30px">
  <img src="/images/logo.png" width="240" />
</div>
```

On neversink, use `neversink_slug` for institutional branding:

```yaml
---
neversink_slug: 'PyMC Labs'
---
```

Keep logos subtle. They should not compete with slide content.


# Anti-Patterns

Avoid these common mistakes:

**Bullet-point walls.** If a slide has more than 5 bullets, turn it into
multiple slides, a diagram, or a table.

**Decorative images.** Every image should convey information. If removing the
image would not reduce understanding, remove it.

**Tiny math.** Default LaTeX size is unreadable from the back row. Always size
up equations.

**Animation overuse.** `v-click` is for revealing steps in an argument. Do not
animate every bullet point on every slide. It slows pacing and frustrates
audiences.

**Inconsistent branding.** Logo position, color palette, and font choices should
be consistent across all slides. Pick a scheme in headmatter and stick to it.

**Empty presenter notes.** Notes are the script. Write them fully.
