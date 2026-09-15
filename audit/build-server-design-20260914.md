# Build Server Design — awrawr-pc (2026-09-14)

## Recommendation: Dagger + Self-Hosted GitHub Actions Runner

**Don't reinvent.** The cutting-edge pattern as of Sept 2026 (documented Aug 2026,
[Medium](https://medium.com/@sriram8438/scalable-ci-cd-with-github-actions-dagger-73f05dd70b67)):
GitHub Actions handles **triggers** (on push) and CI integration; **Dagger** handles
the reusable pipeline logic (programmable, containerized, cached, traced).

### Why Dagger (not alternatives)

| Option | Verdict |
|--------|---------|
| **Dagger** | ✅ Programmable CI/CD engine. Pipelines as code (8 language SDKs). Containerized, repeatable, OpenTelemetry-traced. Local-first: same pipeline runs on laptop, CI, or cloud. Only needs a container runtime. |
| Earthly | Viable but less programmable; Dagger's module ecosystem + tracing wins. |
| Nix/Devenv 2.x | Great for reproducible dev envs, heavier adoption curve. devenv 2.2 (Jul 2026) adds "attach to running processes" — interesting for future, not for CI now. |
| Bazel/Buck2 | Overkill for polyglot repos. Dagger handles any language via containers without BUILD file sprawl. |
| Raw shell scripts | ❌ Not repeatable, not cached, not traced. |
| GitHub-hosted runners | Blocked: private-repo Actions $0 spending limit kills jobs in 2–4s (proven). Self-hosted is the only path. |

### Why this fits awrawr-pc

- Docker 29.6.2 installed and **active** (Dagger's only hard dependency) ✅
- 16 cores x86_64 — plenty for parallel containerized builds ✅
- Passwordless sudo works ✅
- Self-hosted runner already staged at `~/actions-runner-nsl/` (not yet configured) ✅
- Languages: Python, TypeScript/Bun, Rust, Go — all via Dagger container pipelines ✅

## Architecture (text diagram)

```
  GitHub push (any repo)
        │
        ▼
  ┌─────────────────────────────┐
  │ GitHub Actions workflow     │  ◄── triggers only: on: [push]
  │ (dagger/dagger-for-github)  │      calls Dagger module ci()
  └──────────────┬──────────────┘
                 │ runs-on: self-hosted
                 ▼
  ┌─────────────────────────────┐
  │ awrawr-pc (Arch, 16 cores)  │
  │                             │
  │  pitchfork daemon:          │
  │  ┌───────────────────────┐  │
  │  │ actions-runner        │──┼──► polls GitHub for jobs
  │  │ (~/actions-runner-nsl)│  │    auto-restart, boot_start
  │  └───────────┬───────────┘  │
  │              │ job received │
  │              ▼              │
  │  ┌───────────────────────┐  │
  │  │ Dagger engine         │  │
  │  │ (container via Docker)│  │
  │  └───────────┬───────────┘  │
  │              │              │
  │   ┌──────────┼──────────┐   │
  │   ▼          ▼          ▼   │
  │ ┌─────┐  ┌──────┐  ┌──────┐ │
  │ │Python│ │TS/Bun│  │Rust/Go│ │  ◄── parallel, cached,
  │ │test  │  │build │  │build │ │      streamed logs
  │ └─────┘  └──────┘  └──────┘ │
  └─────────────────────────────┘
        │
        ▼
  Streaming logs → GitHub Actions UI
  (Dagger emits OpenTelemetry traces + granular logs)
```

### Data flow per commit

1. `git push` → GitHub Actions triggers workflow
2. Workflow calls `dagger/dagger-for-github` with `module: <org>/<repo>/.dagger`, `args: ci --source=.`
3. Self-hosted runner on awrawr-pc picks up the job
4. Dagger engine spins up containers per language (Python/pytest, Bun, cargo, go)
5. Each step cached (content-addressed); only changed layers rebuild
6. Logs stream to Actions UI in real time (no batch-and-pray)
7. Artifacts (binaries, test reports) returned as Dagger outputs

## pitchfork Daemon Definition (draft)

```toml
# /home/toxic/sovereign/pitchfork.toml — append

[daemons."build-runner"]
command = "/home/toxic/actions-runner-nsl/run.sh"
workdir = "/home/toxic/actions-runner-nsl"
retry = true
boot_start = true
# env: RUNNER_TOKEN set via systemd EnvironmentFile (0600), NOT in toml
env_file = "/home/toxic/.config/build-runner.env"
```

Notes:
- The runner itself is the daemon (long-lived, polls GitHub). Dagger is
  invoked per-job, not as a daemon — it doesn't need to be.
- `run.sh` blocks polling; pitchfork `retry=true` + `boot_start=true`
  gives persistence across crashes and reboots.
- Token lives in `env_file` (mode 0600), never in the toml or repo.

## Language Support Matrix

| Language | Dagger approach | Container base |
|----------|----------------|----------------|
| Python | `python:3.12` + pip/uv | Official python image |
| TypeScript/Bun | `oven/bun:1` | Official bun image |
| Rust | `rust:1.8x` + cargo | Official rust image |
| Go | `golang:1.2x` | Official golang image |

All run as Dagger container operations — reproducible, cached, no host
pollution. New language = new container, not a host install.

## Audit: Persistence / Permanence / Connectivity / Restart

| Concern | Status |
|---------|--------|
| **Persistence** (survives reboot?) | Runner via pitchfork `boot_start=true` → yes. Docker daemon via systemd → yes. Dagger engine is ephemeral per-job (by design). Build cache persists in Docker volumes. |
| **Permanence** (pitchfork-owned?) | Runner WILL be pitchfork-owned (definition above). Dagger CLI installed via mise (version-pinned). No manual nohup. |
| **Connectivity** (reachable from cell?) | Cell doesn't need direct access — GitHub Actions is the trigger plane. Cell can poll job status via `gh` API. Runner polls GitHub outbound (no inbound needed). |
| **Restart failures** | Runner: pitchfork retry handles crashes. Docker: systemd handles it. Dagger: per-job, no state to lose. Cache: Docker volumes survive. Worst case: cold cache rebuild (slower, not broken). |

## What Needs Chris's Approval

1. **GitHub runner registration token** — generate from repo/org Settings → Actions → Runners → "New self-hosted runner". This is the only secret needed. Cannot proceed without it.
2. **Which repos get Dagger CI first** — recommend starting with `toxicwind/squawk` (our own, low risk), then rolling out.
3. **Dagger module location** — `.dagger/` dir in each repo, or a shared org-level module? Recommend per-repo `.dagger/` calling a shared module for DRY.
4. **Resource limits** — 16 cores shared with other services. Recommend Dagger `--parallel` cap or cgroup limits if builds contend with live services.

## Implementation Steps (after approval)

1. `config.sh --token <TOKEN> --url https://github.com/<org> --name awrawr-pc --labels self-hosted,linux,x64`
2. Install Dagger CLI via mise: `mise use dagger@latest`
3. Write `.dagger/main.go` (or Python SDK) with `ci()` function: test Python, build Bun, build Rust, build Go — parallel
4. Add pitchfork daemon definition, `pitchfork daemon start build-runner`
5. Push a test commit, verify streaming logs in Actions UI
6. Document in repo README

## Research Ledger (Exa costs)

- Dagger programmable CI/CD 2026: $0.007
- Build systems (Nix/Devenv/Earthly) 2026: $0.007
- Self-hosted runner alternatives 2026: $0.007
- Buck2/Bazel 2026: $0.012
- devenv 2.2 deep: $0.007
- **Total: $0.040**
