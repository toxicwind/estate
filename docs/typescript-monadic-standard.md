# Estate TypeScript error-handling: `Result`/`TaskEither` (fp-ts) vs `Effect`

> Decision doc — 2026-11-01. Resolves the tension between the AGENTS.md-stated
> standard ("compose pipelines as `Result`/`Ok`/`Err` or `TaskEither`") and the
> de-facto `effect` dependency already shipped in several estate products.

## 1. The tension

- **AGENTS.md §3.3** ("Implementation Style") names `Result`/`Ok`/`Err` or
  `TaskEither` chains as the monadic standard. `fp-ts` is the implied engine.
- **Reality (verified 2026-11-01):** `effect` (effect@4) is already installed
  and used in thresher (Go proxy aside, its TS tooling), kappa-code, and now
  dedicated-mcp (the universal MCP registry handlers are `Effect.tryPromise`
  chains). None of those products depend on `fp-ts` at runtime.

So the written standard and the running code disagree. Two truths are a bug —
this doc picks a resolution.

## 2. Head-to-head

| Axis | `fp-ts` `Result`/`TaskEither` | `effect` |
|---|---|---|
| Type story | tagged unions (`Left`/`Right`) via `Either`; `TaskEither` for async | typed `Effect<Success, Error, R>` with higher-kinded `R` (Requirements); no HKT abstraction leak |
| Error channel | `E` is one union; composition threads it by hand or `chain` | `Error` is a first-class typed channel; `Effect.fail`/`tryPromise`/`mapError` compose naturally |
| Async | `Task`/`TaskEither` (lazy `Promise`) | `Effect` is lazy + trampolined; `Effect.runPromise` at the edge |
| Dependency injection | manual closure/reader | `Services`/`Effect.gen` with `R` tracked — DI at type level |
| Concurrency | manual | `Effect.all`, `Fiber`, structured concurrency built-in |
| Static output | small; `fp-ts` 2.x is a functional-library, bring-your-own-pipe | one coherent runtime; larger but batteries included |
| Learning curve | fp-ts knowledge; HKT signatures get dense | one unified model; simpler end-to-end but a bigger vocabulary |
| Estate track record | none at runtime (doc-only) | thresher tooling, kappa-code, dedicated-mcp (shipping) |

## 3. Decision

**Adopt `effect` as the estate's TypeScript monadic standard**, and treat the
AGENTS.md `Result`/`Ok`/`Err` / `TaskEither` wording as the *concept* (a labelled
error channel + composition), not a mandate for the `fp-ts` package.

Reasons:
1. **Code is absolute** (AGENTS.md §1.5). The running estate already converges on
   `effect`; the doc must follow the code, not the other way.
2. `effect` gives the same "fail-fast, typed error channel" discipline the
   `TaskEither` wording was after, without a second dependency family.
3. `Result`/`TaskEither` and `Effect` are the same shape of tool; `effect` bundles
   the concurrency/interruption the estate needs for daemon-style code.

## 4. Rule going forward

- New TS products / handlers: use `effect` (`Effect.tryPromise`, `Effect.gen`,
  `Effect.mapError`). **Never** `throw` a bare error out of a handler — map it to
  an `Effect.fail`/typed result so the error channel is explicit.
- Do **not** add `fp-ts` to new code. Existing code that already ships fp-ts
  (none confirmed at runtime) may stay until touched, then migrate.
- Update **AGENTS.md §3.3** wording to say `effect` (the earlier turn's doc fix)
  so the written contract matches reality.

## 5. Reference

- `effect` 4.x docs: https://effect.website
- In-tree examples: `pens/dedicated/products/dedicated-mcp/src/pen/geode-trio.ts`
  (Effect.tryPromise handlers returning typed tool content).