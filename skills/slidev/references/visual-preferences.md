# Author's Visual Preferences

These preferences are distilled from 6 successful slide decks totaling 443
slides. They represent established patterns, not suggestions. Deviations should
be justified.

## Layout Hierarchy

Use layouts in this priority order. The top layouts account for 80% of all
slides across decks.

### 1. `layout: image` (full-screen visuals)

The most common layout. Use when a single image, figure, or photograph carries
the slide.

```md
---
layout: image
image: /images/figure.png
---

<!-- often no text at all; let the image speak -->
```

With text overlay:

```md
---
layout: image
image: /images/photo.jpg
---

<div class="text-4xl font-bold">
  Brief Label
</div>
```

For figure slides that must show the entire image without cropping:

```md
---
layout: image-right
image: /images/figure.png
backgroundSize: contain
---

# Explanation Title

Supporting text or equation here.
```

### 2. `layout: center` (single focal point)

Use for one centered element: an image, a single equation, or a single
statement.

```md
---
layout: center
---

<img src="/images/plot.png" class="mx-auto" />
```

```md
---
layout: center
---

$$
\Huge
\underbrace{\text{Pr}(\theta | y)}_{\text{Posterior}}
=
\frac{
  \text{Pr}(y | \theta) \cdot \text{Pr}(\theta)
}{
  \text{Pr}(y)}
$$
```

### 3. `layout: side-title` (section intros and concept slides)

Title in a sidebar with main content beside it. Very common for introducing new
concepts.

```md
---
layout: side-title
side: l
color: stone
titlewidth: is-4
align: rm-lm
---

::title::

# Concept Name

::content::

Explanation text here.

$$
\Huge \theta \sim \text{Normal}(0, 1)
$$
```

Use `side: l` (left) by default. The `align: rm-lm` means right-middle for the
title, left-middle for the content.

### 4. `layout: top-title` (data and model slides)

The workhorse for content-heavy slides in neversink. Use for model
specifications, code examples, and results.

```md
---
layout: top-title
color: amber
---

::title::

# Model Specification

::content::

```python
with pm.Model() as model:
    alpha = pm.Normal('alpha', 0, 10)
```
```

### 5. `layout: image-right` / `image-left` (figure + explanation)

Image on one side, text on the other. Use `backgroundSize: contain` when the
full image must be visible.

```md
---
layout: image-right
image: /images/distribution.png
backgroundSize: contain
---

# Prior Distribution

Quantifies the **uncertainty** in latent variables.

$$
\Huge \theta \sim \text{Normal}(0, 1)
$$
```

### 6. `layout: two-cols-title` / `layout: two-cols` (comparisons)

For side-by-side comparisons: code vs output, before vs after, two concepts.

```md
---
layout: two-cols-title
---

::title::

# Comparison

::left::

Left content

::right::

Right content
```

### 7. `layout: section` (transitions)

Section dividers. Always use `color: dark`.

```md
---
layout: section
color: dark
---

# Part 2: Methods
```

### 8. `layout: quote` (citations)

```md
---
layout: quote
color: zinc
quotesize: text-m
authorsize: text-s
author: 'Bill James'
---

# "the search for objective knowledge about baseball"
```

### 9. `layout: cover` (title slide)

Keep minimal. Title, author, affiliation, logo.

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

### 10. `layout: default` / `layout: full` (custom content)

Use `full` when you need complete control with no theme padding. Use `default`
for simple custom layouts.

```md
---
layout: full
color: black
---

<img src="/images/fullbleed.jpg" class="w-full" />
```

## Color Usage Patterns

### Neversink Color Distribution

Across 6 decks, colors are used in this proportion:

| Color | Frequency | Purpose |
|-------|-----------|---------|
| `amber` | ~60% | Default content slides. Warm, neutral, professional |
| `dark` | ~15% | Section dividers and dramatic transitions |
| `zinc` / `stone` | ~10% | Quotes, citations, reflective moments |
| `blue` / `violet` | ~8% | Technical depth, mathematical content |
| `black` | ~5% | Image-heavy slides where the image must dominate |
| `cyan` / `navy` | ~2% | Occasional accent for variety |

### Color Rules

- **Never** use `red`, `green`, or `yellow` as full-slide backgrounds. They are
  harsh and imply success/failure semantics.
- **Never** use random color variations. A color change signals a structural
  shift.
- Section dividers are always `color: dark`.
- Quotes are typically `color: zinc` or `color: stone`.
- Math-heavy slides can use `color: blue` or `color: violet` for visual
  distinction.

## Typography Rules

### Math Sizing

**Always** size display math with `\Huge` or `\Large`. Default LaTeX size is
unreadable from the back row.

```md
$$
\Huge
\text{Pr}(\theta | y) = \frac{\text{Pr}(y | \theta) \text{Pr}(\theta)}{\text{Pr}(y)}
$$
```

For inline math within text, keep it simple. Complex expressions belong in
display mode.

### Code Sizing

Code blocks should be readable. For neversink, use the custom class to increase
font size:

````md
```python {all}{class:'!children:text-2xl'}
def model(x, y):
    with pm.Model() as m:
        alpha = pm.Normal('alpha', 0, 10)
```
````

Use `text-2xl` for most code blocks, `text-1xl` for very long blocks that need
to fit.

### Title Sizing

Default heading sizes are usually sufficient. For extra impact, use inline
styles sparingly:

```md
<h1 style="font-size: 3em;">Big Title</h1>
```

### Transform Scaling

Use `<Transform :scale="N">` for resizing specific elements:

| Scale | Use Case |
|-------|----------|
| `0.3` | Logos on title slides |
| `1.2` | Images that need slight enlargement |
| `2.0` | Key equations or single symbols |
| `6.0` | Single mathematical symbols (e.g., $\hat{\theta}$) |

```md
<Transform :scale="6">

$\Huge \hat{\theta}$

</Transform>
```

## Image Placement Patterns

### Logo Placement

Place logos consistently, typically bottom-right:

```md
<div class="absolute right-80px bottom-30px">
  <img src="/images/logo.png" width="240" />
</div>
```

For the-unnamed theme, a slightly different position:

```md
<div class="absolute bottom-5 right-5">
  <img src="/images/logo.png" alt="logo" width="240" />
</div>
```

### Image Grids

For multiple figures, use CSS grid:

```md
<div class="grid grid-cols-2 gap-4">
  <img src="/images/a.png">
  <img src="/images/b.png">
  <img src="/images/c.png">
  <img src="/images/d.png">
</div>
```

For flexible layouts, use flexbox:

```md
<div style="display: flex; justify-content: space-between;">
  <img src="/images/a.png" style="width: 32%; margin-right: 1%;">
  <img src="/images/b.png" style="width: 32%; margin-right: 1%;">
  <img src="/images/c.png" style="width: 32%;">
</div>
```

### Background Images

Any slide can have a background image:

```md
---
background: /images/background.jpg
---

# Slide content overlays the image
```

Use this for photographs that set mood while text provides context.

### Full-Bleed Images

For images that must fill the entire slide with no padding:

```md
---
layout: full
color: black
---

<img src="/images/fullbleed.jpg" class="w-full" />
```

Or with `layout: image`:

```md
---
layout: image
image: /images/fullbleed.jpg
---
```

## Presenter Notes Discipline

Every single slide must have presenter notes. No exceptions.

### Format

```md
# Slide Title

Slide content

<!--
Full talking points written as complete sentences. The speaker should be able
to read these verbatim if needed.

Include citations: (Gelman et al. 2013).
Include transitions: "Next, we will see how this applies to..."
Include anticipated questions and brief answers.
-->
```

### Content Guidelines

- Write complete sentences, not fragments or reminders
- Include all citations and sources
- Provide transition sentences to the next slide
- Add timing cues for demos if relevant
- Never write one-word reminders like "explain this"

### Hiding Slide Numbers

On some slides (like full-screen images or videos), hide the slide number:

```md
---
layout: image
image: /images/figure.png
slide_info: false
---
```

## Progressive Reveal Patterns

### v-click for Staged Reveals

Use `v-click` to reveal content progressively. This is especially effective for
building up an argument or showing before/after states.

```md
<div v-click>

## First point appears on click

</div>

<div v-click>

## Second point appears on next click

</div>
```

### Click-Based Code Highlighting

Reveal code line by line:

````md
```python {1|3-5|all}{class:'!children:text-2xl'}
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

Use `|` to separate click steps. `all` reveals everything on the final click.

## Neversink-Specific Components

### SpeechBubble

Use for callout text overlaid on images:

```md
---
layout: image
image: /images/background.jpg
---

<br>
<SpeechBubble position="br" color='sky' shape="round" maxWidth="300px">

## Data are **random**

</SpeechBubble>
```

Positions: `tl`, `t`, `tr`, `l`, `r`, `bl`, `b`, `br`.

### Admonition

Use for styled callout boxes within content:

```md
<Admonition title="The Likelihood Principle" color='zinc'>

The likelihood function contains all of the information about the data relevant
to inference.

</Admonition>
```

## Structural Patterns

### Section Divider Cadence

Insert section dividers every 8–12 slides. This gives the audience a mental
reset.

```md
---
layout: section
color: dark
---

# New Section Title
```

### Deck Arc

A typical deck follows this arc:

1. **Title slide** (`layout: cover`): Topic, speaker, affiliation, logo
2. **Context slides** (`layout: image`, `layout: center`): Hook the audience
3. **Core content** (`layout: top-title`, `layout: side-title`): The meat of the
talk, building complexity gradually
4. **Section dividers** (`layout: section`, `color: dark`): Reset every 8–12
slides
5. **Application slides** (`layout: two-cols-title`, `layout: image-right`):
Real-world examples
6. **Closing slide** (`layout: end` or `layout: center`): Thank you, contact,
or key takeaways

### The Closing Slide

Keep the closing simple:

```md
---
layout: center
---

<div class="text-8xl font-bold text-center">
  Thank You!
</div>

<div class="flex justify-center">
  <Email v="email@example.com" class="text-2xl" />
</div>
```

Or with key takeaways:

```md
---
layout: center
color: amber
---

# Key Takeaways

1. Gaussian processes model distributions over functions
2. PyMC makes GP specification intuitive
3. Always check your posterior predictive
```

Never end with only "Thank you" and no other content. Provide closure.
