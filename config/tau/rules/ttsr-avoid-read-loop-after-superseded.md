---
name: ttsr-avoid-read-loop-after-superseded
description: "When read returns superseded content, immediately try a different approach instead of retrying the same file"
condition: ": \"You have received this identical output [0-9]+ times\\. Re-reading '[^']+' will not change it — use a narrower selector|proceed with the edit|different approach\""
scope: "tool:read(*.py)"
---

When a `read` tool returns 'Superseded by a newer read' or similar warnings, NEVER retry the same file with the same selector. Instead: use a narrower selector (path:A-B), switch to a different tool (bash, edit, ffs_find), or proceed with the task using what you already know. Stuck in a loop by repeatedly calling the same failing tool is a defect, not progress. The conversation MUST continue — issue a new tool call with a different approach, or complete the task.