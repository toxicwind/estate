#!/usr/bin/env bun
// Permanent: parse cargo --message-format=json, apply MachineApplicable edits.
// Uses only stable Cargo/rustc APIs. No third-party deps.
import { $ } from "bun";
import { dirname, resolve } from "node:path";

const HERE   = dirname(new URL(import.meta.url).pathname);
const ENGINE = resolve(HERE, "..");
const MODE   = (process.argv[2] ?? "dry") as "dry" | "apply";

interface Diag {
  reason: string;
  message: {
    code: { code: string } | null;
    level: string;
    message: string;
    spans: Array<{ file_name: string; is_primary: boolean; line_start: number }>;
    suggestions: Array<{
      applicability: string;
      message: string;
      source: string;
      span: { file_name: string; byte_start: number; byte_end: number };
    }>;
  };
}

async function collect(): Promise<Diag[]> {
  const proc = Bun.spawn(
    ["cargo", "build", "--message-format=json", "--workspace"],
    { cwd: ENGINE, stdout: "pipe", stderr: "pipe" }
  );
  const text = await new Response(proc.stdout).text();
  await proc.exited;
  const out: Diag[] = [];
  for (const line of text.split("\n")) {
    if (!line.startsWith("{")) continue;
    try { const j = JSON.parse(line); if (j.reason === "compiler-message") out.push(j); } catch {}
  }
  return out;
}

function editsFrom(diags: Diag[]) {
  const e: Array<{ file: string; start: number; end: number; repl: string; msg: string }> = [];
  for (const d of diags) {
    const code = d.message.code?.code ?? "?";
    const prim = d.message.spans.find((s) => s.is_primary);
    for (const s of d.message.suggestions) {
      if (s.applicability !== "MachineApplicable") continue;
      e.push({
        file: s.span.file_name, start: s.span.byte_start, end: s.span.byte_end,
        repl: s.source,
        msg: `[${code}] ${prim?.file_name ?? "?"}:${prim?.line_start ?? 0} ${s.message}`,
      });
    }
  }
  return e;
}

async function applyAll(edits: ReturnType<typeof editsFrom>) {
  const byFile = new Map<string, typeof edits>();
  for (const e of edits) { const a = byFile.get(e.file) ?? []; a.push(e); byFile.set(e.file, a); }
  for (const [file, list] of byFile) {
    list.sort((a, b) => b.start - a.start);
    let bytes = new Uint8Array(await Bun.file(file).arrayBuffer());
    for (const e of list) {
      const before = bytes.slice(0, e.start);
      const after  = bytes.slice(e.end);
      const mid    = new TextEncoder().encode(e.repl);
      const next   = new Uint8Array(before.length + mid.length + after.length);
      next.set(before, 0); next.set(mid, before.length); next.set(after, before.length + mid.length);
      bytes = next;
    }
    await Bun.write(file, bytes);
    console.log(`  wrote ${file} (${list.length} edits)`);
  }
}

const diags = await collect();
const errs  = diags.filter((d) => d.message.level === "error");
const warns = diags.filter((d) => d.message.level === "warning");
console.log(`collected: ${errs.length} errors, ${warns.length} warnings`);
const edits = editsFrom(diags);
console.log(`machine-applicable edits: ${edits.length}`);
for (const e of edits.slice(0, 20)) console.log(`  ${e.msg}`);
if (MODE === "apply" && edits.length > 0) await applyAll(edits);
