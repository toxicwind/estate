#!/usr/bin/env bun
/**
 * Sovereign Kimi-Claw Bridge
 * Connects Kimi IM / Bridge events to OpenFang (:25103), Herd (:25100), and HAL Substrate (:25143).
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { homedir } from "node:os";

const HOME = homedir();
const HERD_URL = process.env.HERD_URL || "http://127.0.0.1:25100/v1";
const OPENFANG_URL = process.env.OPENFANG_URL || "http://127.0.0.1:25103";
const HAL_URL = process.env.HAL_URL || "http://127.0.0.1:25143";

export interface KimiBridgeConfig {
  herdUrl: string;
  openfangUrl: string;
  halUrl: string;
  kimiToken?: string;
  userId?: string;
}

export function loadKimiConfig(): KimiBridgeConfig {
  let token = process.env.KIMI_API_KEY || process.env.KIMI_BRIDGE_TOKEN;
  let userId = process.env.KIMI_USER_ID;

  const secretsPath = resolve(HOME, ".secrets");
  if (existsSync(secretsPath)) {
    const lines = readFileSync(secretsPath, "utf8").split("\n");
    for (const line of lines) {
      if (line.startsWith("KIMI_API_KEY=") && !token) {
        token = line.slice("KIMI_API_KEY=".length).trim().replace(/^['"]|['"]$/g, "");
      }
      if (line.startsWith("KIMI_BRIDGE_TOKEN=") && !token) {
        token = line.slice("KIMI_BRIDGE_TOKEN=".length).trim().replace(/^['"]|['"]$/g, "");
      }
      if (line.startsWith("KIMI_USER_ID=") && !userId) {
        userId = line.slice("KIMI_USER_ID=".length).trim().replace(/^['"]|['"]$/g, "");
      }
    }
  }

  return {
    herdUrl: HERD_URL,
    openfangUrl: OPENFANG_URL,
    halUrl: HAL_URL,
    kimiToken: token,
    userId,
  };
}

export async function dispatchToOpenFang(message: string, agent = "coyote"): Promise<string> {
  try {
    const res = await fetch(`${OPENFANG_URL}/api/agents/${agent}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (res.ok) {
      const data = await res.json() as { response?: string; content?: string; text?: string };
      return data.response || data.content || data.text || JSON.stringify(data);
    }
  } catch (err) {
    console.warn(`[Kimi-Claw] OpenFang dispatch failed, falling back to Herd: ${err}`);
  }

  // Fallback to Herd
  return dispatchToHerd(message);
}

export async function dispatchToHerd(prompt: string, model = "beellama/qwen-flash-128k"): Promise<string> {
  try {
    const res = await fetch(`${HERD_URL}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages: [{ role: "user", content: prompt }],
        temperature: 0.7,
      }),
    });
    if (res.ok) {
      const data = await res.json() as { choices?: Array<{ message?: { content?: string } }> };
      return data.choices?.[0]?.message?.content || "[No output from Herd]";
    }
    return `[Herd Error: ${res.statusText}]`;
  } catch (err) {
    return `[Herd Exception: ${err}]`;
  }
}

if (import.meta.main) {
  const config = loadKimiConfig();
  console.log(`[Kimi-Claw Bridge] Initialized. Herd: ${config.herdUrl}, OpenFang: ${config.openfangUrl}, HAL: ${config.halUrl}`);
}
