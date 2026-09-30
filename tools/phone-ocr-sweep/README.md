# phone-ocr-sweep

OCR sweep over adb-pulled phone screenshots (corpus at `/home/toxic/ocr-sweep/shots/`,
outputs in `/home/toxic/ocr-sweep/txt/`). Idempotent: `ocr-one.sh` skips files
that already have a `.txt` output; each tesseract run is wrapped in `timeout 20`.

Provenance: built ad-hoc 2026-09-30 for the GTG/phone screenshot sweep; copied
here as the durable record.

**Guard history:** `run-ocr.sh` refuses to start while another instance holds
`/home/toxic/ocr-sweep/run-ocr.lock` (`flock -n`), and is capped at `-P4`.
Two swarm-watchdog eject events within 40 min forced this: yote load
84.7/105.4/82.0 at 04:59 MDT (an `xargs -P16` variant on the same corpus),
then 49.6 at 05:39 MDT (two `-P4` drivers stacked on the same corpus —
watchdog EJECTED, shed one duplicate, the other finished the tail).
