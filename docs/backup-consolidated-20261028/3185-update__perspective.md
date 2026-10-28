## Perspective: the bug trap, the product question, and what this patch is not

Added 2026-09-16, after re-reading the full issue #3185 thread (11 comments via
GitHub API, 2026-04-23 → 2026-08-17) and the reporter's follow-ups. This section
does not change the code; it records the framing the patch is written against,
so the next person doesn't fall into the same trap.

### Two definitions of "fix" collided

The thread runs two different definitions of "fix" at once:

1. **Product definition** (the reporter's): stop the freeze on Pixel 10 without
   degrading every other device — "hamstring Pixel 10, not all devices."
   Workaround A (`canReuseCodec=false` on Pixel 10) was rejected by the reporter
   because it caused black frames; workaround B (force software decode) shipped
   but costs quality and battery. The desired behavior is that the device stops
   failing on codec-level switches — most other devices handle them fine.
2. **Correctness definition** (this patch's): the selector should never bundle
   mutually incompatible AVC profiles/levels into one adaptive selection in the
   first place. The Big Buck Bunny ladder proves the selector bug exists
   independent of any one device.

Gate A serves definition 2, globally. It is not a Pixel 10 workaround.

### The firmware defect is separate — and already fixed upstream

The Pixel 10 freeze is a firmware defect, not a selector defect: the Tensor G5
VPU (`google.hardware.media.c2@3.0-service`) fails `VPU_DecCompleteSeqInit`
(`FAILED TO DEC_PIC_HDR`, SEQERR 20480 = SPS/PPS reject) when the stream's
profile/level changes, surfacing as MediaCodec error `0xe`/`14`. Google's media
codec team identified the root cause and merged a firmware fix internally on
2026-08-17 (microkatz on #3185); it ships in a future Pixel update. No ExoPlayer
patch can fix firmware — Gate A reduces the *selector's* contribution (it stops
offering cross-profile switches), but on unpatched Pixel 10 firmware the VPU can
still fail on any reconfigure. That is Google's bug to ship, not ours to paper
over.

### The bug trap: four arguments, one thread

The discussion kept mixing four separate arguments without labeling them:

1. the firmware defect (VPU state machine),
2. the selector correctness bug (this patch),
3. the product workaround choice (which devices to hamstring, and how),
4. the philosophy layer — shipping a fix here is a negotiation with Google and
   the device vendors, not just a diff.

Arguing (4) as if it were (1), or "fixing" (2) while believing you've fixed
(1), is the trap. This patch fixes (2). It deliberately does not touch (1)
or (3).

### Proprietary, correctly attributed

`DefaultTrackSelector.java` is Apache 2.0 open source — it is not the
proprietary code in this story. The actual proprietary layers are the Pixel 10
VPU firmware/driver in `/vendor` and the reporter's production playback stack.
Aim the fix at the layer you can actually change; don't ask an open-source
selector to compensate for a closed firmware state machine beyond what
correctness already requires.

### Gate B: proposed, audited, NOT implemented

A device-aware follow-up ("Gate B": Pixel 10-only stricter gating, matching the
reporter's product preference) was specified in review notes — and the double
audit below caught the spec gating the **wrong devices**: one draft listed
`tokay` (Pixel 9, Tensor G4) and another listed `comet` (Pixel 9 Pro Fold),
neither of which is a Pixel 10. The verified Tensor G5 / Pixel 10 set is
`frankel` (Pixel 10), `blazer` (Pixel 10 Pro), `mustang` (Pixel 10 Pro XL),
`rango` (Pixel 10 Pro Fold), `stallion` (Pixel 10a). Gate B stays unimplemented
until the device list is confirmed and explicitly approved — and with the
firmware fix already merged internally, the product question belongs to the
exo-team proposal discussion, not to this correctness patch.
