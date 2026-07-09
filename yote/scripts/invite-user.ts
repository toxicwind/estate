#!/usr/bin/env bun
// scripts/invite-user.ts
// Replaces scripts/telethon/invite_puppertrix.py
//
// Invites a given @username to every group/channel visible to the
// userbot session. The original script hardcoded "puppertrix" — this
// version takes the target as a CLI arg so it's reusable.
//
// Usage: bun run scripts/invite-user.ts <username>

import { Overlord } from "../src/lib/overlord.ts";

const API_ID = parseInt(process.env.TELEGRAM_API_ID || "0");
const API_HASH = process.env.TELEGRAM_API_HASH || "";
const SESSION = process.env.TELEGRAM_SESSION || "";
const TARGET = process.argv[2];

if (!TARGET) {
  console.error("Usage: bun run scripts/invite-user.ts <username>");
  process.exit(1);
}
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

  for (const d of list) {
    if (!d.isGroup && !d.isChannel) continue;
    const result = await overlord.inviteUser(d.id, TARGET, d.isChannel);
    if (result.status === "ok") {
      console.log(`Invited ${TARGET} to ${d.name}`);
    } else {
      console.log(`Failed ${d.name}: ${result.error}`);
    }
  }

  await overlord.stop();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
