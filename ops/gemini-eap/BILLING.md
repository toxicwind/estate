# Gemini EAP Tool-Retrieval — billing wall (the ONLY remaining step)

Everything code-side for the Gemini EAP tool-retrieval lane is LANDED and live;
inference is blocked by one item: the Google **AI Studio prepay wallet is empty**.

## Proven end-to-end (all verified live 2026-10-21)

- Keys authenticate: `GET https://generativelanguage.googleapis.com/v1beta/models` with
  another valid `GEMINI_EAP_KEY_N` + `x-goog-user-project:654595778272` returns 200.
  The keypool marks `gemini-eap-interactions` keys `healthy`.
- The keypool routes: a tool-retrieval request through
  `http://127.0.0.1:25109/gemini-eap-interactions/v1/chat/completions` (OpenAI body
  with `{"type":"tool_search"}` + `defer_loading:true`) reaches Gemini's
  `POST /v1beta/interactions` and is only rejected as
  `402 RESOURCE_EXHAUSTED: prepayment credits are depleted`.
- The Bun shim at `estate/ops/gemini-eap/eap-shim.mjs` hits the same 402 boundary.

## The ONE action that unblocks (human, account-holder, needs a payment method)

1. Open `https://ai.studio/projects` logged in as the account that owns
   project `654595778272` (gen-lang-client-0111199472).
2. Open that project → **Billing**.
3. **Add funds** to the Gemini API prepay wallet (a payment method is required).

Not needed: a new API key (keys are valid), a keypool/code change (routing is
correct), or a different billing account (Cloud billing account `Main`
`01D908-94C4CD-F167FF` is already open and linked; the wallet is separate).

Contact/verify after funding: rerun
`node /home/toxic/estate/ops/gemini-eap/eap-smoke.mjs` — it should return the
tool-retrieval response (status 200 + `steps`) instead of `402`.
