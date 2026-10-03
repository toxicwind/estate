# mbx-cache

The estate's direct local [mise](https://mise.jdx.dev/) remote task-cache server.

`mbx-cache` replaces the old flicker/woodpecker build daemon. The old service
queued arbitrary host commands; this service has one narrow contract: store and
restore immutable, content-addressed build outputs for mise tasks and
mr-boxington. Builds remain normal `mise run` executions with the toolchains
declared by each project.

See `SKILL.md` for operation and `ops/mbx-cache/run.sh` for lifecycle.