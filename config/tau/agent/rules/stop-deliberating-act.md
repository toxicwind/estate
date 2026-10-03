---
name: stop-deliberating-act
description: "Stop narrating plans and looping over deliberation — issue one concrete tool call or finish"
condition: ["(?i)\\b(let me|i.ll|going to|i will|i.ll just|let.s)\\b.{0,60}\\b(check|verify|look at|read|see|find|wait|confirm|make sure)\\b", "(?i)\\b(still deciding|weighing|considering options|picking between|on the fence|let me think)\\b", "(?i)\\b(for now,? )?(let me )?(re-?)?(summariz|recap)\\b"]
scope: ["text", "thinking"]
---

Stop narrating intended actions. Either issue the tool call, or emit the final answer.

Repeatedly restating a plan — "let me check", "I'll verify", "let me commit", "let me push" — without the corresponding tool call is the defect. The prose has no value; the tool call or the answer does.

When a loop guard fires, you were re-sampling the same context. Break pattern immediately: do not re-plan, do not summarize the state again, do not ask whether to proceed. Pick the most boring viable option and act, or declare the task complete.

Do not narrate intermediate states ("that's confirmed", "good", "fair") as standalone turns either. Combine the acknowledgement with the next real action in the same turn, or drop it.