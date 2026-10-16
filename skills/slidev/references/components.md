# Built-in Components

Slidev auto-imports components from these sources:
1. Built-in components
2. Theme components (neversink, the-unnamed)
3. Addon components
4. `./components/` directory

No import statements needed.

## Navigation

### Link

Navigate to a specific slide:

```md
<Link to="5">Go to slide 5</Link>
<Link to="intro">Go to intro</Link>
```

Use `routeAlias` in frontmatter to create named destinations:

```yaml
---
routeAlias: intro
---
```

### Toc (Table of Contents)

```md
<Toc />
<Toc maxDepth="2" />
<Toc columns="2" />
```

Props:
- `columns`: Number of columns
- `maxDepth` / `minDepth`: Heading depth filter
- `mode`: `all` | `onlyCurrentTree` | `onlySiblings`

Use `Toc` sparingly. A table of contents slide is usually unnecessary for talks
under 30 minutes.

## Animation

### VClick

Show content on click:

```md
<VClick>

This appears after the first click

</VClick>
```

### VClicks

Reveal list items one by one:

```md
<VClicks>

- First point
- Second point
- Third point

</VClicks>
```

Use `v-clicks` for bullet lists where order matters. Do not animate every list.
Reserve for the 2–3 most important lists in the talk.

### VSwitch

Switch between states:

```md
<VSwitch>
  <template #1>State 1</template>
  <template #2>State 2</template>
</VSwitch>
```

## Layout Helpers

### Transform

Scale elements:

```md
<Transform :scale="0.8">
  <img src="/images/logo.png" />
</Transform>
```

Useful for making logos or large images fit without custom CSS.

### AutoFitText

Auto-sizing text that scales to fill available space:

```md
<AutoFitText :max="200" :min="50" modelValue="Hello" />
```

## Media

### Youtube

```md
<Youtube id="dQw4w9WgXcQ" />
<Youtube id="dQw4w9WgXcQ" width="600" height="400" />
```

### Tweet

```md
<Tweet id="1423789844234231808" />
<Tweet id="1423789844234231808" :scale="0.8" />
```

## Conditional Rendering

### LightOrDark

Show different content based on theme mode:

```md
<LightOrDark>
  <template #dark>Dark mode content</template>
  <template #light>Light mode content</template>
</LightOrDark>
```

### RenderWhen

Show content only in specific contexts:

```md
<RenderWhen context="presenter">
  Only visible in presenter mode
</RenderWhen>
```

Contexts: `main`, `visible`, `print`, `slide`, `overview`, `presenter`,
`previewNext`

## Neversink Components

Neversink adds several custom components. Refer to the neversink documentation
for full details:

- **Sticky notes**: `NSNote` for callout boxes
- **Admonitions**: `NSAdmonition` for warnings, tips, notes
- **Bubbles**: `NSBubble` for speech-bubble style annotations

Example:

```md
<NSAdmonition type="warning">

This is a warning callout

</NSAdmonition>
```

## Custom Components

Create `./components/MyComponent.vue`:

```vue
<script setup lang="ts">
defineProps({
  title: String
})
</script>

<template>
  <div class="p-4 border rounded">
    <h3>{{ title }}</h3>
    <slot />
  </div>
</template>
```

Use in slides:

```md
<MyComponent title="Hello">
  Content here
</MyComponent>
```

Keep custom components minimal. Prefer built-in layouts and components unless
you have a repeating pattern that justifies the overhead.
