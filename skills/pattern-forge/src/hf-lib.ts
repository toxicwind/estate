import { join } from "node:path";
import { homedir } from "node:os";
import { readFileSync } from "node:fs";

const TOKEN_KEYS = ["HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HF_AUTH_TOKEN"];

export function resolveMaybe(envKeys: string[], vaultPaths: string[]): { key: string; from: string } {
  for (const k of envKeys) {
    const v = process.env[k]?.trim();
    if (v) return { key: v, from: `environment:${k}` };
  }
  for (const p of vaultPaths) {
    try {
      const vault = readFileSync(p, "utf8");
      const re = new RegExp(`^\\s*(?:export\\s+)?(?:${envKeys.join("|")})\\s*=\\s*["']?([^"'\\n#]+)["']?`, "m");
      const hit = vault.match(re);
      if (hit?.[1]?.trim()) return { key: hit[1].trim(), from: `${p} (vault)` };
    } catch {
      /* continue */
    }
  }
  return { key: "", from: "not found" };
}

export const HF_TOKEN = resolveMaybe(TOKEN_KEYS, [join(homedir(), ".secrets"), join(homedir(), ".bashrc.env")]).key;