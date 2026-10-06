---
crew: 'yote-console-fix'
scope: 'yote console black-screen fix (post-kernel-switch): bore flavor had no nvidia driver -> sddm couldn''t render on RTX 3090 (black DP-1/DP-2) and `Conflicts=getty@tty1.service` killed the console fallback; installed `linux-cachyos-bore-nvidia-open 7.2.6-1`, `mkinitcpio -p linux-cachyos-bore`, modprobed nvidia_drm, restarted sddm -- greeter active; all three 7.2.6 flavors now covered'
owner: 'Ember'
status: 'DONE (2026-09-20) -- operational fix, no repo changes; PER-KERNEL RULE recorded in §1'
order: 54
registered: '2026-09-20'
updated: '2026-09-29'
---

# yote-console-fix

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
