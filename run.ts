#!/usr/bin/env bun
// capture-helps.ts — Bun version of your bash capture

type Build = {
  name: string;
  bin: string;
  ld: string;
};

const builds: Build[] = [
  {
    name: "beellama",
    bin: "/home/toxic/projects/beellama.cpp/build/bin/llama-server",
    ld: "/home/toxic/projects/beellama.cpp/build/bin",
  },
  {
    name: "llama-cpp-turboquant",
    bin: "/home/toxic/projects/llama-cpp-turboquant/build/bin/llama-server",
    ld: "/home/toxic/projects/llama-cpp-turboquant/build/bin",
  },
  {
    name: "ik_llama",
    bin: "/home/toxic/projects/ik_llama.cpp-main/build/bin/llama-server",
    ld: [
      "/home/toxic/projects/ik_llama.cpp-main/build/bin",
      "/home/toxic/projects/ik_llama.cpp-main/build/src",
      "/home/toxic/projects/ik_llama.cpp-main/build/ggml/src",
      "/home/toxic/projects/ik_llama.cpp-main/build/examples/mtmd", // libmtmd.so lives here
    ].join(":"),
  },
  {
    name: "ik_turboquant",
    bin: "/home/toxic/projects/ik_llama.cpp-main/build_turboquant/bin/llama-server",
    ld: [
      "/home/toxic/projects/ik_llama.cpp-main/build_turboquant/bin",
      "/home/toxic/projects/ik_llama.cpp-main/build_turboquant/src",
      "/home/toxic/projects/ik_llama.cpp-main/build_turboquant/ggml/src",
      "/home/toxic/projects/ik_llama.cpp-main/build_turboquant/examples/mtmd",
    ].join(":"),
  },
];

const outPath = "/tmp/llama_help_all.json";
const result: Record<string, string> = {};

for (const b of builds) {
  console.log(`=== ${b.name} ===`);
  const proc = Bun.spawnSync({
    cmd: [b.bin, "--help"],
    env: { ...process.env, LD_LIBRARY_PATH: b.ld },
    stdout: "pipe",
    stderr: "pipe",
  });

  const stdout = new TextDecoder().decode(proc.stdout);
  const stderr = new TextDecoder().decode(proc.stderr);
  // --help writes to stdout, but capture both like `2>&1`
  result[b.name] = stdout + stderr;

  if (proc.exitCode !== 0) {
    console.warn(`[${b.name}] exited ${proc.exitCode}`);
  }
}

await Bun.write(outPath, JSON.stringify(result, null, 2));
console.log(`\nWrote ${outPath}`);

// preview like your jq command
for (const [name, txt] of Object.entries(result)) {
  console.log({
    name,
    len: txt.length,
    preview: txt.slice(0, 200).replace(/\n/g, "\\n"),
  });
}