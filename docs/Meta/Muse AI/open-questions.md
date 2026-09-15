# Open questions

1. **What triggers a cell replacement?** Two observed in one day (2026-09-14 ~03:50 and 13:17 MDT). The client banner ("restarting for an update") is generic — it shows for any cell loss, not a diagnosed cause. Candidates: platform update rollout, OOM/memory eviction, host VM maintenance. Heavy fleet load (20 active agents, spawn bursts) preceded both deaths; self-inflicted OOM is not ruled out.
2. **What are the cell's resource quotas?** Observed 7.7G RAM / 7.5G disk, no swap. Are these quotas, and what does the platform do at the limit — kill processes, throttle, or replace the cell?
3. **Host VM vs cell lifecycle.** Launcher comments reference "a live VM" as the host. Does one VM serve many cells over time? What, if anything, survives on the host across cell replacements?
4. **Where does Postgres live?** External to the cell and persistent across replacements. Managed service? Same host? Unknown.
5. **What is Sentinel?** Partially answered 2026-09-14: it routes egress (`hatch-egress-proxy`, "Sentinel-routed") AND owns the approval store — Sentinel's approval records are explicitly outside the `muse.db` query surface (per the DB schema guide). Still unknown: where it runs, its full responsibilities.
6. **The channel system.** `JARVIS_CD_CHANNEL` is injected per VM and gates which skills/binaries are revealed inside the cell. What channels exist, and which one is this cell on?
7. **The update mechanism.** When the platform "updates", is it a new rootfs image plus cell replacement? That would explain the fresh-everything signature (new boot_id, empty wtmp/journal) we see each time.
