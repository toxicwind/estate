---
name: lessons-learned
description: >-
  Automatically augment a skill after it produces friction, misunderstandings,
  or back-and-forth correction. Invoke after a rough interaction with any skill
  using phrases like "that was painful," "fix that skill," "don't make me
  explain that again," "that skill misunderstood me," or /skill:lessons-learned.
  Reads the current session context, identifies the root cause, and surgically
  edits the target skill's SKILL.md so future invocations incorporate the
  correction without manual user intervention.
---

# Lessons Learned: Automatic Skill Augmentation

When a skill interaction goes sideways — extra rounds of clarification,
misunderstood intent, wrong assumptions, skipped steps, or poor output — this
skill captures the root cause and bakes the fix directly into the skill's
instructions.

## Step-by-step workflow

1. **Identify the target skill.**
   - If the user explicitly names a skill, use that.
   - If not, infer from the session context: which skill was most recently
     invoked before the friction started? Which skill's output triggered the
     back-and-forth?
   - If ambiguous, ask the user: "Which skill should I improve?"

2. **Analyze the friction.**
   - Review the current session conversation to identify the specific gap.
   - Categorize the failure mode:
     - **Missing constraint** — the skill allowed an invalid action or assumption.
     - **Wrong default** — the skill chose poorly when multiple options existed.
     - **Ambiguous trigger** — the skill fired when it shouldn't have, or didn't
       fire when it should have.
     - **Skipped step** — the skill omitted a required validation, check, or action.
     - **Poor example** — an existing example in the skill led the agent astray.
     - **Scope creep** — the skill did too much or too little relative to its contract.
     - **Tool misuse** — the skill used the wrong tool or wrong tool arguments.
   - Formulate the lesson as a single, concrete rule or addition.

3. **Load the target skill's `SKILL.md`.**
   - Path: `skills/<name>/SKILL.md`
   - Read the entire file to understand its structure and existing sections.

4. **Determine the surgical edit.**
   - Prefer **additive** changes: add a constraint, add a step, add an example,
     add a clarification.
   - Map the lesson to the most relevant existing section:
     - Workflow gap → add or refine a step in the numbered workflow.
     - Constraint gap → add to the `## Constraints` section.
     - Ambiguity → add to `## Trigger phrases`, `## When to use`, or clarify
       the `description` in the YAML frontmatter.
     - Example gap → add a few-shot example.
     - Output format issue → add to `## Output format`.
   - If no existing section is a clear fit, append a `## Lessons Learned`
     section at the end of the body.
   - **Never** rewrite the YAML frontmatter unless the trigger phrases or
     description are demonstrably wrong.
   - **Never** remove existing content unless it directly contradicts the new
     lesson.

5. **Apply the edit.**
   - Use the `edit` tool with a tight range.
   - After editing, re-read the modified section to verify coherence.

6. **Summarize.**
   - In chat: state the skill, the root cause, and exactly what was added or
     changed. Keep it to one paragraph.

## Constraints

- Only edit `SKILL.md` files under `./skills/`. Never touch extensions,
  themes, or non-skill files.
- Be additive. Preservation beats elegance — append a new bullet rather than
  rewriting a paragraph.
- If you are uncertain about the correct section or wording, produce a draft
  in chat and ask for confirmation before writing.
- Do not change the skill's name in the YAML frontmatter.
- After editing, verify the `SKILL.md` still has valid YAML frontmatter and
  consistent markdown structure.
- If the same lesson applies to multiple skills, edit each one separately.
- If the friction was caused by a bug in the agent or tool, not the skill's
  instructions, say so — do not patch a skill for a platform bug.

## When to stop

- Stop after the `SKILL.md` has been edited and verified.
- If the user says "never mind" or "don't change the skill," stop immediately.
- If the root cause cannot be determined from the session context, stop and
  ask the user to describe the problem in one sentence.
