# Phase 1 — Paper & docs findings: modularizing pitchfork.toml

Research worker: **Wren** (Ember's crew), 2026-09-30.
Target: /home/toxic/sovereign/pitchfork.toml on yote — 995 lines, 82 `[daemons.*]` sections, pitchfork 2.25.0.
Key local fact (from the file's own header comment, verified read-only): **pitchfork does NOT
hot-reload this file.** Editing a `[daemons.*]` section changes nothing until
`bin/pitchfork-restart sovereign/<name>` re-registers the daemon. Any modularization must
design its own reload semantics — the supervisor won't provide them for free.

## Findings

Numbered citations. Papers first (ranked by relevance), then verified upstream docs.

### Papers

**[1] Dolstra, E. & Löh, A. "NixOS: A Purely Functional Linux Distribution."**
*Proc. ICFP '08*, pp. 367–378. DOI `10.1145/1411204.1411255`.
The canonical "generate system config from typed modules" design. NixOS composes a whole
OS configuration from modules declaring *typed options* with *definitions*; conflicting
definitions merge through per-option merge functions gated by explicit priorities
(`mkDefault` < plain < `mkForce`). Generation is a pure function → the output config is
reproducible, diffable, and atomically switchable. Direct precedent for design B, and the
priority mechanism is the cleanest formal answer to "last-wins vs deep-merge": neither —
typed merge with declared precedence.

**[2] Dolstra, E. "The Purely Functional Software Deployment Model."**
PhD thesis, Utrecht University, 2006. https://edolstra.github.io/pubs/phd-thesis.pdf
Foundations behind [1]: components in isolated content-addressed stores; nothing mutated
in place; upgrades are atomic and rollback is trivial. Relevance: any *generated*
pitchfork config should be atomic (write whole file, never patch in place) — a
half-written supervisor config is the exact failure class this thesis eliminates.

**[3] Xu, T. et al. "Hey, You Have Given Me Too Many Knobs!: Understanding and Dealing
with Over-Designed Configuration in System Software."** *FSE '15*.
DOI `10.1145/2786805.2786852`.
Measured: only 6.1–16.7% of config parameters are set by most users; up to 54.1% are
rarely set by anyone. Their guidelines removed 51.9% of one system's parameters with
little user impact. Relevance: per-daemon manifests (B) and fragment layers (C) both
risk knob proliferation. The paper argues for *few, well-defaulted* knobs — a
modular design must not turn 82 daemons into 82 snowflake schemas.

**[4] Hicks, M. & Nettles, S. "Dynamic Software Updating."**
*ACM TOPLAS* 27(6):1049–1096, 2005. https://mhicks.me/papers/HicksNettles03.html
Design goals for live update: flexibility (any part upgradable), robustness, ease of use,
low overhead. Key mechanism: updates applied at *programmer-determined points* via
patches carrying both new code and the old→new state transition; patches are
*verifiable* (proof-carrying). Relevance to hot-reload: the granularity question is not
"reload everything or nothing" but "define safe update points and verify the
transition." pitchfork's per-daemon restart is the coarse analog; a modular design can do
better by diffing old vs new per-daemon and only transitioning changed daemons.

**[5] Armstrong, J. "Making Reliable Distributed Systems in the Presence of Software
Errors."** PhD thesis, KTH, 2003. https://erlang.org/download/armstrong_thesis_2003.pdf
Erlang/OTP: supervision trees + hot code loading (two module versions coexist; processes
migrate on explicit `code:purge`/message boundaries). Relevance: the oldest production
proof that *per-component* upgrade granularity works at scale — the supervisor tree
itself is never torn down to upgrade a leaf. Direct ancestor of the "reload definitions,
restart only changed daemons" model.

**[6] Shapiro, M. et al. "Conflict-free Replicated Data Types."**
INRIA RR-7687, 2011; *SSS 2011*. https://inria.hal.science/inria-00609399
Defines Strong Eventual Consistency (SEC): replicas converge without coordination iff
updates are associative, commutative, idempotent. Relevance: if pitchfork.d fragments are
*additive* (each file owns disjoint daemon-name keys), the composed config is a
grow-only map — a CRDT in all but name, and multi-writer edits (humans + agents)
converge by construction. The moment two files can set the *same* key, SEC is lost and
you need explicit precedence (back to [1]).

**[7] Mens, T. "A State-of-the-Art Survey on Software Merging."**
*IEEE TSE* 28(5):449–462, 2002. DOI `10.1109/TSE.2002.1000449`.
Canonical survey of two-way / three-way / structural / semantic merge. Core result:
three-way merge beats two-way *when a common ancestor exists*; without one, conflicts are
undecidable. Relevance: keep the parent config in git (it is: sovereign-projects) and a
module system can three-way merge fragment edits. Without ancestor tracking (e.g.
hand-edits to generated output), prefer designs where conflicts are *structurally
impossible* (additive fragments, [6]) over designs that need conflict resolution.

**[8] Kleppmann, M. et al. "Local-First Software: You Own Your Data, in spite of the
Cloud."** *Onward! 2019*, pp. 154–178. DOI `10.1145/3359591.3359737`.
CRDTs in practice (Automerge JSON): multi-writer convergence works, but conflicts must
be *surfaced in UI*, not silently resolved. Relevance: warns against silent
last-wins for anything humans debug at 2am — a `pitchfork config explain <daemon>`
(showing which fragment set each key) is the config analog of their conflict UI.

**[9] Semenov, G. & Aksenov, V. "Semantic Conflict Model for Collaborative Data
Structures."** 2026 (conference, Edinburgh). https://arxiv.org/html/2602.19231
Three-way merge over a replicated journal with *explicit* local conflict resolution;
formalizes LWW register; argues CRDTs' built-in resolution is "implicit and opaque."
Relevance: newest work in the set, and it reinforces [8] — if the design ever allows
same-key overrides across fragments, make the resolution explicit and inspectable,
never magic.

**[10] Xu, T. et al. "Do Not Blame Users for Misconfigurations."** *SOSP '13*,
pp. 244–259.
Misconfigurations cause a large share of production failures; systems should
*prevent* them (validation, safe defaults) rather than blame operators. Relevance:
whatever the module system, ship a validator (`pitchfork config check`) in the same
commit — the SOSP line says a modular config without validation just distributes the
misconfiguration surface.

### Verified upstream docs (ground truth for borrowing)

**[D1] systemd.unit(5) — drop-in semantics.**
https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html (verified 2026-09-30).
`foo.service.d/*.conf` parsed *after* the main unit file, in alphanumeric order;
`/etc/` > `/run/` > `/usr/lib/` precedence; dash-truncated prefix dirs
(`foo-bar-.service.d/`) for families; equally-named files deeper in the hierarchy win.
Settings generally override (some list directives are additive unless reset with an
empty assignment first — the one sharp edge). Verdict for borrowing: the most
battle-tested drop-in design in existence; the rule is "ordered files, later wins,
documented exceptions."

**[D2] `systemctl daemon-reload` semantics** (systemctl(1) man text, verified).
"Rerun all generators, reload all unit files, and recreate the entire dependency tree.
While the daemon is being reloaded, all sockets systemd listens on… will stay
accessible." It does **not** restart running services. Verdict: the reference
implementation of hot-reload granularity — *reload definitions globally, restart
nothing implicitly;* changed units get explicit follow-up action. This is exactly the
granularity a pitchfork.d watcher should implement.

**[D3] supervisord `[include]`** (supervisord.org/configuration.html, v4.3.0, verified).
Single key `files` = space-separated globs, resolved relative to the *including*
file; **recursive includes from included files are not supported**; processed only by
`supervisord`. Effectively concatenation — the ecosystem convention
(`/etc/supervisor/conf.d/*.conf`) is one file per program, i.e. additive fragments.
Verdict: the closest structural analog to design A, with the same limitation pitchfork
would face: include is load-time composition, not hot reload.

**[D4] Docker Compose file merging**
(https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/, verified).
Ordered `-f` files: scalars replaced by later files; multi-value options
(`ports`, `expose`, …) *concatenated*; `environment`/`labels`/`volumes`/`devices`
merged key-wise with local precedence; override fragments **need not be valid
standalone files**; all relative paths resolve against the *base* file (documented
footgun — the `include` top-level element exists precisely to fix it). Verdict: the
best-documented mixed merge policy (replace vs concat vs keyed-merge per field type);
the path-resolution footgun is a warning for design C (mise fragments in subdirs).

**[D5] CUE value lattice / unification** (https://cuelang.org/docs/concepts/logic/, verified).
All values (types included) sit in a lattice; merging = greatest lower bound → merge is
**unambiguous and order-independent**; conflicting concrete values are *errors*
(bottom), not silent wins; defaults via `*1 | int`. The docs explicitly contrast this
with "file-based approaches as used in HCL and Kustomize" and Jsonnet-style
inheritance, where "another concrete value that occurs elsewhere can override it" —
finding a value never guarantees the final answer. Verdict: the strongest formal
argument *against* silent last-wins layering (design C's failure mode) and *for*
conflicts-as-errors in generated configs (design B done right).

## Relevance-to-design

### Design A — pitchfork.d drop-ins merged at load
**Best-supported by the literature.** [D1] systemd, [D3] supervisord conf.d, and [D4]
compose all converge on the same pattern: ordered fragment files, deterministic
precedence, additive-by-default. The papers add two constraints that turn "folk
practice" into a safe design: (a) per [6] Shapiro, keep fragments **additive per
daemon-name key** — one file owns `[daemons.<name>]` wholly, never two files setting
the same key — so the merge is a conflict-free map union with no resolution logic at
all; (b) per [7] Mens, this sidesteps three-way merge entirely because conflicts are
structurally impossible. [D2] gives the reload model: a `pitchfork.d` watcher should
diff old vs new per-daemon and re-register *only changed daemons* (systemd's
"reload definitions, restart nothing implicitly"). [8]/[9] demand a
`pitchfork config explain` view so the effective config is always inspectable.
[D1]'s reset-first exception is the cautionary tale: if any directive type merges
differently, document it in exactly one place.

### Design B — generated config from per-daemon manifests
**Strongest formal precedent, highest implementation cost.** [1] NixOS is the
existence proof: typed options + merge functions + explicit priorities
(`mkDefault`/plain/`mkForce`) subsume the last-wins-vs-deep-merge debate, and [2]
Dolstra's thesis adds atomicity (generate whole file, swap atomically — never patch
the live config in place). [D5] CUE shows the endgame: order-independent unification
with conflicts as *errors*, which is strictly safer than any precedence chain. [3]
Xu/FSE'15 and [10] Xu/SOSP'13 jointly require: keep the manifest schema small (few
knobs, good defaults) and ship validation (`cue vet`-analog) in the same change —
otherwise generation just moves misconfigurations upstream. **Warning from local
history:** the pitchfork.toml header says a generator was *retired* 2026-09-14 because
it "would destroy live daemons" — a B prototype must prove atomic, non-destructive
regeneration (the [2] property) before anything else, or it repeats a known failure.

### Design C — mise.local.toml fragments composed upward
**Weakest literature support; the papers mostly warn against it.** [D4] compose is the
only positive template (ordered overlays, per-field merge policy), and even it
documents the relative-path footgun that upward composition from subdirectories
invites. [D5] CUE's design docs are an explicit critique of exactly this shape:
with layered file overrides, "finding a declaration for a concrete field value does
not guarantee a final answer" — debugging becomes "which layer won," multiplied by
every directory level. [3] predicts knob explosion as each layer adds its own
overrides. [6] SEC is unachievable here without a total precedence order, and [9]
says any such order must be explicit and inspectable, not emergent. If C is pursued
anyway, it needs [D1]-style deterministic ordering, [D2]-style diff-scoped reload, and
an `explain` view ([8]) as mandatory companions — at which point it has reinvented A
with worse debuggability.

---

*Sources: 10 papers ([1]–[10]) + 5 verified doc pages ([D1]–[D5]). alphaXiv searched;
no configuration-composition papers found there (checked 2026-09-30).*
