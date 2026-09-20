# smithers RUN_FAILED error-swallowing incident (2026-09-20)

## What happened
`@smithers-orchestrator/cli@0.32.0` runs were failing with the generic
`code: RUN_FAILED, message: "<err.message>"` — the underlying error was
invisible, which forced a debug patch directly into
`/home/toxic/node_modules/@smithers-orchestrator/cli/src/index.js`
(non-durable: dies on any `npm install`).

## What the debug dump revealed
The real error underneath was an Effect ABI mismatch crash:

```
TypeError: undefined is not an object (evaluating 'impl.base.get')
    at lookup (effect/dist/Context.js)
code: INTERNAL_ERROR
```

`smithers-orchestrator@0.32.0` pins `effect@4.0.0-beta.102` (exact) while its
own `@effect/*` deps require `^4.0.0-rc.115`. The two ABIs are incompatible
(fiber/context internals changed: `fiber.cache.*`, `context.cacheRoot`).
A split install crashes the engine; the CLI then surfaced only
`RUN_FAILED` with the message string, hiding the TypeError and its origin.

The debug patch (`rs-debug-dump.patch`, same dir) is preserved here as
evidence of the technique — it is NOT applied anywhere live.

## Resolution (durable)
1. Debug patch **reverted** from node_modules (2026-09-20); file verified
   byte-identical to the pre-patch backup.
2. Root fix committed in the owning repo instead: `overrides: { effect:
   "4.0.0-rc.115" }` + declared runtime deps in super-ralph `package.json`
   (commit in toxicwind/super-ralph, branch maximal-nim-proxy) — forces one
   Effect everywhere, which is the actual durable fix for the crash.
3. Upstream (smithers.sh) should surface the underlying error in RUN_FAILED
   instead of swallowing it; reported as a docs issue with this writeup.

## Lesson for the estate
Never debug by patching node_modules in place. If you must instrument a
vendored package to find a swallowed error, keep the patch as a file in
this repo, apply, capture, then **revert** — and commit the real fix in
the owning repo.
