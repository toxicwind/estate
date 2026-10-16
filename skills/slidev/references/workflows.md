# Getting Started

## Scaffold the Project

Use the scaffold script or do it manually.

### Via Script

```bash
./scripts/scaffold.sh my-talk "Talk Title" "Author Name" "Affiliation"
cd my-talk && npm install && npm run dev
```

### Manually

```bash
mkdir my-talk && cd my-talk
npm install @slidev/cli@^0.51.0 slidev-theme-neversink@^0.3.6 slidev-theme-the-unnamed@^0.0.22 vue@^3.5.0
```

Use [scripts/scaffold.sh](../scripts/scaffold.sh) as the canonical source for
`package.json` and `slides.md` headmatter.

## Create `slides.md` with Headmatter

```md
---
theme: neversink
layout: cover
class: text-center
fonts:
  sans: Poppins
  mono: Source Code Pro
  weights: '200,400,600'
---

# Talk Title

**Author Name**
*Affiliation*

<div class="absolute right-80px bottom-30px">
  <img src="/images/logo.png" width="240" />
</div>

---
```

## Add Image Assets

Create `images/` or `assets/` directory. Reference images with absolute paths:
`/images/my-photo.jpg`. For full-slide backgrounds, use the `image:` frontmatter
or `layout: image`.

## Iterate with Dev Server

```bash
npm run dev
```

Verify at `http://localhost:3030`. Iterate on content before polishing design.


# Workflows

## Add a Slide

### Choose the Right Layout

| Slide Purpose | Recommended Layout | Notes |
|---------------|-------------------|-------|
| Title / cover | `cover` | Keep minimal: title, author, affiliation, logo |
| Full-screen image | `image` | Use `image: /path.jpg` in frontmatter. Add short text overlay if needed |
| Content with heading | `top-title` | Default for most content. Use `color:` for variety |
| Section divider | `section` | Big text, transitional. Use `color:` to signal new section |
| Quote / citation | `quote` | Use `author:` and `quotesize:` frontmatter |
| Image + text side by side | `image-right` or `image-left` | Good for explaining a figure |
| Two concepts compared | `two-cols-title` | Use `::left::` and `::right::` slots |
| Heading + content sidebar | `side-title` | Use `side: left` or `side: right`. Good for section intros |
| Centered single point | `center` | Single image, single equation, or single statement |
| Code walkthrough | `default` or `top-title` | Use fenced code blocks with line highlighting |

### Apply Color Intentionally

With neversink, apply colors via `color:` frontmatter. Preferred colors based on
usage patterns:

| Color | Use Case |
|-------|----------|
| `amber` | Default content slides. Warm, neutral, easy on eyes |
| `black` | Image-heavy slides where you want the image to dominate |
| `violet` / `blue` | Technical depth, mathematical content |
| `zinc` / `stone` | Quotes, citations, reflective moments |
| `dark` | Section dividers, dramatic transitions |

Avoid: `red`, `green`, `yellow` as full-slide backgrounds (harsh or imply
success/failure semantics). Light variants (`amber-light`, `sky-light`) work for
calm, airy slides.

### Write Presenter Notes

Every slide gets notes. Format:

```md
# Slide Title

Slide content here

<!--
Full talking points. Write complete sentences the speaker can read verbatim.
Include citations: (Gelman et al. 2013).
Include transitions: "Next, we'll see how this applies to..."
-->
```

### Keep Text Minimal

- Title: one line, max 6 words
- Body bullets: max 5 per slide, max 6 words each
- Prefer visual explanations over bullet lists
- Use `v-click` to reveal points sequentially instead of showing all at once

## Review a Deck

Run this checklist before declaring a deck complete:

### Content
- [ ] Every slide has exactly one focal point
- [ ] No slide has more than 5 bullet points
- [ ] Every slide has presenter notes
- [ ] Notes contain full sentences, not reminders
- [ ] Math equations are sized with `\Huge` or `\Large`
- [ ] Code blocks use syntax highlighting and line highlighting when relevant

### Visual Design
- [ ] Color changes signal structural transitions, not decoration
- [ ] Images are high-resolution and fill their space intentionally
- [ ] Text contrasts sufficiently with background on every slide
- [ ] Logo placement is consistent (typically `absolute right-80px bottom-30px`)
- [ ] No slide feels crowded; whitespace is intentional

### Narrative Flow
- [ ] Title slide establishes topic, speaker, and affiliation
- [ ] Section dividers appear every 8–12 slides
- [ ] Each section has a clear purpose visible in its first slide
- [ ] The deck builds complexity gradually
- [ ] The final slide provides closure (summary, contact, or call to action)

### Technical
- [ ] `npm run dev` loads without errors
- [ ] All image paths resolve
- [ ] Math renders correctly
- [ ] Code blocks highlight correctly


# Quick Patterns

### Title Slide

```md
---
theme: neversink
layout: cover
class: text-center
fonts:
  sans: Poppins
  mono: Source Code Pro
  weights: '200,400,600'
---

# Talk Title

**Author Name**
*Affiliation*

<div class="absolute right-80px bottom-30px">
  <img src="/images/logo.png" width="240" />
</div>
```

### Full-Screen Image with Overlay

```md
---
layout: image
image: /images/photo.jpg
---

<div class="text-4xl font-bold">
Image Label
</div>
```

### Section Divider

```md
---
layout: section
color: dark
---

# New Section Title
```

### Quote Slide

```md
---
layout: quote
color: zinc
quotesize: text-m
authorsize: text-s
author: 'Author Name'
---

# "The quote text goes here"
```

### Two-Column Comparison

```md
---
layout: two-cols-title
columns: is-6
align: l-lt-lt
---

::title::

# Comparison Title

::left::

Left content

::right::

Right content
```

### Side Title with Content

```md
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

### Code Walkthrough

````md
---
layout: top-title
color: amber
---

# Code Example

```python {1|3-5|all}
def model(x, y):
    with pm.Model() as m:
        alpha = pm.Normal('alpha', 0, 10)
        beta = pm.Normal('beta', 0, 10)
        sigma = pm.HalfNormal('sigma', 1)
        y_hat = alpha + beta * x
        pm.Normal('y', mu=y_hat, sigma=sigma, observed=y)
    return m
```
````

Use `{1|3-5|all}` for click-based line highlighting. Each `|` is a click step.

### Math Slide

```md
---
layout: center
color: blue
---

$$\Huge
\underbrace{\text{Pr}(\theta | y)}_{\textcolor{yellow}{\small \text{Posterior}}}
=
\frac{
  \overbrace{\text{Pr}(y | \theta)}^{\textcolor{yellow}{\small \text{Likelihood}}}
  \cdot
  \overbrace{\text{Pr}(\theta)}^{\textcolor{yellow}{\small \text{Prior}}}
}{
  \underbrace{\text{Pr}(y)}_{\small \text{Evidence}}}
$$
```

### Image Grid

```md
---
layout: center
---

<div class="grid grid-cols-2 gap-4">
  <img src="/images/a.png">
  <img src="/images/b.png">
  <img src="/images/c.png">
  <img src="/images/d.png">
</div>
```
