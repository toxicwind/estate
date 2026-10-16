# Storytelling and Narrative Structure

## The Arc of a Technical Talk

A strong technical presentation follows a recognizable structure:

1. **Hook** (1–2 slides): Why should the audience care?
2. **Context** (2–4 slides): What do they need to know to follow?
3. **Core content** (60% of slides): The meat of the talk
4. **Synthesis** (2–3 slides): What does it all mean?
5. **Closing** (1 slide): Clear takeaway or call to action

## Slide Pacing

| Talk Length | Target Slide Count | Notes per Slide |
|-------------|-------------------|-----------------|
| 15 minutes | 15–20 slides | 30–45 seconds of content |
| 30 minutes | 25–35 slides | 45–60 seconds of content |
| 60 minutes | 40–55 slides | 60–90 seconds of content |

Plan for fewer slides than you think. Audience comprehension drops after 45
minutes regardless of slide count.

## The Hook

The first two slides determine whether the audience leans in or checks out.

Effective hooks:
- A surprising statistic or result
- A concrete problem the audience faces
- A provocative question
- A striking image that encapsulates the talk's theme

Avoid:
- Table of contents (wastes the hook moment)
- "About me" slides (save for later or omit)
- Agenda slides (audiences forget them immediately)

## Section Dividers

Insert a `layout: section` slide every 8–12 slides. This gives the audience a
mental reset and signals a new chapter.

```md
---
layout: section
color: dark
---

# Part 2: Methods
```

The section title should answer: "What is this section about and why does it
matter?"

## Building Complexity

Structure the core content as a staircase:

```
Simple concept A
    -> Extension B builds on A
        -> Extension C builds on B
            -> Full system D combines A, B, C
```

Never introduce concept C before the audience understands B. Each slide should
feel like a natural next step, not a jump.

## Presenter Notes as Narrative

Write notes as a continuous narrative, not bullet points:

```md
<!--
We just saw that linear models fail when relationships are non-linear. That
brings us to Gaussian processes. A GP is a distribution over functions, not
just over parameters. This is the key insight: instead of assuming a particular
functional form, we put a prior directly on the space of possible functions.

Transition: "To understand how this works, let's look at the multivariate
Gaussian..."
-->
```

Good notes contain:
- Complete sentences the speaker can read aloud
- Citations for claims
- Transitions to the next slide
- Answers to likely questions
- Timing cues for demos ("pause here for 3 seconds")

## The Closing Slide

The last slide should be the one the audience remembers. Options:

**Summary:**
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

**Call to action:**
```md
---
layout: center
color: blue
---

# Try It Yourself

```bash
pip install pymc
```

https://www.pymc.io
```

**Contact:**
```md
---
layout: center
---

# Questions?

**Chris Fonnesbeck**

GitHub: @fonnesbeck
Fosstodon: @fonnesbeck
Web: fonnesbeck.com
```

Never end with "Thank you" as the only content. It is a wasted slide.

## Anti-Patterns in Narrative

**The reference manual talk.** Do not walk through every parameter of an API.
Audiences can read documentation. Focus on the 3 things that matter most.

**The incremental reveal with no payoff.** If you spend 10 slides building up
to a result, the result must be worth it. Test: if you revealed the result on
slide 2, would the talk still be valuable? If yes, you are burying the lede.

**The shaggy dog story.** Every slide must earn its place. If you can remove a
slide and the argument still holds, remove it.
