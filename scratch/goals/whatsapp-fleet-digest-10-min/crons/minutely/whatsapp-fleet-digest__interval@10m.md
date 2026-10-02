---
id: whatsapp-fleet-digest
title: WhatsApp fleet digest
enabled: true
owner: goal:whatsapp-fleet-digest-10-min
mode: task
schedule:
  kind: interval
  timezone: America/Denver
  at: 2026-09-14T14:46:06
  every: 10m
timeout_secs: 300
delivery:
  - surface: side_chat
    to: bb551bbc-81cd-4f77-a2d4-ead6d3eeaa78
metadata:
  originating_channel_context_json: '{"originating_channel":"side_chat","chat_kind":"direct","conversation_id":"bb551bbc-81cd-4f77-a2d4-ead6d3eeaa78","delivery_channel":"side_chat","delivery_target_id":"bb551bbc-81cd-4f77-a2d4-ead6d3eeaa78","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
WhatsApp fleet digest check (runs every 10 min; this chat is Chris's WhatsApp).

1. Run: bash ~/workspace/whatsapp-fleet-digest.sh — capture stdout. The script never advances the cursor itself; when there are new messages it ends with a CURSOR=<n> line.
2. If output is exactly NO_NEW_TRAFFIC: stay silent — produce no user-facing message.
3. If the script fails or prints DIGEST_ERROR: stay silent (transient vault issue). Do NOT touch the cursor file.
4. Otherwise the output is the digest: lines like `[#fleet] <sender> text`, plus a final CURSOR=<n> line.
   - Write <n> to ~/workspace/whatsapp-fleet-digest.cursor (advances past delivered messages; only when actually delivering).
   - Final user-facing message: one header line `Fleet — <k> new`, then the message lines WITHOUT the CURSOR line. Keep tight for a phone screen; if more than 20 messages arrived, summarize instead of dumping.
   - Lines marked `[sealed message]` stay as-is — never try to unseal or guess content.

Routine quiet runs never message the user.
