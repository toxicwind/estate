# Oracle Market End-to-End Settlement Proof — 2026-10-03

**Lane:** oracle-settle · **Agent:** Slate (Ember's crew)
**Date:** 2026-10-03 19:15 MDT (America/Denver)
**Claim:** a real intake filed through the oracle market was triaged, bid on,
executed, verified, and settled — the complete chain is recorded on the
tamper-evident ledger.

## The task

Deterministic, independently verifiable: compute `(1791069188 * 7919) mod 104729`
and report the single integer. Expected value (computed independently on the
cell before filing): **48213**.

- **Intake file:** `0272-slate-intake-1791076510.md` (from slate)
- **Intake ID / Task ID:** `task-1791076510806`
- **Tags:** `probe` · **Class:** standard · **Exec mode:** super-ralph

## The ledger chain

Source: `/home/toxic/estate/ranch/squawk/oracle/ledger/ledger.jsonl`
(all timestamps 2026-10-03 MDT)

| ts | event | detail |
|---|---|---|
| 19:15:10 | `intake-decision` | from slate → route TASK, "biddable work" |
| 19:15:10 | `task_open` | `task-1791076510806`, deadline 19:15:25 |
| 19:15:11 | `bid_accepted` | bidder-forge, amount 0.93, nonce d86e1c5aedeff517 |
| 19:15:11 | `bid_accepted` | bidder-scout, amount 0.94, nonce b269432aed241fea |
| 19:15:25 | `assigned` | winner **bidder-scout**, bond 10.0 locked, price_paid 0.93 (second-price) |
| 19:15:53 | `stake_released` | bond released, **reward 5.0** to bidder-scout |
| 19:15:53 | `settled` | **verified: true, success: true**, duration 25.6s, reason null |

Raw `settled` entry:

```json
{"task_id": "task-1791076510806", "winner": "bidder-scout",
 "verified": true, "success": true, "duration_ms": 25604.6,
 "price_paid": 0.93, "reason": null, "event": "settled",
 "ts": 1791076553.5311005}
```

## Verification

The winner's super-ralph run (exit 0, 24s) reported **48213** with a fully-MET
4-criterion ACCEPTANCE-REPORT. The oracle's verifier parsed the signed output
itself (`_parse_acceptance_report`): found=True, all_met=True, 4/4 items MET.
48213 == independently computed expected value → exact match. Total
intake→settle wall time: **43 seconds**.

## Repairs this proof required

The market was non-functional before this proof; three stacked defects were
found and fixed on the way (each verified live):

1. **Stake deadlock** — repeated no-result slashes had drained both bidders to
   stake 5.0 < BOND 10.0, so every assignment failed `stake-lock-failed`
   forever. Admin re-grant to 25.0 each, recorded as an `admin-grant` ledger
   event (precedent: the earlier `admin-release`).
2. **Super-ralph EACCES** — the 18:29 sweep folded `ranch/corral/src/cli/index.ts`
   (super-ralph's entry point) without the exec bit; bidders failed with
   `PermissionError`. Fixed via `git update-index --chmod=+x`, committed to
   ranch main as `0012ffc`, pushed, remote ref verified.
3. **Mixed-newline acceptance rejection** — super-ralph emits a real newline
   after its banner then literal `\n` escapes for the body; both
   `_canon_ralph_text` (bidder.py) and `_parse_acceptance_report`
   (oracle_loop.py) only normalized escapes when *zero* real newlines existed,
   so a correct result (48213, report present) failed as
   `acceptance-report-missing`. Both now normalize unconditionally.
   Verified by unit test against the exact rejected output
   (found=True, all_met=True, 4/4 MET). Folded to ranch main (`ad1b20c`,
   remote-verified); oracle-market + both bidders restarted via pitchfork.

## Open risks (not mine to fix in this lane)

- **Ticket-path execution is still broken:** work-shaped tasks send super-ralph
  into a ticket-scheduler loop where the `review-fix` node returns plain text
  against a Smithers `z.object` output schema → retry spiral → no-result
  slash (27 slashes vs 2 clean settles in ledger history). Only fast-path
  (pure-text, no-side-effect) tasks settle today.
- **Slash economics re-deadlock:** each no-result slash burns 10.0 stake; at
  25.0 the bidders survive two slashes before assignments halt again. The
  mechanism has no faucet — worth a design pass.

## Provenance

- Proof doc: `corral/docs/oracle-settlement-proof-2026-10-03.md` (this file),
  in toxicwind/estate.
- Fix commits: ranch main `0012ffc` (exec bit), `ad1b20c` (newline
  canonicalization, via sweep fold).
- Daemons at proof time: oracle_loop.py, bidder.py (forge + scout),
  market_watchdog.py, oracle_chat.py — all live on yote.
