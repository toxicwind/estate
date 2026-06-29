import { $ } from "bun";

const HOME = Bun.env.HOME || "/home/toxic";
const GROK = `${HOME}/.grok`;
const SOV = `${HOME}/sovereign`;

async function version(bin: string): Promise<string> {
  const proc = Bun.spawn([bin, "--version"], { stdout: "pipe", stderr: "ignore" });
  const out = await new Response(proc.stdout).text();
  return out.trim() || "not found";
}

async function fdList(dir: string, ext?: string, maxDepth = 99): Promise<string[]> {
  const args = ["--type", "f", "--max-depth", String(maxDepth)];
  if (ext) args.push("-e", ext);
  args.push(dir);
  const proc = Bun.spawn(["fd", ...args], { stdout: "pipe", stderr: "ignore" });
  const out = await new Response(proc.stdout).text();
  return out.split("\n").filter(Boolean);
}

async function rgCtx(dir: string, pattern: string, ctx = 2): Promise<string> {
  const proc = Bun.spawn(["rg", "--json", "-C", String(ctx), pattern, dir], { stdout: "pipe", stderr: "ignore" });
  return new Response(proc.stdout).text();
}

async function dumpJsonl(dir: string, outPath: string, maxBytes = 50_000) {
  const files = await fdList(dir);
  const writer = Bun.file(outPath).writer();
  for (const f of files) {
    const rel = f.replace(`${dir}/`, "");
    const stat = await Bun.file(f).stat().catch(() => null);
    if (!stat) continue;
    const ext = f.slice(f.lastIndexOf("."));
    const isText = [".toml",".json",".md",".txt",".py",".ts",".js",".sh",".nix",".yaml",".yml"].includes(ext);
    if (isText && stat.size < maxBytes) {
      const text = await Bun.file(f).text();
      writer.write(JSON.stringify({ path: rel, size: stat.size, type: "text", content: text }) + "\n");
    } else if (isText) {
      const buf = await Bun.file(f).arrayBuffer();
      const slice = new TextDecoder("utf-8", { fatal: false }).decode(buf.slice(0, maxBytes)) + "\n... [truncated]";
      writer.write(JSON.stringify({ path: rel, size: stat.size, type: "text", content: slice }) + "\n");
    } else {
      writer.write(JSON.stringify({ path: rel, size: stat.size, type: "binary" }) + "\n");
    }
  }
  await writer.end();
  console.log(`Wrote ${files.length} entries → ${outPath}`);
}

console.log(`rg:  ${await version("rg")}`);
console.log(`fd:  ${await version("fd")}`);

console.log("\n--- .grok config.toml ---");
console.log(await Bun.file(`${GROK}/config.toml`).text().catch(() => "not found"));

console.log("\n--- sovereign config.toml ---");
console.log(await Bun.file(`${SOV}/config.toml`).text().catch(() => "not found"));

await dumpJsonl(GROK, `${HOME}/grok_full.jsonl`);
await dumpJsonl(SOV, `${HOME}/sovereign_full.jsonl`);
