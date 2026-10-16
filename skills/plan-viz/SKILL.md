---
name: plan-viz
description: >-
  Create a rich, self-contained HTML visualization of an implementation plan.
  Invoke whenever the user asks to visualize a plan, create a plan overview,
  make an implementation plan visual, "show me the plan," "plan as HTML," or
  any request to turn a project plan, roadmap, or architecture into a visual
  artifact. Also trigger when the user mentions wanting mock-ups, code excerpts,
  or maximum context about a plan in a single viewable file. Also trigger
  automatically after a plan is created, saved, or just written (e.g., after
  `writing-plans` produces a plan file). This skill gathers plan content from
  conversation or files and produces a styled HTML file with sections for
  overview, phases, architecture, code/mock-ups, dependencies, risks, and
  success criteria, then opens it in a browser window using the `browser` tool
  (requires a graphical environment; falls back to reporting the file path).
---

# Plan Visualization

Transform an implementation plan into a rich, single-file HTML artifact that
maximizes context at a glance.

## When to Use

- The user says "visualize my plan," "plan overview," "show me the plan"
- The user wants an HTML file representing an implementation plan
- The user asks for mock-ups, code excerpts, or "maximum context" about a plan
- The user wants to communicate a plan to stakeholders or teammates visually
- The user has a written plan (PLAN.md, ROADMAP.md, etc.) and wants it turned
  into a visual artifact

## Workflow

### 1. Auto-detect recently-created plans

Before asking the user, check whether a plan was just created:

1. List `docs/plans/` for `.md` files sorted by modification time (newest first).
2. If no `docs/plans/` directory exists, check the project root for `PLAN.md`,
   `ROADMAP.md`, or `DESIGN.md`.
3. If a candidate file is found, apply two gates **before** auto-selecting it:
   - **Recency gate:** Only auto-select if the file was modified within the
     last 5 minutes. If it is older, treat it as not found.
   - **Content validation gate:** Verify the file contains at least one heading
     (`## `) and at least one of the strings `Goal`, `Plan`, `Architecture`,
     or `Timeline`. If validation fails, treat it as not found.
4. If a valid, recent plan file passes both gates, read it and skip clarifying
   questions. Proceed directly to visualization.
5. If no valid, recent plan file is found, fall back to the existing
   "Gather plan content" logic below.

This makes the skill self-sufficient when invoked immediately after
`writing-plans` saves to `docs/plans/`.

### 2. Gather plan content

If the user has already described the plan in this conversation, synthesize it.
If the plan exists in a file, read it. If neither, ask concise clarifying
questions to elicit:

- What is the goal? What problem does this solve?
- What are the major phases or milestones?
- What are the key components, services, or modules?
- What technologies, libraries, or APIs are involved?
- What does success look like? What are the risks or blockers?

Keep questions minimal — one or two at a time. Do not stall on gathering; use
what you have and produce the artifact.

### 3. Classify the plan

Determine the dominant domain so you know which sections to emphasize:

- **Software / infrastructure** — emphasize architecture, components, data flow,
  API contracts, deployment
- **Data science / ML / statistical modeling** — emphasize data strategy,
  modeling approach, validation, reproducibility, PCS framework
- **Notebook-driven analysis / reporting** — emphasize pipeline stages, outputs,
  visualization strategy, audience
- **Mixed** — balance all of the above

### 4. Load the template

Read `assets/template.html`. It is a self-contained HTML file with embedded CSS.
Fill in the marked sections. Do not alter the CSS or structure unless the user
explicitly asks for a different visual style.

### 5. Fill each section

Replace the placeholder comments in the template with real content. Each section
should be dense with useful information.

#### Title & Metadata
- Project name and one-line summary
- Date, author (if known), plan version

#### Executive Summary
- 3-5 sentences capturing the goal, scope, and expected outcome
- Mention the primary audience (developers, stakeholders, yourself)

#### Phases / Timeline
- List phases with estimated durations
- For each phase: objective, key deliverables, dependencies on prior phases
- Use a simple numbered or card layout; avoid complex JS chart libraries

#### Architecture & Components
- Describe the system structure: services, modules, data stores, external APIs
- Include a text-based diagram or ASCII art if it aids clarity
- Note interfaces, contracts, and trust boundaries

#### Code Excerpts & Mock-ups
- Include 2-4 short, representative code snippets, config samples, or interface
  mock-ups that illustrate the plan
- Choose excerpts that reveal the most about the approach (not boilerplate)
- Use the template's pre-styled `<pre><code>` blocks with language labels
- Escape HTML special characters (`<`, `>`, `&`) inside code blocks so they
  render correctly

#### Dependencies & Risks
- External dependencies: libraries, APIs, teams, approvals
- Risks with severity (High / Medium / Low) and mitigation
- Blockers that must be resolved before a phase can start

#### Success Criteria
- Measurable outcomes: metrics, thresholds, deliverables
- Definition of done for the overall plan and for each phase

### 6. Write and serve the output

1. Save the completed HTML to a file named `<project>-plan.html` (or
   `plan.html` if no project name is obvious) in the current working directory.
2. **Primary output path:** Immediately use the `browser` tool to open the file:
   - `browser` action: `open`
   - `url`: `file://<absolute-path-to-html>`
   - The template is fully self-contained (embedded CSS, no CDN links, no
     external images), so `file://` rendering is correct without the complexity
     of a local HTTP server.
3. **Fallback output path:** If the `browser` call fails or the environment
   lacks a graphical browser, report the absolute file path and exit cleanly
   without retrying.
4. **Alternative output path:** If the user explicitly asks for the file path
   without a browser window (e.g., in a headless or CI context), skip the
   browser step and report the path directly.

## Design Principles

- **Density over brevity.** The user asked for maximum context. Include excerpts,
  mock-ups, and specifics. A 200-line HTML file is better than a sparse one.
- **Scannable structure.** Use headings, cards, and color-coded severity badges
  so a reader can grasp the plan in 30 seconds or read deeply in 5 minutes.
- **Self-contained.** The HTML must have no external dependencies (no CDN links,
  no images unless data URIs). It should render correctly offline.
- **No placeholders.** Every section must have real content. If a piece of
  information is genuinely unknown, state the open question explicitly rather
  than leaving a placeholder.

## Output Format

A single `.html` file written to the filesystem. Provide the file path in chat.


## Integration

- **`writing-plans`** should reference `@skills/plan-viz` after saving a plan
  to `docs/plans/`. The `plan-viz` skill is designed to auto-detect those files
  within a 5-minute recency window.
- **`executing-plans`** should reference `@skills/plan-viz` after loading a plan
  so the user can view it visually before beginning implementation.
- Do not modify the global `writing-plans` or `executing-plans` superpowers
  directly; document the intended hook here for future maintainers.