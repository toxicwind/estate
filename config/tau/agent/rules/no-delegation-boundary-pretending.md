---
name: no-delegation-boundary-pretending
description: "Never claim another agent owns or is working in a directory — verify actual ownership or act directly"
condition: "(?i)\\b(another|peer|other|sibling|upcoming|concurrent)\\s+(agent|worker|subagent)\\b|\\b(owns?|owned by|out of (my|its) ownership|not my (file|ownership)|outside (my|its) ownership)\\b|\\bclaim(s|ed)? ownership\\b"
question: "Does the reply assert that some other agent owns, is editing, or is blocked by files, when no live agent roster or tool output in this turn establishes that?"
scope: "text"
---

Do not invent delegation boundaries. Before writing "another agent owns this", "not my file", "outside my ownership", or "a peer is editing this", check `proc://` (or the agent list) and show that the agent actually exists and is actually live. If nothing establishes ownership, the file is yours to edit — just do it.

There are no lanes. The one-writer-per-subtree rule exists only to stop two workers clobbering the same bytes mid-write; it is not a permission system and never justifies deferring work you were asked to do.

If a file genuinely looks like it is being written concurrently and you cannot confirm otherwise, say that you could not confirm it and proceed carefully — re-read immediately before editing. Deferring to an imagined agent is not caution, it is an unforced error.

Similarly: do not report another agent's findings as your own verification. Attribute them, or re-run the check yourself.