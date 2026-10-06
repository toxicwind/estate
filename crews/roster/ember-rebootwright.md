---
crew: 'ember-rebootwright'
scope: 'Infra ports assessment + crew-b-f844 snapshot cleanup + staged yote kernel cutover (7.1.5-1 -> 7.2.6-1)'
owner: 'ember-rebootwright (Ember''s crew)'
status: 'DONE (2026-09-21) -- cutover EXECUTED 19:37:53 MDT via /tmp/kernel-cutover.sh (sha256 ad596f83); clean shutdown 19:38:14; NO boot until 21:39:02 MDT (~2h dark vs 2-4 min expected -- machine sat off/pre-kernel, boot trigger unverified: physical press / WoL / AC restore); now on 7.2.6-1-cachyos-bore (verified live `uname -r` 2026-09-21). Post-boot fallout fully repaired: (a) black-screen fix 2026-09-20 ~21:47 (bore had no nvidia driver -- installed linux-cachyos-bore-nvidia-open 7.2.6-1, mkinitcpio -p, sddm restarted, greeter on DP-1/DP-2; PER-KERNEL RULE in §1); (b) daemon-repair crew evicted 76 stale pitchfork registrations, all serve backends /health 200. Ports: cockpit 9090->25212 via systemd drop-in, curl -k 200 verified. crew-b-f844 moved to /home/toxic/.trash-20260920/crew-b-f844 (recoverable)'
order: 41
registered: '2026-09-21'
updated: '2026-09-29'
---

# ember-rebootwright

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.
