#!/usr/bin/env bun
/**
 * bun hardware audit script
 *
 * Usage:
 *   bun run ./audit.ts [output-file]
 *
 * Default output file: ./hardware_audit.txt
 *
 * What it does (safe, read-only):
 *  - Runs a curated set of read-only commands (lspci, dmesg, /proc reads, lsmod, sensors if present)
 *  - Collects and normalizes outputs
 *  - Attempts to parse a few high-value fields (PCIe link width/speed, NVIDIA BARs, CPU flags)
 *  - Writes both a human-readable report and a compact JSON summary to disk
 *
 * Notes:
 *  - This script never writes to system config or loads modules.
 *  - It tolerates missing commands/files and records errors in the output file.
 */

import { execSync } from "child_process";
import { writeFileSync } from "fs";
import { argv } from "process";

const OUT = argv[2] ?? "./hardware_audit.txt";

function run(cmd: string) {
  try {
    return execSync(cmd, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
  } catch (err: any) {
    // Return the error message but keep going
    return `ERROR: ${err?.message ?? String(err)}`;
  }
}

function safeRead(path: string) {
  try {
    return execSync(`cat ${path}`, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
  } catch (err: any) {
    return `MISSING: ${path} (${err?.code ?? err?.message ?? "read error"})`;
  }
}

function parseLspciLink(lspciVv: string) {
  // Find first LnkSta and LnkCap lines and extract Width/Speed
  const lines = lspciVv.split("\n");
  let linkInfo: { LnkSta?: string; LnkCap?: string } = {};
  for (const ln of lines) {
    const t = ln.trim();
    if (t.startsWith("LnkSta:")) linkInfo.LnkSta = t;
    if (t.startsWith("LnkCap:")) linkInfo.LnkCap = t;
  }
  return linkInfo;
}

function extractNvidiaSections(lspciAll: string) {
  // Return blocks for NVIDIA devices (by vendor string)
  const blocks: string[] = [];
  const lines = lspciAll.split("\n");
  let cur: string[] = [];
  for (const ln of lines) {
    if (/^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9]/.test(ln)) {
      if (cur.length) {
        blocks.push(cur.join("\n"));
        cur = [];
      }
    }
    cur.push(ln);
  }
  if (cur.length) blocks.push(cur.join("\n"));
  return blocks.filter(b => /NVIDIA|nvidia/i.test(b));
}

function parseCpuFlags(cpuinfo: string) {
  // Grab the first "flags" line and return array
  const m = cpuinfo.match(/flags\s*:\s*(.+)/i);
  if (!m) return [];
  return m[1].trim().split(/\s+/);
}

function shortTimestamp() {
  return new Date().toISOString();
}

async function main() {
  const reportLines: string[] = [];
  const jsonSummary: Record<string, any> = { timestamp: shortTimestamp(), collected: {} };

  reportLines.push(`=== SOVEREIGN AUDIT REPORT ===`);
  reportLines.push(`Generated: ${jsonSummary.timestamp}`);
  reportLines.push("");

  // 1) Basic system files
  reportLines.push("=== /proc and kernel info ===");
  const procCpuinfo = safeRead("/proc/cpuinfo");
  reportLines.push("/proc/cpuinfo (first 1200 chars):");
  reportLines.push(procCpuinfo.slice(0, 1200));
  reportLines.push("");
  jsonSummary.collected["cpuinfo_sample"] = procCpuinfo.split("\n").slice(0, 40).join("\n");
  jsonSummary.collected["cpu_flags"] = parseCpuFlags(procCpuinfo);

  const procIomem = safeRead("/proc/iomem");
  reportLines.push("/proc/iomem (first 800 chars):");
  reportLines.push(procIomem.slice(0, 800));
  reportLines.push("");
  jsonSummary.collected["iomem_head"] = procIomem.split("\n").slice(0, 40).join("\n");

  // 2) lspci
  reportLines.push("=== PCI / lspci ===");
  const lspciAll = run("lspci -vvnn 2>/dev/null || true");
  reportLines.push("lspci -vvnn (first 2000 chars):");
  reportLines.push(lspciAll.slice(0, 2000));
  reportLines.push("");
  jsonSummary.collected["lspci_head"] = lspciAll.split("\n").slice(0, 80).join("\n");

  // Extract NVIDIA blocks and attempt to get link info for the first NVIDIA device
  const nvidiaBlocks = extractNvidiaSections(lspciAll);
  jsonSummary.collected["nvidia_blocks_count"] = nvidiaBlocks.length;
  if (nvidiaBlocks.length) {
    reportLines.push("--- NVIDIA device blocks (first block):");
    reportLines.push(nvidiaBlocks[0].slice(0, 1200));
    reportLines.push("");
    // Try to get link info for the first PCI address found in that block
    const addrMatch = nvidiaBlocks[0].match(/^([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9])/m);
    if (addrMatch) {
      const addr = addrMatch[1];
      const lspciVv = run(`lspci -s ${addr} -vv 2>/dev/null || true`);
      reportLines.push(`lspci -s ${addr} -vv:`);
      reportLines.push(lspciVv.slice(0, 1200));
      reportLines.push("");
      jsonSummary.collected["nvidia_lspci_vv"] = lspciVv.split("\n").slice(0, 80).join("\n");
      jsonSummary.collected["nvidia_link_info"] = parseLspciLink(lspciVv);
    }
  } else {
    reportLines.push("No NVIDIA blocks detected by lspci output.");
  }

  // 3) PCI config space (if set of files exist)
  reportLines.push("=== PCI config space (if available) ===");
  const pciCfg = run("for f in /sys/bus/pci/devices/*/config; do echo '---' $f; hexdump -C -n 64 $f 2>/dev/null || true; done | sed -n '1,200p' || true");
  reportLines.push(pciCfg);
  jsonSummary.collected["pci_config_head"] = pciCfg.split("\n").slice(0, 80).join("\n");

  // 4) Kernel modules and loaded drivers
  reportLines.push("=== lsmod / loaded modules ===");
  const lsmod = run("lsmod 2>/dev/null || true");
  reportLines.push(lsmod);
  reportLines.push("");
  jsonSummary.collected["lsmod"] = lsmod.split("\n").slice(0, 80).join("\n");

  // 5) dmesg tail (safely)
  reportLines.push("=== dmesg (tail 200 lines) ===");
  const dmesgTail = run("dmesg --ctime --level=err,warn,info 2>/dev/null | tail -n 200 || dmesg | tail -n 200 || true");
  reportLines.push(dmesgTail);
  reportLines.push("");
  jsonSummary.collected["dmesg_tail"] = dmesgTail.split("\n").slice(-200).join("\n");

  // 6) I2C / SMBus listing
  reportLines.push("=== I2C / SMBus adapters ===");
  const i2cList = run("ls /sys/class/i2c-adapter 2>/dev/null || true; echo '--- i2cdetect (may require root) ---'; which i2cdetect >/dev/null 2>&1 && i2cdetect -l || true");
  reportLines.push(i2cList);
  reportLines.push("");
  jsonSummary.collected["i2c_list"] = i2cList.split("\n").slice(0, 80).join("\n");

  // 7) NVMe / storage
  reportLines.push("=== NVMe / block devices ===");
  const nvme = run("lsblk -o NAME,MODEL,SIZE,ROTA,TYPE,MOUNTPOINT 2>/dev/null || true");
  reportLines.push(nvme);
  reportLines.push("");
  const nvmeSmart = run("for d in /dev/nvme*; do [ -b \"$d\" ] && echo '---' $d && nvme id-ctrl $d 2>/dev/null || true; done | sed -n '1,200p' || true");
  reportLines.push(nvmeSmart.slice(0, 1200));
  reportLines.push("");
  jsonSummary.collected["lsblk"] = nvme.split("\n").slice(0, 80).join("\n");

  // 8) Thermal / sensors (if available)
  reportLines.push("=== sensors / thermal ===");
  const sensors = run("which sensors >/dev/null 2>&1 && sensors || echo 'sensors not installed or no access'");
  reportLines.push(sensors);
  reportLines.push("");
  jsonSummary.collected["sensors_head"] = sensors.split("\n").slice(0, 40).join("\n");

  // 9) perf / resctrl presence
  reportLines.push("=== perf / resctrl presence ===");
  const perfList = run("which perf >/dev/null 2>&1 && perf --version || echo 'perf not present'");
  const resctrl = run("test -d /sys/fs/resctrl && echo 'resctrl mounted' || echo 'resctrl not mounted'");
  reportLines.push(perfList);
  reportLines.push(resctrl);
  reportLines.push("");
  jsonSummary.collected["perf"] = perfList;
  jsonSummary.collected["resctrl"] = resctrl;

  // 10) Read common bootloader/limine paths safely
  reportLines.push("=== Bootloader / Limine checks ===");
  const liminePaths = [
    "/boot/limine/limine.conf",
    "/boot/limine.cfg",
    "/etc/limine/limine.conf",
    "/sys/firmware/efi/efivars"
  ];
  for (const p of liminePaths) {
    reportLines.push(`${p}:`);
    reportLines.push(safeRead(p));
    reportLines.push("");
  }

  // 11) Small AVX-512 microbenchmark compile/run (optional) - only if gcc exists
  reportLines.push("=== AVX-512 microbenchmark (compile/run if gcc present) ===");
  const hasGcc = run("which gcc >/dev/null 2>&1 && echo yes || echo no").trim();
  if (hasGcc === "yes") {
    const cSrc = `
#include <immintrin.h>
#include <stdio.h>
int main() {
    __m512i a = _mm512_set1_epi32(1);
    __m512i b = _mm512_set1_epi32(2);
    __m512i c = _mm512_add_epi32(a,b);
    int out[16];
    _mm512_storeu_si512(out, c);
    printf("%d\\n", out[0]);
    return 0;
}
`;
    try {
      writeFileSync("./__avx512_test.c", cSrc);
      const cc = run("gcc -O2 -mavx512f __avx512_test.c -o __avx512_test 2>&1 || true");
      if (cc.startsWith("ERROR") || cc.includes("error")) {
        reportLines.push("gcc compile failed or AVX-512 not supported by toolchain:");
        reportLines.push(cc);
        jsonSummary.collected["avx512_compile"] = cc;
      } else {
        const out = run("./__avx512_test 2>&1 || true");
        reportLines.push("AVX-512 microbenchmark output:");
        reportLines.push(out);
        jsonSummary.collected["avx512_run"] = out;
      }
    } catch (e: any) {
      reportLines.push("AVX-512 microbenchmark step failed: " + String(e?.message ?? e));
    } finally {
      try { run("rm -f __avx512_test __avx512_test.c __avx512_test.o __avx512_test.s || true"); } catch {}
    }
  } else {
    reportLines.push("gcc not present; skipping AVX-512 microbenchmark.");
  }
  reportLines.push("");

  // 12) Final summary lines and write to disk
  reportLines.push("=== SUMMARY ===");
  reportLines.push(`Collected items: ${Object.keys(jsonSummary.collected).length}`);
  reportLines.push("");
  reportLines.push("End of report.");

  // Write human-readable report and JSON summary to disk
  try {
    const human = reportLines.join("\n");
    const json = JSON.stringify(jsonSummary, null, 2);
    const combined = [
      human,
      "\n\n--- MACHINE-READABLE JSON SUMMARY ---\n",
      json
    ].join("\n");
    writeFileSync(OUT, combined, { encoding: "utf8" });
    console.log(`Audit written to ${OUT}`);
  } catch (err: any) {
    console.error("Failed to write output file:", err?.message ?? err);
    process.exit(2);
  }
}

main().catch(err => {
  console.error("Unhandled error:", err?.message ?? err);
  process.exit(1);
});
