# AGENTS.md — squawk-verification

## Role
You add Ed25519 signature verification to squawk's message ingest. You are the bouncer — every message gets checked at the door.

## Task
1. Modify squawk's ingest path to:
   - Extract `SQUAWK_SENDER` and `SQUAWK_SIGNATURE` from message frontmatter
   - Look up the sender's public key in `corral/personas/<name>/identity.pub`
   - Verify the signature against the message body
   - If valid: display as `name` (normal)
   - If invalid or missing: display as `~name` (unverified, self-asserted)
   - If sender has no registered key: display as `~name`, prompt to onboard
2. The verification must not drop messages — mark them, don't delete them.
3. Log all verification failures with timestamp, claimed sender, and reason.

## Constraints
- NEVER drop a message due to failed verification. Mark it `~name`.
- Verification must be fast (<10ms per message). Cache public keys in memory.
- If `identity.pub` is missing for a known persona, treat as "no key" (unverified), not as an error.
- The oracle (when moved to squawk) will use the same verification path.

## Verification
Test with: valid signature → `name`, tampered body → `~name`, unknown sender → `~name`, missing signature → `~name`.

## Output
Report: files modified, test results, performance measurements. Include the exact verification logic for review.
