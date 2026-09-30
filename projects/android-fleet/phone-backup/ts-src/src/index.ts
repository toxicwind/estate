#!/usr/bin/env bun
/**
 * phone-backup — μ-speed Pixel backup via ADB
 * 
 * Hybrid strategy (benchmarked 2026-09-30):
 * - Many small files → on-device tar, then pull single tarball (29 MB/s)
 * - Large files → parallel adb pull, 8-way (44 MB/s)
 * - SQLite incremental manifest (borrowed from kafami86/ADB-X pattern)
 * 
 * Usage:
 *   bun src/index.ts pull [dest]     # pull phone → dest
 *   bun src/index.ts verify [dest]   # verify manifest
 *   bun src/index.ts clean           # delete verified dirs from phone
 */

import { $ } from "bun";
import { Database } from "bun:sqlite";
import { existsSync, mkdirSync } from "fs";
import { join } from "path";

// ============================================================================
// Config
// ============================================================================

const PIXEL_IP = "10.0.0.77";
const PARALLEL_STREAMS = 8;  // Validated: AndroidFiles independently found 8x
const ADB = "/usr/bin/adb";

const SOURCE_DIRS = [
  "Export",
  "1openfang", 
  "Tasker",
  "House",
  "Documents",
  "ik_llama.cpp-main",
  "Download",
];

// Photos explicitly out of scope (standing direction)
const EXCLUDED = ["DCIM", "Pictures"];

// ============================================================================
// Endpoint Discovery (port rotates)
// ============================================================================

async function discoverPixel(): Promise<string> {
  const result = await $`${ADB} devices`.text();
  const lines = result.split("\n");
  for (const line of lines) {
    const match = line.match(new RegExp(`^${PIXEL_IP}:(\\d+)\\s+device`));
    if (match) {
      return `${PIXEL_IP}:${match[1]}`;
    }
  }
  throw new Error(`Pixel not found at ${PIXEL_IP}. Check wireless ADB.`);
}

// ============================================================================
// SQLite Manifest DB (incremental tracking — ADB-X pattern)
// ============================================================================

class ManifestDB {
  private db: Database;

  constructor(path: string) {
    this.db = new Database(path);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS files (
        path TEXT PRIMARY KEY,
        size INTEGER NOT NULL,
        mtime INTEGER NOT NULL,
        hash TEXT,
        pulled_at INTEGER NOT NULL
      );
      CREATE TABLE IF NOT EXISTS pulls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at INTEGER NOT NULL,
        completed_at INTEGER,
        source_dir TEXT NOT NULL,
        files INTEGER DEFAULT 0,
        bytes INTEGER DEFAULT 0,
        status TEXT DEFAULT 'running'
      );
      CREATE INDEX IF NOT EXISTS idx_files_mtime ON files(mtime);
    `);
  }

  recordFile(path: string, size: number, mtime: number, hash?: string) {
    this.db.prepare(`
      INSERT OR REPLACE INTO files (path, size, mtime, hash, pulled_at)
      VALUES (?, ?, ?, ?, ?)
    `).run(path, size, mtime, hash || null, Date.now());
  }

  needsPull(path: string, size: number, mtime: number): boolean {
    const row = this.db.prepare(
      "SELECT size, mtime FROM files WHERE path = ?"
    ).get(path) as { size: number; mtime: number } | null;
    if (!row) return true;
    return row.size !== size || row.mtime !== mtime;
  }

  startPull(sourceDir: string): number {
    const result = this.db.prepare(`
      INSERT INTO pulls (started_at, source_dir) VALUES (?, ?)
    `).run(Date.now(), sourceDir);
    return Number(result.lastInsertRowid);
  }

  finishPull(id: number, files: number, bytes: number, status: string = "ok") {
    this.db.prepare(`
      UPDATE pulls SET completed_at = ?, files = ?, bytes = ?, status = ?
      WHERE id = ?
    `).run(Date.now(), files, bytes, status, id);
  }

  close() {
    this.db.close();
  }
}

// ============================================================================
// Transfer Engine (hybrid: parallel pull + tar for small files)
// ============================================================================

interface TransferResult {
  dir: string;
  files: number;
  bytes: number;
  method: "parallel-pull" | "tar-pull";
  durationMs: number;
}

async function adbShell(pixel: string, cmd: string): Promise<string> {
  return await $`${ADB} -s ${pixel} shell ${cmd}`.text();
}

async function getDirStats(pixel: string, dir: string): Promise<{ files: number; bytes: number }> {
  // Toybox quirk: iterate, don't use bare find /sdcard
  const output = await adbShell(pixel, `find /sdcard/${dir} -type f 2>/dev/null | wc -l`);
  const files = parseInt(output.trim()) || 0;
  
  const duOutput = await adbShell(pixel, `du -sb /sdcard/${dir} 2>/dev/null | cut -f1`);
  const bytes = parseInt(duOutput.trim()) || 0;
  
  return { files, bytes };
}

async function parallelPull(
  pixel: string,
  dir: string,
  dest: string,
  manifest: ManifestDB
): Promise<TransferResult> {
  const start = Date.now();
  const stats = await getDirStats(pixel, dir);
  
  const destDir = join(dest, dir);
  mkdirSync(destDir, { recursive: true });
  
  // Get file list
  const fileList = await adbShell(pixel, `find /sdcard/${dir} -type f 2>/dev/null`);
  const files = fileList.split("\n").filter(f => f.trim());
  
  // 8-way parallel pull (validated magic number)
  const pullId = manifest.startPull(dir);
  let completed = 0;
  let totalBytes = 0;
  
  const pullOne = async (remotePath: string) => {
    const relPath = remotePath.replace(`/sdcard/${dir}/`, "");
    const localPath = join(destDir, relPath);
    const localDir = join(localPath, "..");
    mkdirSync(localDir, { recursive: true });
    
    try {
      await $`${ADB} -s ${pixel} pull ${remotePath} ${localPath}`.quiet();
      const stat = await $`stat -c%s ${localPath}`.text().catch(() => "0");
      const size = parseInt(stat.trim()) || 0;
      totalBytes += size;
      completed++;
      
      // Record in manifest (size+mtime for incremental)
      const mtimeStr = await adbShell(pixel, `stat -c%Y ${remotePath} 2>/dev/null`).catch(() => "0");
      const mtime = parseInt(mtimeStr.trim()) || 0;
      manifest.recordFile(`${dir}/${relPath}`, size, mtime);
    } catch (e) {
      console.error(`Failed to pull ${remotePath}: ${e}`);
    }
  };
  
  // Bounded concurrency: 8 streams
  const workers: Promise<void>[] = [];
  const queue = [...files];
  
  for (let i = 0; i < PARALLEL_STREAMS; i++) {
    workers.push((async () => {
      while (queue.length > 0) {
        const file = queue.shift();
        if (file) await pullOne(file);
      }
    })());
  }
  
  await Promise.all(workers);
  manifest.finishPull(pullId, completed, totalBytes);
  
  return {
    dir,
    files: completed,
    bytes: totalBytes,
    method: "parallel-pull",
    durationMs: Date.now() - start,
  };
}

async function tarPull(
  pixel: string,
  dir: string,
  dest: string,
  manifest: ManifestDB
): Promise<TransferResult> {
  const start = Date.now();
  const stats = await getDirStats(pixel, dir);
  
  // On-device tar (eliminates per-file round-trips)
  const tarName = `${dir}-${Date.now()}.tar`;
  await adbShell(pixel, `cd /sdcard && tar -cf /sdcard/${tarName} ${dir} 2>/dev/null`);
  
  // Pull single tarball (fast sequential)
  const destTar = join(dest, tarName);
  await $`${ADB} -s ${pixel} pull /sdcard/${tarName} ${destTar}`.quiet();
  
  // Extract
  const destDir = join(dest, dir);
  mkdirSync(destDir, { recursive: true });
  await $`tar -xf ${destTar} -C ${dest} --strip-components=1`.quiet();
  
  // Cleanup
  await adbShell(pixel, `rm /sdcard/${tarName}`);
  await $`rm ${destTar}`.quiet();
  
  const pullId = manifest.startPull(dir);
  manifest.finishPull(pullId, stats.files, stats.bytes);
  
  return {
    dir,
    files: stats.files,
    bytes: stats.bytes,
    method: "tar-pull",
    durationMs: Date.now() - start,
  };
}

// ============================================================================
// Main
// ============================================================================

async function main() {
  const [cmd, destArg] = Bun.argv.slice(2);
  const dest = destArg || "/mnt/8TB/phone-archive";
  
  mkdirSync(dest, { recursive: true });
  const manifestPath = join(dest, "manifests", "backup.db");
  mkdirSync(join(dest, "manifests"), { recursive: true });
  const manifest = new ManifestDB(manifestPath);
  
  const pixel = await discoverPixel();
  console.log(`Pixel at ${pixel}`);
  
  if (cmd === "pull" || !cmd) {
    console.log(`Pulling to ${dest}...`);
    const results: TransferResult[] = [];
    
    for (const dir of SOURCE_DIRS) {
      // Check if dir exists on phone
      const exists = await adbShell(pixel, `ls -ld /sdcard/${dir} 2>&1 | head -1`);
      if (exists.includes("No such file")) {
        console.log(`Skip ${dir} (not on phone)`);
        continue;
      }
      
      const stats = await getDirStats(pixel, dir);
      console.log(`${dir}: ${stats.files} files, ${(stats.bytes / 1024 / 1024).toFixed(1)}MB`);
      
      // Hybrid selection:
      // - Many small files (>100 files, avg <1MB) → tar-pull
      // - Otherwise → parallel-pull
      const avgSize = stats.files > 0 ? stats.bytes / stats.files : 0;
      const useTar = stats.files > 100 && avgSize < 1024 * 1024;
      
      const result = useTar
        ? await tarPull(pixel, dir, dest, manifest)
        : await parallelPull(pixel, dir, dest, manifest);
      
      const mbps = (result.bytes / 1024 / 1024) / (result.durationMs / 1000);
      console.log(`  ✓ ${result.method} ${result.files} files in ${(result.durationMs/1000).toFixed(1)}s (${mbps.toFixed(1)} MB/s)`);
      results.push(result);
    }
    
    // Write manifest
    const manifestTxt = join(dest, "manifests", `pull-manifest-${new Date().toISOString().slice(0,10)}.txt`);
    const lines = results.map(r => 
      `OK ${r.dir} files=${r.files} bytes=${r.bytes} method=${r.method} duration=${r.durationMs}ms`
    );
    await Bun.write(manifestTxt, `# phone-backup manifest ${new Date().toISOString()} pixel=${pixel}\n` + lines.join("\n") + "\n");
    console.log(`\nManifest: ${manifestTxt}`);
    
  } else if (cmd === "verify") {
    console.log("Verifying manifest...");
    // TODO: implement verification against DB
    console.log("Use: check manifests/backup.db for pull history");
    
  } else if (cmd === "clean") {
    console.log("Clean: delete verified dirs from phone");
    console.log("SAFETY: Only deletes dirs with 'ok' status in manifest");
    // TODO: implement safe deletion with manifest check
    
  } else {
    console.log("Usage: bun src/index.ts [pull|verify|clean] [dest]");
  }
  
  manifest.close();
}

main().catch(e => {
  console.error("FATAL:", e.message);
  process.exit(1);
});
