# Code Slides and Syntax Highlighting

## Basic Code Blocks

Slidev uses Shiki for syntax highlighting. Specify the language after the
opening backticks:

````md
```python
def model(x, y):
    with pm.Model() as m:
        alpha = pm.Normal('alpha', 0, 10)
        return m
```
````

## Line Highlighting

Highlight specific lines:

````md
```python {2,4-5}
def model(x, y):
    with pm.Model() as m:          # highlighted
        alpha = pm.Normal('alpha', 0, 10)
        beta = pm.Normal('beta', 0, 10)   # highlighted
        sigma = pm.HalfNormal('sigma', 1) # highlighted
        return m
```
````

## Click-Based Highlighting

Reveal code incrementally. Each `|` is a click step:

````md
```python {1|3|5-7|all}
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

Use this for code walkthroughs. Do not animate every code block. Reserve it for
the 2–3 most important examples.

## Line Numbers

Enable globally in headmatter:

```yaml
lineNumbers: true
```

Or per-block:

````md
```python {lines:true}
def hello():
    return "world"
```
````

For technical talks, line numbers are usually unnecessary clutter. Enable only
when referring to specific lines in explanation.

## Monaco Editor

For editable code or live demos:

````md
```ts {monaco}
const x = 1
```
````

For runnable code:

````md
```ts {monaco-run}
console.log('Hello')
```
````

Monaco is heavy. Use it only for interactive workshop sessions, not for
conference talks where the speaker presents and the audience watches.

## Code Import

Import code from external files to keep slides.md clean:

```md
<<< ./snippets/model.py
```

With highlighting:

```md
<<< ./snippets/model.py {2,4-5}
```

Use a `snippets/` directory for imported code.

## Scrollable Code

For long code blocks:

````md
```python {maxHeight:'400px'}
def very_long_function():
    # ... many lines ...
```
````

Prefer splitting long code across multiple slides over scrolling.

## Code in Two-Column Layouts

Code on one side, explanation on the other:

```md
---
layout: two-cols-title
---

::title::

# Model Specification

::left::

```python
with pm.Model() as m:
    alpha = pm.Normal('alpha', 0, 10)
    beta = pm.Normal('beta', 0, 10)
```

::right::

- `alpha`: Intercept prior
- `beta`: Slope prior
- Both are weakly informative
```

## Best Practices

- Keep code blocks under 15 lines on a slide
- Highlight the lines you are discussing
- Use `v-click` to reveal code and explanation together
- Font size: default is usually readable; use `{zoom: 0.8}` on the slide if
code feels cramped
- Always test that code syntax highlights correctly before presenting
