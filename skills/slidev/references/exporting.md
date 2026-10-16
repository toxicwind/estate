# Exporting and Deployment

## PDF Export

PDF is the standard format for sharing slides. It is reliable, portable, and
works offline.

### Prerequisites

```bash
npm install -D playwright-chromium
npx playwright install chromium
```

### Basic Export

```bash
npx slidev export
```

Output: `slides-export.pdf` in the project root.

### Export Options

| Flag | Purpose | Example |
|------|---------|---------|
| `--output` | Custom filename | `--output my-talk.pdf` |
| `--with-clicks` | Each click step as separate page | `--with-clicks` |
| `--range` | Export subset of slides | `--range 1,5-10,15` |
| `--dark` | Force dark mode | `--dark` |
| `--wait` | Delay before capture (ms) | `--wait 3000` |
| `--timeout` | Max time per slide (ms) | `--timeout 60000` |
| `--with-toc` | Add clickable outline | `--with-toc` |
| `--format` | Output format | `--format pptx` or `--format png` |

### Recommended Export Command

For complex decks with math and images:

```bash
npx slidev export --wait 3000 --timeout 60000 --with-toc
```

### Per-Slide Export Issues

If global layers render incorrectly:

```bash
npx slidev export --per-slide
```

Or use `slide-top.vue` instead of `global-top.vue` for page-specific layers.

## PowerPoint Export

```bash
npx slidev export --format pptx
```

PowerPoint export is useful when the audience needs editable slides. Note that
animations, complex layouts, and custom fonts may not translate perfectly.

## PNG Export

Export individual slides as images:

```bash
npx slidev export --format png --range 1-5
```

Useful for thumbnails, social media, or embedding in documents.

## Static SPA Build

Build a deployable static site:

```bash
npx slidev build
```

Output goes to `dist/`. Deploy to any static host.

### Build with Download Button

Add to headmatter:

```yaml
---
download: true
export:
  format: pdf
  withClicks: false
---
```

The built SPA includes a PDF download button.

## Hosting Options

### Netlify

```bash
npx slidev build
netlify deploy --prod --dir=dist
```

Or use `netlify.toml`:

```toml
[build]
  publish = "dist"
  command = "npx slidev build"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Vercel

```json
{
  "scripts": {
    "build": "slidev build"
  }
}
```

Vercel auto-detects the build command.

### GitHub Pages

Use GitHub Actions:

```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx slidev build --base /my-talk/
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
```

## CI/CD Patterns

### GitHub Actions: Export PDF on Push

```yaml
name: Export PDF
on: push
jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npx playwright install chromium
      - run: npx slidev export --wait 3000
      - uses: actions/upload-artifact@v4
        with:
          name: slides
          path: slides-export.pdf
```

### GitHub Actions: Deploy to Netlify

```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx slidev build
      - run: npx netlify-cli deploy --prod --dir=dist
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

## SEO and Social Sharing

Add Open Graph metadata in headmatter:

```yaml
---
seoMeta:
  ogImage: /images/og-image.png
  twitterCard: summary_large_image
---
```

Create `public/og-image.png` (1200x630) for social sharing.

## Troubleshooting Export

| Symptom | Fix |
|---------|-----|
| Missing content | Increase `--wait` (3000–5000ms) |
| Math not rendering | Increase `--timeout` to 60000ms |
| Broken emojis | Install emoji font on CI runner |
| Wrong colors | Check if `--dark` is needed |
| Blank pages | Verify all image paths resolve |
| Font issues | Ensure fonts are loaded or use system fallbacks |
