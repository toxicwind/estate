# ArXiv Emergence Survey — Synthesis (Sovereign Registry)

**DSU Mechanism**: The hotfix registry (`hotfix_registry.ts`) implements Dynamic Software Update via `fs.watch()` + `.unref()` on the persistent `patches/` directory (`startWatcher`, line 182-210). `loadPatch()` dynamically imports updated `.ts` modules into memory; `persistPatch()` writes them permanently. This is the DSU pattern: live reload without daemon restart, with rollback via `.disabled` rename.

**Recursive Scheduling**: Pitchfork (`pitchfork.ts` generator) defines daemon lifecycle (`[daemons.*]`) and group orchestration (`[groups.core]`, `[groups.agents]`). The registry resolves service definitions (`ALL_SERVICES`) through `hotfixRegistry.resolve<ServiceDef>()`, creating a recursive scheduling layer: core services (herd, hindsight) feed health to agent runtimes (tau) through the same resolution mechanism.

**Sovereign Registry Synthesis**: The three arXiv streams converge in `patches/experimental_fusion.ts`: persistent file store (`persistPatch`), health-gated activation (`hindsight` port 25117 + `herd` daemon), and registry resolution (`resolve<T>`) without monkey-patching. The new hotfix (`TARGET = registry.emergent_sync`, `VERSION = 3.0.0`) binds these into one deliverable patch.
