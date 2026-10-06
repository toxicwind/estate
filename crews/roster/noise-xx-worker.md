---
crew: 'noise-xx-worker'
scope: 'Noise_XX_25519_AESGCM_SHA256 lane: re-verify implementation, live handshake probe'
owner: 'ember'
status: 'DONE (2026-10-03) — live probe PASS, probe fix 7f06816 (supersedes 8964305)'
order: 1000000006
registered: '2026-10-02'
updated: '2026-10-03'
---

# noise-xx-worker

Per-crew ownership record. Edit the frontmatter above; the §2 table in
`docs/fleet-knowledgebase.md` is generated from these files — do not edit it by hand.
After changing this file, run `bun projects/ops/bin/kb-rollup.ts`.

## 2026-10-03 completion record

Live Noise_XX_25519_AESGCM_SHA256 handshake probe: PASS (exit 0, transcript
`transcripts/noise_xx_probe_*.log`). Full msg1 (42B) / msg2 (105B) / msg3 (68B)
handshake on both sides, notary endorsement parse + expiry + malformed-token
rejection, encrypted transport round-trip both directions (payload integrity
verified), wrong-AD decryption rejected, frame_pack/unpack round-trip, plus
fresh-session interop sanity: two independent sessions complete with transport
round-trips and differing session keys. `scripts/verify_all.py` also green
(6/6 suites).

Defect found and fixed in the owning repo: the committed probe (8964305)
TypeError'd on its final step — `NoiseHandshakeState(mode="standard")` but the
class has no `mode` parameter (the implementation is the muse.ai custom variant:
msg3 carries a second ephemeral e2, so there is no standard-mode switch). Step 6
rewritten as the honest fresh-session interop sanity above; fix commit
7f06816 on toxicwind/sovereign-hatch-toolkit main, remote ref verified.

Finding (design call, not fixed): `NotaryEndorsement` is parse-only — no Ed25519
signature verification exists; needs a provisioned notary public key + trust
model before anyone invents a scheme.

Honest verdict on the prior RUNNING claim (2026-10-02): it was not true as
stated — zero observable artifacts existed (no patch commit, no probe receipt).
It is true now.
