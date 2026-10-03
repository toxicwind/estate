---
crew: 'end4-corrective'
scope: 'sovereign-end4 system-tuning corrective commit: true zero-byte udev mask, corrected Btrfs attribution (911 exclusive bytes never measured), rewritten apply-system-tuning.sh (STAGING_ROOT isolated mode, install -m 644, service reconciliation), installer staging test (18/18 on yote), btrfs-status.sh health+guard tool, audit.py v3 (vmstat/buddyinfo/Btrfs/thermals)'
owner: 'Ember'
status: 'DONE (2026-09-21) -- commit fedb26a0da (on top of toxic''s 9e904729): 9 paths under system-tuning/, 3 executables 100755; mask blob verified 0 bytes; sysctl blob sha256 matches live /etc/sysctl.d/99-zswap-vm.conf; installer test 18/18 pass on yote; audit v3 smoke OK (unallocated_bytes=6443552768, 27 vmstat, 6 thermals); btrfs-status live report exit 0 via passwordless sudo (snapperd wedge timeout-guarded)'
order: 74
registered: '2026-09-21'
updated: '2026-09-29'
---

# end4-corrective

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
