#!/usr/bin/env python3
"""Hardcore-demote Docker in herd: README restructure + warning callouts + build fix."""
import sys

REPO = '/home/toxic/sovereign/herd'

# ---------- 1. README.md ----------
p = REPO + '/README.md'
s = open(p).read()

badge = '[![Unified Docker](https://github.com/toxicwind/herd/actions/workflows/unified-docker.yml/badge.svg)](https://github.com/toxicwind/herd/actions/workflows/unified-docker.yml)'
assert s.count(badge) == 1, 'badge anchor not unique'
s = s.replace(badge + '\n\n', '', 1)  # demote: badge moves down to the Docker section

old_intro = """herd is a fork of [mostlygeek/llama-swap](https://github.com/mostlygeek/llama-swap) (upstream), extended with
herd-specific infrastructure: our own unified Docker images, AST Matrix V2 smart routing, an agentic lens
suite, and hardening fixes for real-world deployments. The fork keeps upstream's core (swap models in and
out of VRAM on demand, OpenAI-compatible endpoints) and layers herd's production tooling on top."""
new_intro = """herd is a fork of [mostlygeek/llama-swap](https://github.com/mostlygeek/llama-swap) (upstream), extended with
herd-specific infrastructure: AST Matrix V2 smart routing, an agentic lens suite, and hardening fixes for
real-world deployments. The fork keeps upstream's core (swap models in and out of VRAM on demand,
OpenAI-compatible endpoints) and layers herd's production tooling on top.

**Runs native — no container required.** The machine is the platform: we operate herd under
mise + pitchfork, and plain `go build` works anywhere. Docker images exist only as a fallback
for folks who can't or won't run the native stack — see
[\U0001f433 Docker (fallback \u2014 not recommended)](#-docker-fallback--not-recommended)."""
assert s.count(old_intro) == 1, 'intro anchor not unique'
s = s.replace(old_intro, new_intro, 1)

old_row = '| Docker images | Own unified images: `ghcr.io/toxicwind/herd:unified-<backend>` (see below) |'
new_row = '| Docker images | Fallback only (not recommended): `ghcr.io/toxicwind/herd:unified-<backend>` \u2014 see below |'
assert s.count(old_row) == 1, 'table row anchor not unique'
s = s.replace(old_row, new_row, 1)

# Cut the old Docker section; it gets re-appended at the bottom, demoted.
start = s.index('## Unified Docker images')
end = s.index('## Agentic lens suite')
s = s[:start] + s[end:]

new_docker = '''## \U0001f433 Docker (fallback \u2014 not recommended)

''' + badge + '''

> \u26a0\ufe0f **The sovereign take on Docker** \U0001f433\U0001f6ab
>
> Docker works. It is also wrong for this stack, and we would rather tell you why than
> pretend otherwise:
>
> - **It fights your GPU.** Every container needs `--gpus`, `--runtime=nvidia`, device flags \u2014
>   ceremony the native binary skips entirely. The GPU is *right there*. Talk to it directly.
> - **It turns 100GB of weights into a mount puzzle.** Your models live on disk. Docker makes you
>   re-expose them through volume mounts and then acts surprised when paths break.
> - **It is a second platform under your platform.** We run on mise + pitchfork: the machine is the
>   platform. Docker inserts a shadow init system, an image registry, and a build pipeline for zero
>   local benefit.
> - **It is slower to iterate.** Rebuild the image, push, pull, restart \u2014 versus `go build` and run.
>
> So why does it exist here at all? As an **export format**: for people who cannot or will not run
> the native stack, and as CI's clean-room proof that herd assembles from nothing. If the machine is
> yours, go native. You will be happier.

herd publishes its own images (not upstream's):

```
ghcr.io/toxicwind/herd:unified-<backend>
```

Built by `docker/unified/build-image.sh`, published by `.github/workflows/unified-docker.yml`.

> **Rootless build note (2026-09-14):** the rootless build stage must use plain `docker build`
> (docker driver), **not** the buildx container driver \u2014 otherwise
> `FROM ghcr.io/toxicwind/herd:unified-<backend>` fails to resolve the local tag. Nightly unified
> builds were failing for a week before this was fixed.

'''
anchor = '## Remotes'
assert s.count(anchor) == 1, 'remotes anchor not unique'
s = s.replace(anchor, new_docker + anchor, 1)
open(p, 'w').write(s)
print('README.md: demoted OK')

# ---------- 2. docker/unified/README.md ----------
p = REPO + '/docker/unified/README.md'
s = open(p).read()
callout = '''# Unified Docker Container

> \u26a0\ufe0f **Heads up from the herd maintainers** \U0001f433\U0001f6ab \u2014 this Docker packaging is a
> *fallback*, not the way. herd runs native under mise + pitchfork (or plain `go build`); containers
> fight GPU passthrough, complicate 100GB+ model mounts, and add build/push/pull ceremony for zero
> local benefit. Only reach for this if you cannot run the native stack. The full sermon lives in the
> [\U0001f433 Docker (fallback \u2014 not recommended)](../../README.md#-docker-fallback--not-recommended) section.
'''
assert s.startswith('# Unified Docker Container\n'), 'unified README head changed'
s = s.replace('# Unified Docker Container\n', callout, 1)
open(p, 'w').write(s)
print('docker/unified/README.md: callout OK')

# ---------- 3. mesh/gateway/bench/README.md (light note; compose is deliberate here) ----------
p = REPO + '/mesh/gateway/bench/README.md'
s = open(p).read()
old_para = """`docker-compose.yml` boots mcpproxy over the frozen reference-server config so
the corpus and live tool list are reproducible across machines. The live
accuracy/latency/full-schema/response-cost scorers attach to it via `-live`"""
new_para = old_para + """

> \U0001f433 *Note:* docker-compose is used here deliberately as a frozen, reproducible benchmark
> substrate \u2014 one of the few places a container earns its keep. For actually *running* herd,
> go native; see the [\U0001f433 Docker (fallback \u2014 not recommended)](../../../README.md#-docker-fallback--not-recommended) note."""
assert s.count(old_para) == 1, 'bench README anchor not unique'
s = s.replace(old_para, new_para, 1)
open(p, 'w').write(s)
print('mesh/gateway/bench/README.md: note OK')

# ---------- 4. docker/build-container.sh: floating-tag fallback ----------
p = REPO + '/docker/build-container.sh'
s = open(p).read()
anchor_sh = """if [[ -z "$LCPP_TAG" ]]; then
    log_info "Abort: Could not find llama-server container for arch: $ARCH"
    exit 1
else
    log_info "LCPP_TAG: $LCPP_TAG"
fi
"""
assert s.count(anchor_sh) == 1, 'build-container.sh anchor not unique'
fallback = anchor_sh + """
# Upstream prunes old build-numbered tags (ghcr.io/ggml-org/llama.cpp:server-*-bNNNN
# come and go); if the resolved tag no longer resolves, fall back to the floating
# tag for this backend instead of failing the build.
FLOAT_TAG="server-${ARCH}"
if [[ "$ARCH" == "cpu" ]]; then
    FLOAT_TAG="server"
fi
if ! docker manifest inspect "${BASE_IMAGE}:${BASE_TAG}" >/dev/null 2>&1; then
    log_info "Upstream tag ${BASE_TAG} does not resolve; falling back to floating tag ${FLOAT_TAG}"
    BASE_TAG="${FLOAT_TAG}"
fi
"""
s = s.replace(anchor_sh, fallback, 1)
open(p, 'w').write(s)
print('docker/build-container.sh: fallback OK')

print('ALL TRANSFORMS APPLIED')
