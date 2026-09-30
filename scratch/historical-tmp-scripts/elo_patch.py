#!/usr/bin/env python3
"""Corrective patch for durable Elo persistence (elo-persist, 2026-09-21).

Fixes vs the first implementation:
1. Startup missing-row path no longer persists bench priors (map-only seeding).
   Only live outcome changes via setElo() create elo_state rows.
2. New persistedEloProviders set: explicit tracking of durably persisted
   providers (startup restores + live setElo writes). Hot-reload skips these
   unconditionally -- numeric equality with the prior is NOT protection.
3. Hot-reload re-seed of an untouched provider writes the refreshed prior to
   the DB but does NOT mark it persisted (markPersisted=False), so a later
   priors refresh can still update the baseline.
4. Constructor fails open: a corrupt/unopenable DB falls back to :memory: so
   routing stays alive on priors instead of crashing the daemon.
5. Comments corrected (no more claims that fallback priors are persisted).
"""
import sys

PATH = "/home/toxic/.worktrees/elo-persist/tools/sovereign-router/sovereign-router-ts/router_matrix.ts"

with open(PATH) as f:
    src = f.read()

edits = []

# --- Edit 1: add persistedEloProviders field ---------------------------------
old1 = """  priorsMtime = 0;
  priorsSource = "";
"""
new1 = """  priorsMtime = 0;
  priorsSource = "";
  /**
   * Providers with a durably persisted Elo row: restored at startup or
   * written by a live update through setElo(). Hot-reload NEVER re-seeds
   * these -- even when the persisted value numerically equals the bench
   * prior. Numeric equality is not proof a provider is untouched.
   */
  persistedEloProviders = new Set<string>();
"""
edits.append((old1, new1))

# --- Edit 2: constructor fails open on corrupt DB -----------------------------
old2 = """    // HealthDB first: Elo restore reads persisted live-learned values from
    // it; bench priors only fill providers with no stored row.
    this.health = new HealthDB(dbPath);
"""
new2 = """    // HealthDB first: Elo restore reads persisted live-learned values from
    // it; bench priors only fill providers with no stored row.
    // Fail open: a corrupt/unopenable DB must never take the router down --
    // fall back to an in-memory DB and keep routing on priors.
    try {
      this.health = new HealthDB(dbPath);
    } catch (e) {
      console.error(
        `[sovereign-router] HealthDB unavailable at ${dbPath}, ` +
          `Elo persistence disabled (routing on priors):`,
        e,
      );
      this.health = new HealthDB(":memory:");
    }
"""
edits.append((old2, new2))

# --- Edit 3: setElo gains markPersisted --------------------------------------
old3 = """  /**
   * setElo — the ONLY writer of provider Elo. Updates the in-memory map and
   * writes through to the HealthDB (elo_state table) so the value survives
   * a daemon restart. Best-effort: a DB failure must never break routing
   * (same contract as the Governor's snapshot persistence).
   */
  private setElo(prov: string, value: number): void {
    this.elo.set(prov, value);
    try {
      this.health.saveElo(prov, value);
    } catch {
      /* persistence is best-effort; routing semantics are untouched */
    }
  }
"""
new3 = """  /**
   * setElo — the ONLY writer of provider Elo. Updates the in-memory map and
   * writes through to the HealthDB (elo_state table) so the value survives
   * a daemon restart. Best-effort: a DB failure must never break routing
   * (same contract as the Governor's snapshot persistence).
   *
   * markPersisted=true (default): the provider joins persistedEloProviders.
   * Use for live-learned values and startup restores. Hot-reload re-seeds a
   * bench prior with markPersisted=false: the refreshed baseline is written,
   * but a later priors refresh may still update it -- it is a baseline, not
   * learned state.
   */
  private setElo(prov: string, value: number, markPersisted = true): void {
    this.elo.set(prov, value);
    if (markPersisted) this.persistedEloProviders.add(prov);
    try {
      this.health.saveElo(prov, value);
    } catch {
      /* persistence is best-effort; routing semantics are untouched */
    }
  }
"""
edits.append((old3, new3))

# --- Edit 4: applyBenchPriors docstring ---------------------------------------
old4 = """  /**
   * applyBenchPriors -- seed Elo from bench-priors.json.
   *
   * Startup (force=true): providers with a persisted Elo row in the
   * HealthDB get their live-learned value back — priors never clobber a
   * restore. Providers with no stored row fall back to the bench prior
   * (1000 when unbenched or the file is missing), which is then persisted.
   * Hot-reload: only providers whose Elo is still exactly at the last
   * applied prior are re-seeded -- providers with live traffic history
   * (including restored values) keep their learned Elo. Live outcomes keep
   * updating Elo either way.
   */
"""
new4 = """  /**
   * applyBenchPriors -- seed Elo from bench-priors.json.
   *
   * Startup (force=true): providers with a persisted Elo row in the
   * HealthDB get their live-learned value back and join
   * persistedEloProviders -- priors never clobber a restore, even on exact
   * numeric equality with the prior. Providers with no stored row fall back
   * to the bench prior (1000 when unbenched or the file is missing) IN
   * MEMORY ONLY: initial bench seeding is a fallback, not learned state,
   * and is never persisted. Only live outcome changes (via setElo) create
   * elo_state rows.
   * Hot-reload: re-seeds only providers that are neither durably persisted
   * nor touched by live traffic. persistedEloProviders is the authority, so
   * a restored value that happens to equal the old prior stays protected.
   * Live outcomes keep updating Elo either way.
   */
"""
edits.append((old4, new4))

# --- Edit 5: startup branch — map-only seeding, mark restores persisted -------
old5 = """        if (typeof prev === "number") {
          // Restored live-learned Elo: map-only (already in the DB).
          // priorElo records the *prior* baseline so hot-reload treats a
          // restored value as live-learned and never re-seeds it.
          this.elo.set(p, prev);
          this.priorElo.set(p, prior);
          restored.push(p);
        } else {
          this.setElo(p, prior);
          this.priorElo.set(p, prior);
          reseeded.push(p);
        }
"""
new5 = """        if (typeof prev === "number") {
          // Restored live-learned Elo: map-only (already in the DB), and
          // marked persisted so hot-reload never re-seeds it -- even when
          // the stored value numerically equals the bench prior.
          this.elo.set(p, prev);
          this.priorElo.set(p, prior);
          this.persistedEloProviders.add(p);
          restored.push(p);
        } else {
          // Missing row: bench prior fills the in-memory map ONLY. Never
          // persisted -- fallback priors are not learned state.
          this.elo.set(p, prior);
          this.priorElo.set(p, prior);
          reseeded.push(p);
        }
"""
edits.append((old5, new5))

# --- Edit 6: hot-reload branch — skip persisted, reseed baseline unmarked -----
old6 = """      } else {
        const cur = this.elo.get(p) ?? 1000;
        const last = this.priorElo.get(p) ?? 1000;
        if (cur === last) {
          this.setElo(p, prior);
          this.priorElo.set(p, prior);
          reseeded.push(p);
        }
      }
"""
new6 = """      } else {
        // Durably persisted providers are never re-seeded, regardless of
        // numeric equality with the prior.
        if (this.persistedEloProviders.has(p)) continue;
        const cur = this.elo.get(p) ?? 1000;
        const last = this.priorElo.get(p) ?? 1000;
        if (cur === last) {
          // Untouched by live traffic: refresh the baseline. Written to the
          // DB but NOT marked persisted -- a later priors refresh may update
          // it again; only learned values are protected.
          this.setElo(p, prior, false);
          this.priorElo.set(p, prior);
          reseeded.push(p);
        }
      }
"""
edits.append((old6, new6))

for i, (old, new) in enumerate(edits, 1):
    n = src.count(old)
    if n != 1:
        print(f"EDIT {i}: anchor found {n}x (expected 1) -- ABORTING")
        sys.exit(1)
    src = src.replace(old, new)
    print(f"EDIT {i}: applied")

with open(PATH, "w") as f:
    f.write(src)
print("PATCH OK")
