/**
 * cascade.ts — Cascade API client for the proxy.
 *
 * Implements the 3-step cascade flow:
 *   StartCascade → SendUserCascadeMessage → poll GetCascadeTrajectorySteps
 *
 * Adapted from antigravity-mcp/src/lib/cascade-client.ts.
 */

import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";
import { randomUUID } from "node:crypto";
import { execSync } from "node:child_process";
import type { AntigravityInstance } from "./discovery.ts";

const LS_SERVICE = 'exa.language_server_pb.LanguageServerService';

// ─── Metadata ────────────────────────────────────────────────────────────────

const FINGERPRINT_PATH = path.join(os.homedir(), '.gemini', 'antigravity', '.proxy-fingerprint');

function getFingerprint(): string {
  try {
    if (fs.existsSync(FINGERPRINT_PATH)) {
      const fp = fs.readFileSync(FINGERPRINT_PATH, 'utf8').trim();
      if (fp) return fp;
    }
    const fp = randomUUID();
    fs.mkdirSync(path.dirname(FINGERPRINT_PATH), { recursive: true });
    fs.writeFileSync(FINGERPRINT_PATH, fp, 'utf8');
    return fp;
  } catch {
    return '8a666781-eba7-4c3d-8102-6c01ddf55435';
  }
}

function readApiKey(): string {
  const dbPath = path.join(
    os.homedir(),
    'Library/Application Support/Antigravity/User/globalStorage/state.vscdb',
  );
  if (!fs.existsSync(dbPath)) return '';
  try {
    const out = execSync(
      `sqlite3 "${dbPath}" "SELECT value FROM ItemTable WHERE key='antigravityAuthStatus'"`,
      { encoding: 'utf8', timeout: 5000 },
    ).trim();
    const data = JSON.parse(out) as { apiKey?: string };
    return data.apiKey ?? '';
  } catch {
    return '';
  }
}

function buildMetadata(): object {
  return {
    ideName: 'Antigravity',
    ideVersion: '1.18.3',
    extensionName: 'Antigravity',
    extensionVersion: '1.18.3',
    locale: 'en',
    os: 'darwin',
    sessionId: randomUUID(),
    deviceFingerprint: getFingerprint(),
    apiKey: readApiKey(),
  };
}

// ─── HTTP helper ─────────────────────────────────────────────────────────────

/** Bun-native HTTP POST (no node:http) */
async function httpPost(
  instance: AntigravityInstance,
  method: string,
  body: string,
  timeoutMs = 30_000,
): Promise<string> {
  const res = await fetch(
    `http://127.0.0.1:${instance.port}/${LS_SERVICE}/${method}`,
    {
      method: "POST",
      headers: {
        "x-codeium-csrf-token": instance.csrfToken,
        "Content-Type": "application/json",
        "Accept-Encoding": "identity",
      },
      body,
      signal: AbortSignal.timeout(timeoutMs),
    },
  );
  return await res.text();
}

async function callRpc<T>(
  instance: AntigravityInstance,
  method: string,
  body: unknown,
  timeoutMs?: number,
): Promise<T> {
  const respText = await httpPost(instance, method, JSON.stringify(body), timeoutMs);

  let parsed: unknown;
  try {
    parsed = JSON.parse(respText);
  } catch {
    throw new Error(`callRpc ${method}: invalid JSON: ${respText.slice(0, 200)}`);
  }

  if (
    typeof parsed === 'object' &&
    parsed !== null &&
    'code' in parsed &&
    'message' in parsed
  ) {
    const err = parsed as { code: unknown; message: unknown };
    throw new Error(`callRpc ${method} server error ${String(err.code)}: ${String(err.message)}`);
  }

  return parsed as T;
}

// ─── Cascade API ─────────────────────────────────────────────────────────────

/** Start a new cascade session and return the cascadeId. */
export async function startCascade(instance: AntigravityInstance): Promise<string> {
  const metadata = buildMetadata();
  const resp = await callRpc<{ cascadeId: string }>(instance, 'StartCascade', {
    metadata,
    source: 'user',
    trajectoryType: 'CASCADE',
  });
  return resp.cascadeId;
}

/** Send a user message into an existing cascade session. */
export async function sendUserMessage(
  instance: AntigravityInstance,
  cascadeId: string,
  prompt: string,
  modelId: number,
  agenticMode = false,
): Promise<void> {
  const metadata = buildMetadata();
  const body = {
    metadata,
    cascadeId,
    items: [{ text: prompt }],
    clientType: 3, // SDK_EXECUTABLE
    messageOrigin: 3,
    cascadeConfig: {
      plannerConfig: {
        planModel: modelId,
        conversational: { agenticMode },
        requestedModel: { model: modelId },
        maxOutputTokens: 8192,
      },
      checkpointConfig: {
        maxOutputTokens: 8192,
      },
    },
  };

  await httpPost(instance, 'SendUserCascadeMessage', JSON.stringify(body), 30_000);
}

export interface PollResult {
  responseText: string;
  generatorModel?: string;
  messageId?: string;
}

/**
 * Poll GetCascadeTrajectorySteps with exponential backoff until a
 * PLANNER_RESPONSE step appears.
 *
 * Backoff: 500ms → 1s → 2s → 4s (max 8s per interval, max 120s total)
 */
export async function pollForResponse(
  instance: AntigravityInstance,
  cascadeId: string,
  opts: { timeoutMs?: number } = {},
): Promise<PollResult> {
  const timeoutMs = opts.timeoutMs ?? 120_000;
  const deadline = Date.now() + timeoutMs;

  let interval = 500;
  let attempt = 0;

  while (Date.now() < deadline) {
    if (attempt > 0) {
      await new Promise<void>((r) => setTimeout(r, Math.min(interval, 8_000)));
      interval = Math.min(interval * 2, 8_000);
    }
    attempt++;

    let resp: { steps?: unknown[] };
    try {
      resp = await callRpc<{ steps?: unknown[] }>(
        instance,
        'GetCascadeTrajectorySteps',
        { cascadeId },
        10_000,
      );
    } catch (e) {
      process.stderr.write(`[cascade] poll attempt ${attempt} error: ${e}\n`);
      continue;
    }

    const steps = resp.steps ?? [];
    for (const step of steps) {
      if (typeof step !== 'object' || step === null || !('type' in step)) continue;

      const s = step as Record<string, unknown>;

      // type 4 = CORTEX_STEP_TYPE_PLANNER_RESPONSE
      if (s['type'] !== 4 && s['type'] !== 'CORTEX_STEP_TYPE_PLANNER_RESPONSE') continue;

      const pr = s['plannerResponse'] as Record<string, unknown> | undefined;
      if (!pr) continue;

      const text = (pr['modifiedResponse'] ?? pr['response']) as string | undefined;
      if (!text || text.trim().length === 0) continue;

      const meta = s['metadata'] as Record<string, unknown> | undefined;
      const generatorModel = meta?.['generatorModel'] as string | undefined;
      const messageId = pr['messageId'] as string | undefined;

      return { responseText: text.trim(), generatorModel, messageId };
    }
  }

  throw new Error(`pollForResponse: timeout after ${timeoutMs}ms — no PLANNER_RESPONSE found`);
}

/**
 * Convert OpenAI messages array to a single prompt string.
 * Prepends any system messages as context.
 */
export function messagesToPrompt(
  messages: Array<{ role: string; content: string }>,
): string {
  const system = messages
    .filter((m) => m.role === 'system')
    .map((m) => m.content)
    .join('\n\n');

  // Get the last user message (most recent turn)
  const userMessages = messages.filter((m) => m.role === 'user' || m.role === 'assistant');

  let prompt = '';

  if (system) {
    prompt += `[System Instructions]\n${system}\n\n`;
  }

  // Include conversation history if multi-turn
  for (const msg of userMessages) {
    if (msg.role === 'user') {
      prompt += `User: ${msg.content}\n`;
    } else if (msg.role === 'assistant') {
      prompt += `Assistant: ${msg.content}\n`;
    }
  }

  // Strip the trailing "User: " prefix added in the loop — cascade expects just the prompt text
  // Actually, for a clean cascade experience: just return the last user message with system context
  const lastUser = messages.filter((m) => m.role === 'user').at(-1);
  if (!lastUser) {
    return prompt.trim();
  }

  if (system && userMessages.length <= 1) {
    // Simple: single user message with system context
    return `${system}\n\n${lastUser.content}`.trim();
  }

  // Multi-turn: include full conversation
  return prompt.trim();
}
