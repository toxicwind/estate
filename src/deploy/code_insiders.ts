#!/usr/bin/env bun
/**
 * Sync VS Code Insiders → llama-swap via oaicopilot plugin settings (Bun).
 * Plugin-only: oaicopilot.baseUrl + oaicopilot.models; chatLanguageModels.json → [].
 */
import { homedir } from "os";
import { join } from "path";

const confPath =
  process.env.LLAMA_SWAP_CONFIG ||
  join(homedir(), "sovereign/tools/llama-swap/config.yaml");
const settingsPath =
  process.env.VSCODE_INSIDERS_SETTINGS ||
  join(homedir(), ".config/Code - Insiders/User/settings.json");
const clmPath =
  process.env.VSCODE_INSIDERS_CHAT_LM ||
  join(homedir(), ".config/Code - Insiders/User/chatLanguageModels.json");

function resolvePort(): string {
  if (process.env.LLAMA_SWAP_PORT) return process.env.LLAMA_SWAP_PORT;
  try {
    const mise = Bun.file(join(homedir(), "sovereign/mise.toml")).textSync();
    const m = mise.match(/LLAMA_SWAP_PORT\s*=\s*"(\d+)"/);
    if (m) return m[1];
  } catch {
    /* */
  }
  return "25100";
}

function parseModelIds(yamlText: string): string[] {
  // Prefer Bun.YAML when available
  try {
    const data = (Bun as unknown as { YAML: { parse: (s: string) => unknown } }).YAML.parse(
      yamlText,
    ) as { models?: Record<string, unknown> };
    if (data?.models && typeof data.models === "object") {
      return Object.keys(data.models).sort();
    }
  } catch {
    /* fall through */
  }
  const ids: string[] = [];
  let inModels = false;
  for (const line of yamlText.split("\n")) {
    if (/^models:\s*$/.test(line)) {
      inModels = true;
      continue;
    }
    if (inModels) {
      if (/^\S/.test(line) && !line.startsWith("#")) break;
      const m = line.match(/^\s{2}([A-Za-z0-9_./-]+):\s*$/);
      if (m) ids.push(m[1]);
    }
  }
  return ids.sort();
}

function ctx(name: string): number {
  const n = name.toLowerCase();
  for (const [tok, val] of [
    ["512k", 524288],
    ["256k", 262144],
    ["192k", 196608],
    ["128k", 131072],
    ["96k", 98304],
    ["64k", 65536],
    ["32k", 32768],
  ] as const) {
    if (n.includes(tok)) return val;
  }
  const m = n.match(/(\d+)(?=k)/);
  return m ? parseInt(m[1], 10) * 1024 : 65536;
}

const port = resolvePort();
const base = `http://127.0.0.1:${port}/v1`;
const yamlText = await Bun.file(confPath).text();
const modelIds = parseModelIds(yamlText);
if (!modelIds.length) {
  console.error("no models in", confPath);
  process.exit(1);
}

const oaicopilotModels = modelIds.map((id) => ({
  id,
  displayName: `local/${id.split("/").pop()}`,
  owned_by: "llama-swap",
  family: "oai-compatible",
  baseUrl: base,
  context_length: ctx(id),
  vision: id.toLowerCase().includes("gemma"),
  max_tokens: 8192,
  max_completion_tokens: 8192,
}));

let settings: Record<string, unknown> = {};
try {
  settings = JSON.parse(await Bun.file(settingsPath).text());
} catch {
  settings = {};
}

settings["oaicopilot.baseUrl"] = base;
settings["oaicopilot.models"] = oaicopilotModels;
settings["oaicopilot.logLevel"] = settings["oaicopilot.logLevel"] || "info";
settings["chat.utilitySmallModel"] = "oaicopilot/beellama/qwen-flash-64k";
delete settings["oai-compatible-copilot.providers"];

await Bun.write(settingsPath, JSON.stringify(settings, null, 2) + "\n");
await Bun.write(clmPath, "[]\n");

console.log(`port=${port} models=${oaicopilotModels.length} base=${base}`);
console.log(`settings=${settingsPath}`);
console.log(`utility=${settings["chat.utilitySmallModel"]}`);
console.log("chatLanguageModels=[]");
for (const m of oaicopilotModels.slice(0, 8)) console.log(`  ${m.id}`);
if (oaicopilotModels.length > 8) console.log(`  ... +${oaicopilotModels.length - 8} more`);
