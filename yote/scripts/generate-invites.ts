#!/usr/bin/env bun
// scripts/generate-invites.ts
// Replaces scripts/telethon/generate_invites.py
//
// Walks every group/channel the userbot session can see, exports an
// invite link for each, and (optionally) DMs them to TARGET_USER.
//
// Usage: bun run scripts/generate-invites.ts

import { Overlord } from "../src/lib/overlord.ts";

const API_ID = parseInt(process.env.TELEGRAM_API_ID || "0");
const API_HASH = process.env.TELEGRAM_API_HASH || "";
const SESSION = process.env.TELEGRAM_SESSION || "";
const TARGET_USER = process.env.TARGET_USER || "";

if (!API_ID || !API_HASH || !SESSION) {
  console.error("Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION in .env");
  process.exit(1);
}

async function main() {
  const overlord = new Overlord({ apiId: API_ID, apiHash: API_HASH, session: SESSION });
  await overlord.start();

  const dialogs = await overlord.getDialogs();
  if (dialogs.status !== "ok") {
    console.error("Failed to list dialogs:", dialogs.error);
    process.exit(1);
  }

  const list = (dialogs as any).dialogs as { id: string; name: string; isGroup: boolean; isChannel: boolean }[];
  console.log(`Found ${list.length} dialogs.`);

  for (const d of list) {
    if (!d.isGroup && !d.isChannel) continue;
    const invite = await overlord.generateInvite(d.id);
    if (invite.status !== "ok") {
      console.log(`Failed for ${d.name}: ${invite.error}`);
      continue;
    }
    console.log(`${d.name}: ${(invite as any).link}`);
    if (TARGET_USER) {
      await overlord.sendMessage(TARGET_USER, `*${d.name}*:\n\`${(invite as any).link}\``);
    }
  }

  await overlord.stop();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
