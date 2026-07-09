#!/usr/bin/env bun
// scripts/overlord-login.ts
// One-time login — saves a permanent GramJS session to .env

import { Overlord } from "../src/lib/overlord";
import { readFileSync, writeFileSync } from "fs";
import { resolve } from "path";

const API_ID = Number(process.env.TELEGRAM_API_ID);
const API_HASH = process.env.TELEGRAM_API_HASH;
const ENV_PATH = resolve(process.cwd(), ".env");

if (!API_ID ||!API_HASH) {
  console.error("❌ Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env first");
  process.exit(1);
}

// if we already have a session, just verify it
if (process.env.TELEGRAM_SESSION) {
  console.log("✅ TELEGRAM_SESSION already exists — testing...");
  const test = new Overlord({ apiId: API_ID, apiHash: API_HASH, session: process.env.TELEGRAM_SESSION });
  try {
    await test.start();
    await test.stop();
    console.log("Session is valid. No need to re-login.");
    process.exit(0);
  } catch {
    console.log("Session invalid — creating new one...");
  }
}

console.log("Logging in (this creates a permanent session)...");
const session = await Overlord.interactiveLogin(API_ID, API_HASH);

// update .env in place
let env = "";
try { env = readFileSync(ENV_PATH, "utf8"); } catch {}
if (env.includes("TELEGRAM_SESSION=")) {
  env = env.replace(/TELEGRAM_SESSION=.*/,"TELEGRAM_SESSION="+session);
} else {
  env += `\nTELEGRAM_SESSION=${session}\n`;
}
writeFileSync(ENV_PATH, env);

console.log("\n✅ Permanent session saved to .env");
console.log("You will never need to run this again unless you log out from Telegram.");