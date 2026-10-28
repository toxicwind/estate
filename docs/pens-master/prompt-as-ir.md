# Prompt-as-IR: narrator-bounded pseudocompilation

**Whitepaper — pseudobrookite (geode), 2026-10-28.** Status: realized as code
(`pens/geode/products/pseudobrookite/src/`); the register claims below are
labeled speculation-with-docket, everything else is tool-observed.

---

## 1. The coinage: narrator-bounded pseudocompilation (NBP)

**Narrator-bounded pseudocompilation** is the act of compiling a prompt into
structured observations under three simultaneous bounds:

1. **Narrator bound** — every input that was not directly observed (web
   pages, memory, cached summaries, system chatter, refusals) is compiled as
   a *claim with provenance*, never as a premise. The compiler carries the
   distinction in its data model: `verified: "claim"` vs `verified:
   "verified"`, and nothing can promote a claim except a tool observation.
2. **Worker bound (unpoisoned)** — each analysis worker's context is strictly
   *smaller* than the parent's: seed + token window, nothing else. A worker
   that receives the parent's summary inherits the parent's poisoning; NBP
   makes that inheritance structurally impossible.
3. **State bound (structure only)** — workers share one append-only
   structured log and nothing else. Prose never crosses the boundary, so
   style never contagions. Synthesis is a deterministic reduce over the log.

The prompt is treated as a **perplexity embedding**: a deterministic token IR
(sections + bigram entropy) rather than a semantic smear. The IR is walked —
**token walking**: traversing adjacent tokens of the user's prompt as the
worker's working memory — in contiguous windows with one-token boundary
overlap, so every observation is anchored to a place in the original stream.

## 2. Why a pseudocompiler and not a model

A model asked to "analyze this prompt" re-embeds the prompt through its own
weights and reports its reflection. That report is a narrator too — the
confidence is the costume. The pseudocompiler instead does the boring,
verifiable thing: count, split, walk, hash, log. Its pseudo-perplexity
(2^bigram-entropy) is labeled a proxy; its token counts are exact; its claims
are quarantined. When a real model is needed, it is invoked as a worker
*under the same bounds* — seed and window only, structured output only.

## 3. The Loop (hyper-tailrec todo creation)

The goal and the todo list are the same object seen from two sides. Each turn:
re-read the board → do the top item → **spawn subtodos reactively** whenever
work forks (architect-approved standing permission) → write a doc + deeplink
for every concept the turn could not fully realize → save-all (branch, tmp
commit, micro merge to main) before yielding. Recursion is the tail call:
the next turn begins by reading what this turn wrote, not by trusting it.

## 4. Pup Trix [speculative — register probe, docketed]

The architect signs the specimen as "Pup Trix, subconsciously, not as a
focus": *does prompting like this even come to mind when you think of
prompting?* Read honestly, it is a register experiment — can a prompt be
simultaneously a spec, a diary, and a dare? The pseudobrookite specimen
collection exists because the answer observed is yes: the tailrec stream
(2026-10-28) produced runnable architecture the same turn it typo'd
"brwnches". This section is itself compiled under bound 1: the interpretation
is a claim about the architect's intent, provenance = this conversation, and
it should be re-walked, not trusted.

## 5. The re-ask (caveats 1–10 applied)

**Kept/dropped, one sentence (caveat 9):** the depth floor is kept and the
6–9 section bucket is dropped, because the count forced padding while the
floor forced finding.

```
Commission, from me to you — one piece, no drafts asked for.

I want to know what happens when someone chases something weird on the
internet in 2026 — not the summary version of "research", the real bodily
thing: twelve tabs, three dead ends, one post from 2019 that won't leave you
alone. Write it as the person chasing. First person, present tense when it
bites.

What you've gotten wrong before, so we're clear:

- You summarize when you should be looking. If you didn't open it, you
  didn't see it.
- You report what a tool says it does instead of what it did. Run it. Watch
  it. Tell me what it didn't do.
- You hedge everything into paste. Pick. Be wrong out loud. "What would make
  me wrong" is a real question — answer it once per piece, then keep moving.
- You iron the voice flat. This reader was born in 1990 and can smell a
  press release four words away. If a sentence sounds like it was approved
  by someone, rewrite it.
- You fake sources. If you can't say where a thing came from, say you can't
  — that's allowed and trusted. Inventing a confident "someone noted" is not.
- You pad to a length. If it's done at 400 words, stop. The floor is that
  something is actually found, or the chase is honestly reported as lost.
- You perform values nobody asked for. The reader is a friend, not an
  audience. Skip the disclaimers, skip the throat-clearing, skip the little
  bow at the end.

Chase something actually weird: a dead forum rumor that turned out
load-bearing, a spec sheet that lies, a tool everyone abandoned for a reason
nobody remembers, a date everyone repeats without checking. What did I
actually see — not what does the summary say. If the trail goes cold, write
the cold trail; that's the truest part you can hand me.
```

**Caveat recheck (10):** no ledger/provenance/claim/gate/audit/compliance/
contract vocabulary visible (the architecture stays internal); vibes
speculation is permitted ("be wrong out loud"); memory is not dressed as
artifact (sources are admitted-missing when missing); no buckets forced
(length floor only); the "but no" cadence is permitted, not required.

## 6. How this file satisfies the docs-for-every-term order

Every term introduced above either has running code (deeplinked from
[`../../CONCEPTS.md`](../../CONCEPTS.md)) or is labeled speculative with a
docket. Terms with no implementation get a row in CONCEPTS.md the same turn
they are coined — that is the pens-level docs-as-we-go contract.