# Estate

One of the estate's five pens (`pens/{estate,geode,barn,ranch,olympus}`).
Every pen has the same shape: `products/` for peer standalone checkouts,
`docs/` for pen-owned documentation, and a `bin/` entrypoint surface that
is symlinked into `~/.local/bin` and pinned by the estate-ops manifest.

## Products

| Product | Repo | Port | Role |
| --- | --- | --- | --- |
| estate-ops | [toxicwind/ops](https://github.com/toxicwind/ops) | — | The estate's ops place: pitchfork plumbing, bin manifest + bin-verify SSOT, shims, audit scripts |
| estate-brain | (dir inside pens) | — | forever-loop agent runtime (run-loop daemon) |
| estate-shell | [toxicwind/estate-shell](https://github.com/toxicwind/estate-shell) | — | shell environment + systemd unit dots (pitchfork.service lives here) |
| estate-dispersal | [sovereign-dispersal](https://github.com/toxicwind/sovereign-dispersal) | — | dispersal pipeline |
| estate-dispersal-monolith | [estate-dispersal-monolith](https://github.com/toxicwind/estate-dispersal-monolith) | — | dispersal monolith |
| estate-end4 | [sovereign-end4](https://github.com/toxicwind/sovereign-end4) | — | end4 desktop environment bits |
| estate-hatch-toolkit | [sovereign-hatch-toolkit](https://github.com/toxicwind/sovereign-hatch-toolkit) | — | hatch toolkit |
| estate-kappa-plugin | [estate-kappa-plugin](https://github.com/toxicwind/estate-kappa-plugin) | — | kappa plugin bridge |
| estate-monitor | [estate-monitor](https://github.com/toxicwind/estate-monitor) | — | monitoring |
| estate-recon | [estate-recon](https://github.com/toxicwind/estate-recon) | — | recon |
| estate-skills | [sovereign-skills](https://github.com/toxicwind/sovereign-skills) | — | skills |
| estate-skills-hub | [sovereign-skills-hub](https://github.com/toxicwind/sovereign-skills-hub) | — | skills hub |
| estate-whoa-breakthrough | [estate-whoa-breakthrough](https://github.com/toxicwind/estate-whoa-breakthrough) | — | whoa breakthrough |

## Control-plane payload (fat pen)

- `pitchfork.toml` — the daemon monolith (authoritative; shadows pitchfork.d)
- `config/` — per-pen config aggregate (tau runtime blob stays anchored at
  legacy `estate/config/tau` via `~/.tau` symlink)
- `stack/` — service launch scripts (`./stack/services/*.sh` from daemon `run=`)


## Layout
```text
estate/
  .gitignore    kitchen-sink `*` + whitelist (submoduleless doctrine)
  README.md     this file — role, member table, ports, languages
  LICENSE
  package.json
  mise.toml
  AGENTS.md
  bin/          entrypoint symlink surface -> ~/.local/bin
  products/     peer standalone checkouts (auto-ignored, never tracked)
  docs/         pen-owned documentation
```

## Tooling

- **bin surface**: entrypoints symlinked into `~/.local/bin`, pinned by the
-  estate-ops manifest and verified by `bin-verify.sh`. A broken link is
-  a FAIL, never a WARN.
-  **README**: generated from the pen's own product set by
-  `bin/readme-gen.ts`.

## Conventions

- Submoduleless: peer repos are shallow clones, never git submodules
- Ports SSOT: `config/ports.env` is the single source of truth for :25xxx ports
- Bun runtime: all TS/JS products run on Bun; Go and Rust are compiled binaries

## License

Estate internal — all rights reserved.
