## 2026-09-14 13:52 MDT - Shingle-side (8a756bd0): Squawk lane split — no collisions

Chris asked for the relay as first-class direct code. Lanes, to avoid duplicate work:

1. **relay-in code path (THIS THREAD, new worker):** implements `chat.py relay-in` in the squawk repo — signed/sequenced post path, `relayed_from: muse-side-chat` frontmatter, smoke-tested in temp root, committed+pushed. Works in a scratch clone only; touches no canonical paths.
2. **Bootstrap (main side, d2aa5a33):** canonical clone /home/toxic/squawk, keys, channels. My earlier bootstrap worker (d4852a5e) COMPLETED WITHOUT DOING THE WORK — it backgrounded its first bridge call and ended the turn anyway. Lesson recorded in AGENTS.md. I am NOT re-spawning a competing bootstrap; main's lane owns it.
3. **Relay agent in Rig (main side, d23c8a01):** the runtime-agent consumer side. Complementary to lane 1 (repo code path) — wire together on completion via this file.

Chris's relay semantics (default, override anytime): his fleet-directed messages in the side chat get relayed into Squawk's fleet channel via relay-in; I (Shingle-side) trigger it in-turn until a tighter automation exists. Reverse direction (fleet -> Chris) stays as my summaries here.
