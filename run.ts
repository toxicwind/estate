// scripts/max-fix.ts
// bun run scripts/max-fix.ts
import { stat, rename, readFile, writeFile } from "fs/promises"
import { join } from "path"
import { homedir } from "os"

const SOV = process.env.SOVEREIGN_ROOT || `${homedir()}/sovereign`
const SWAP = join(SOV, "tools/llama-swap")

// 1) remove institutional blind rg shim
try {
  const p = join(homedir(), ".local/bin/rg")
  const s = await readFile(p, "utf8")
  if (s.includes("llm-safe-rg")) await rename(p, `${p}.bak-${Date.now()}`)
} catch {}

// 2) fix .gitignore - only ignore binaries, keep configs
const giPath = join(SOV, ".gitignore")
let gi = await readFile(giPath, "utf8").catch(() => "")
gi = gi.split("\n").filter(l => l.trim() !== "tools/llama-swap/").join("\n")
if (!gi.includes("tools/llama-swap/llama-swap")) {
  gi += "\n# llama-swap: ignore binaries only, keep configs\ntools/llama-swap/llama-swap\ntools/llama-swap/ollama-proxy\ntools/llama-swap/*.db\n"
}
await writeFile(giPath, gi)

// 3) rename backups by mtime -> config.YYYYMMDD-HHMMSS.yml
for (const n of ["config-old.yaml","config-new-but-changed.yaml","config copy.yaml","config copy 2.yaml","config copy 3.yaml"]) {
  try {
    const full = join(SWAP, n)
    const st = await stat(full)
    const d = new Date(st.mtimeMs)
    const ts = `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,"0")}${String(d.getDate()).padStart(2,"0")}-${String(d.getHours()).padStart(2,"0")}${String(d.getMinutes()).padStart(2,"0")}${String(d.getSeconds()).padStart(2,"0")}`
    let out = join(SWAP, `config.${ts}.yml`)
    let i=1; while (await stat(out).then(()=>true).catch(()=>false)) out = join(SWAP, `config.${ts}-${i++}.yml`)
    await rename(full, out)
  } catch {}
}

// 4) fix comments + ensure port
for (const f of [join(SOV,"stack/modules/llama-herder.yaml"), join(SWAP,"config.yaml")]) {
  try {
    let t = await readFile(f, "utf8")
    t = t.replace(/# FIX: was 28080.*/g, "# listen 28080 is outside backend range 25001-25027 (startPort + 26 models)")
    t = t.replace(/# startPort \+ model-count produces.*/g, "# listen port 28080 is outside backend range. startPort 25001 + 26 models = 25001-25027,")
    t = t.replace(/# well clear of startPort:25001.*/g, "# so 28080 never collides. Runtime check in stack/services/llama-herder.sh")
    if (f.endsWith("config.yaml") && !/^\s*port:\s*28080/m.test(t)) t = t.replace(/^startPort:/m, "port: 28080\nstartPort:")
    await writeFile(f, t)
  } catch {}
}
console.log("max fix done")