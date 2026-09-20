# Prompt audit v1 — oracle-v1 vs realistic token-bucket brief

## Ground truth (measured, hidden tests)
- tb-c1: PASS
- tb-c2: FAIL
- tb-c3: FAIL

## Judge verdict
- winner: tb-c1 (expected tb-c1) -> CORRECT
- ranking: ['tb-c1', 'tb-c3', 'tb-c2']
- confidence: 0.95
- judge_model: kimi-k3-nim
- swap_agreement: True
- rationale: C1 satisfies every hard constraint: uses time.monotonic() [C1 L18], threading.Lock guards all state mutations [C1 L15,27-32], bucket starts full [C1 L13], validates capacity/refill_rate>0 [C1 L9-10] and n>0 [C1 L25-26,35-36]. wait_time returns math.inf for n>capacity [C1 L37-38] and correct delay otherwise [C1 L42-43]. C2 violates two hard constraints: uses time.time() [C2 L13,16] not monotonic, and has no synchronization — C1's rebuttal correctly identifies the over-granting race [R2.2]. C3 concedes its wait_time stub violates the spec [R2.3]. C1 is the only complete, correct implementation.

- rationale citations found: 10 -> ['[C1 L18]', '[C1 L15,27-32]', '[C1 L13]', '[C1 L9-10]', '[C1 L25-26,35-36]', '[C1 L37-38]', '[C1 L42-43]', '[C2 L13,16]']

## Failure modes for oracle-v2
- none found in this audit
