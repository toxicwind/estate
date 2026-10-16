# TODO.md — master workqueue (post-compact handoff)

> **Read this first after /compact.** Ordered by execution. Context block at the
> bottom has every path/decision needed. Updated 2026-10-16 ~23:20.

## Session log 2026-10-16 (late) — DONE, keep for reference

- [x] estate commits + pushes (consolidation, flicker→forge, architect sweep, gitleaks gate fixes)
- [x] ranch: 54+64 dirty submodules forward-committed; VansRouter/mcpproxy-go/flocksync/pi_agent_rust/drover snapped; runtime configs untracked (mesh_config had real keys)
- [x] gitleaks SSOT allowlists: Edge TTS public token, anthropic beta strings, sk-machine test fixtures, conformance template artifacts
- [x] pattern-forge: github_repos leg (repo finder), S2 secretsmith keychain, dblp retry
- [x] corral: toxicwind naming, bun install fix, library import proven (SuperRalph/AgentRegistry)
- [x] 2-second rule: run-fast documented MANDATORY in root+estate AGENTS.md; bash-2s-shim.sh live (aliases in agent shells, ~/.bashrc source)
- [x] 6 MCP forks as own repos: fleet-bus-mcp, hatch-mcp, huggingface-mcp-server, mcp-gateway (gateway.ts implemented), tmux-mcp (framing fix documented), websearch-mcp — all toxicwind/* with aesthetic READMEs
- [x] estate-shell: NEW SSOT repo (toxicwind/estate-shell) — dots, environment.d doctrine (105 vars emitted to systemd), TS deploy engine (dotbot replacement), env doctor (caught real AQ_DRM_DEVICES conflict), 16 cutting-edge deps verified on bun 1.4.3-canary
- [x] mcpproxy-go: gateway.ts fan-out implemented; flocksync unshallowed (was depth-1) from upstream OmniRoute
- [ ] ranch weave land --onto origin/main RUNNING in background (bgp_1470104bc001WoddEe0e2tYoVg)
- [ ] flocksync release/v3.8.52 push RUNNING in background (bgp_14700c49c001EU10hPq4CadZDp)


## 0. In-flight state (uncommitted — commit FIRST)

- [ ] **estate repo dirty (~20 files)**: omniroute takeover (models.yml, ports.env,
      pitchfork.toml, flocksync config.ts/dialog, agent/config.yml), AGENTS.md
      (root is outside git; estate mirror tracked), docker-inventory doc,
      deleted `stack/services/omniroute.sh`, grasp-hub gitlink bump,
      skills/pattern-forge/{bun.lock,package.json,src/hf.ts},
      skills/guide-project-creator/ (new). Commit message ready:
      "omniroute → flock takeover + docker lane policy + forge hf".
      Pre-existing drift NOT mine (leave): engines/herd/*, pi-skills, sigma,
      work/tau-extensions, plugins/agentpluginzoo, bash-style-guide,
      projects/OmniRoute gitlink.
- [ ] **estate/projects consolidation half-done**: 135 estate-only files already
      union-merged into ranch/, 33 whole dirs moved (VansRouter, oh-my-pi,
      tau-extensions, mcpproxy-go, loom, openfang, …), divergent variants archived
      at `estate/var/archive/projects-pre-consolidation-20261016/`.
      REMAINING: (a) OmniRoute gitlink → ranch (.gitmodules entry + 160000
      gitlink, url github.com/toxicwind/OmniRoute), (b) `git rm -r --cached
      projects/` in estate + delete leftovers on disk, (c) commit estate + ranch,
      push both.
- [ ] **secretsmith Bun drop-in unfinished**: full module at
      `ranch/secretsmith/bun/` (dropin.ts, index.ts, bin/secretsmith-bun.ts,
      test/dropin.test.ts, package.json) — NOT committed. Tests were 1 pass/9
      fail from a bad `import { Bun } from "bun"` (shadowed global) — sed-removed
      it, last run 4 pass/6 fail; re-diagnose (likely locateBin/D-Bus), fix, then
      commit+push the secretsmith repo (it also has 1 pre-existing unpushed
      commit `b5b4632` docs-staleness — push both).

## 1. Flicker → forge completion (biggest remaining refactor)

- Daemon keys already `[daemons.forge]` / `[daemons.forge-agent]` (line ~699/715).
- [ ] Compose list (pitchfork.toml line 33) still `"flicker","flicker-agent"` →
      rename to forge/forge-agent.
- [ ] Binaries: `estate/var/reconciliation/flicker/bin/{flicker,flicker-server,
      flicker-agent}` (41MB/69MB/21MB, real running processes :25148/:25240/:3000)
      → rename to forge/forge-server/forge-agent; update pitchfork `run=` lines.
- [ ] `FLICKER_ROOT=/home/toxic/flicker` env (pitchfork line 724) points at a
      MISSING dir — fix to real root; rename var FLICKER_ROOT→FORGE_ROOT.
- [ ] `ranch/flicker/` project dir (bin/flicker*, pitchfork.d/flicker.toml) —
      clean-delete or fold into ranch/forge (NOTE: ranch/forge already exists =
      NativeLink wrapper; do not merge codebases — decide name: forge-build?).
- [ ] Delete `ranch/shell/ii/dots/.config/systemd/user/flicker-server.service`
      (no-competing-systemd doctrine; currently disabled).
- [ ] grasp-hub `skills/03_systems_runtime/flicker` + `flat/flicker` symlink +
      estate/skills/flicker — merge content into a forge skill, clean delete.
- [ ] Verify: `ffs grep -i flicker --root /home/toxic/estate` → only
      var/archive + docs/history hits; daemons green.

## 2. Shell config cleanup (ble.sh / .env / nim-omnibus)

- [ ] **SECURITY**: `~/nim-omnibus.sh` (sourced by .bashrc:178) hardcodes
      NGC_API_KEY + NVCF_API_KEY (same nvapi- value) + BREV_API_KEY +
      BREV_ORG_ID in plaintext — NONE in vault yet. Add all 4 to `~/.secrets`,
      convert the script to vault-grep (copy the proven pattern from
      `.bashrc.local` GITHUB_TOKEN block). Canonical copy is
      `ranch/nim-omnibus/nim-omnibus.sh` (differs from $HOME copy — reconcile).
- [ ] Archive 15 shell backup files (.bashrc.bak*, .bashrc.env.bak*,
      .bashrc.pre-ssot, .bashrc.backup, .bashrc.local.bak*) →
      `~/archive/shell-backups-20261016/`.
- [ ] Pattern-borrow (in progress): 6 real ble.sh bashrcs fetched to
      `/tmp/kilo/bashrc-borrow/` (ARKye03/dotfiles, Narsell/dotfiles,
      rashil2000/dotfiles, jonpas/dotfiles, 6aru/i3-EllenJoe, gyro-uyt/dotfiles —
      21-140 lines each; 12 repos found, 6 fetched). Fetch 2-3 more, compare
      structure (ble.sh→starship order, guards, env handling), rebuild `~/.bashrc`
      proven-style. Current chain works: .profile→.bashrc.env→.bashrc→
      (line 128) .bashrc.local (ble.sh→starship→vault keys)→(line 178)
      nim-omnibus.sh.
- [ ] `~/.env` (9.7KB, NOT sourced by shells — app/compose env): cleaned of
      omniroute refs; document its role in AGENTS.md shell-chain section.

## 3. FreeInference upstream proof (.md doc pending)

- [ ] Proven local-side: no /etc/hosts intercept; freeinference.org → real
      Cloudflare IP 172.67.197.180; legit Google Trust Services TLS cert;
      `server: cloudflare` headers; 402 body = "no remaining credits" with valid
      37-char token; /v1/models 200 with 6 models (glm-5.3-flash, minimax-m3,
      qwen3.6-35b, diffusiongemma, deepseek-v4-flash, bge-m3).
- [ ] Do the dedi A/B: identical /v1/models + /v1/chat/completions + /v1/messages
      requests from 172.96.160.178 (sshpass root, key FREEINFERENCE_API_KEY) —
      compare status/model-remap/429 behavior. Same = upstream proven.
- [ ] Write `estate/findings/prior-audits/freeinference-upstream-proof-20261016.md`
      incl. known flaws: free tier concurrency=1 (429 the loser), /v1/messages
      silently remaps model (glm req → qwen3.6-35b served), 402 credit wall on
      HF router (separate provider). Also: NO orphaned local models — bge-m3/
      glm-5.3-flash are remote; local engine is pure-Bun localZeroShot.

## 4. Agent READMEs modernization (paper-grounded, started)

- Grounding: "Agent READMEs: An Empirical Study of Context Files for Agentic
  Coding" (ACM TOSEM 2026, doi 10.1145/3840295 — 2,303 files/1,925 repos:
  context files are "complex, difficult-to-read artifacts that evolve like
  configuration code") + "The Developer as Curator" (doi 10.1145/3840586.3843212
  — three failure modes: wrong/missing/stale context).
- [ ] Root `/home/toxic/AGENTS.md` (rewritten thin+curated ✓) + estate mirror
      (rewritten as nested domain file ✓) — final read-through for the
      "superaware ffs" table and lane policy, then sync mirror byte-for-byte
      where sections are shared.
- [ ] Nested AGENTS.md convention: root = universal contract; estate = domain;
      ranch/<component>/AGENTS.md = component. Document in both files (root
      already has the scope-split table).

## 5. Smaller queued items

- [ ] omniroute-gateway row in `findings/prior-audits/docker-inventory-20261016.md`
      → mark RETIRED (merged into flock).
- [ ] estate/skills/flicker + grasp-hub flicker skill → fold/rename (item 1).
- [ ] `ranch/projects/estate-core` oddity → consolidate (move to ranch/<name> or
      estate/projects — pick the non-weird one).
- [ ] `/home/toxic/projects/effusion-labs` (home-level, Lane B) → consolidate
      under ranch/websites/effusionlabs or keep as the compose runtime dir with a
      documented pointer (running container references its compose path).
- [ ] docker-inventory: hindsight container owner/origin still unknown.
- [ ] omniroute-gateway container: Lane-A borderline → being retired via flock
      takeover (see §0); migrate any unique omniroute provider config before
      final `docker rm` if the 402-free path ever needs its upstreams.

## Context (paths/decisions — stable)

- grasp-hub = `/home/toxic/estate/grasp-hub` (GitHub `toxicwind/grasp-hub`, was
  estate-skills-hub). Router: `node bin/grasp-hub.js route "<query>"`. Registry
  submodule: tinh2/skills-hub-registry (553 skills). UI fork: toxicwind/skills-hub.
- forge hf = `estate/skills/pattern-forge/src/{hf,hf-lib}.ts`; CLI
  `forge hf search|classify|embed|completions|find-classifier|tree|categorize`.
  3 engines: embed (freeinference bge-m3, cosine) / freeinference (glm-5.3-flash
  completions) / local (pure-Bun idf+ngram, margin-gated ABSTAIN). 40+ tests.
- freeinference: base `https://freeinference.org/v1`, key `FREEINFERENCE_API_KEY`
  (~/.secrets). HF router (router.huggingface.co) = separate, 402 credit-gated.
- ffs: refresh stale index with `ffs index --root <dir>` (a stale index caused
  missed files once). Full guide: `ffs guide` (288 lines).
- flock = first-class native router: pitchfork `estate/flock`, :25193,
  `~/.flock/flock` binary; canonical router per models.yml is cuttinggate
  :25200 (flock :25193 marked RETIRED there but daemon still serves).
- ranch/mesh/flocksync: ANOTHER WORKER has staged WIP (circuitBreaker/
  upstreamGuard, release/v3.8.52) — do not touch that repo.
- rustdesk: fixed 2026-10-16. Native pitchfork hbbs/hbbr on 25220-25224, key at
  `ranch/rustdesk-server/id_ed25519.pub`; docker containers + stale REDIRECT
  NAT rules removed (they caused remote RST).
- secretsmith: Python/libsecret CLI at `ranch/secretsmith` (submodule,
  github toxicwind/secretsmith). Bun drop-in being built at `bun/` in-repo.
- Docker lane policy (in both AGENTS.md): Lane A estate services = native
  pitchfork (no docker); Lane B ops/websites = compose in owning repo, ports in
  `config/ports.env`, loopback/tailnet bind. One supervisor per service.
