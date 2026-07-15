#!/usr/bin/env bun
/**
 * lock.ts — advisory file lock for sovereign shared config files.
 *
 * Uses atomic mkdir(2) + PID file for cross-process locking.
 * Every agent that modifies config.yaml, opencode.json, or any shared
 * state MUST acquire a lock first.
 *
 * Usage:
 *   import { withLock } from "../lib/lock";
 *
 *   await withLock("config.yaml", async () => {
 *     // read, modify, write — guaranteed exclusive
 *   });
 */

import { mkdir, rmdir, writeFile, readFile } from "fs/promises";
import { join } from "path";
import { existsSync } from "fs";

const LOCK_DIR = "/tmp/sovereign-locks";

function lockPath(name: string): string {
  const safe = name.replace(/[^a-zA-Z0-9._-]/g, "_");
  return join(LOCK_DIR, safe + ".lock");
}

async function ensureLockDir(): Promise<void> {
  try { await mkdir(LOCK_DIR, { recursive: true }); } catch {}
}

/**
 * Try to acquire lock. Returns true if acquired, false if held by another.
 */
async function tryAcquire(lockDir: string, pid: number): Promise<boolean> {
  try {
    await mkdir(lockDir, { recursive: false });
    await writeFile(join(lockDir, "pid"), String(pid), "utf-8");
    return true;
  } catch {
    // Lock is held — check if owner is stale
    try {
      const pidFile = join(lockDir, "pid");
      if (existsSync(pidFile)) {
        const oldPid = parseInt(await readFile(pidFile, "utf-8"), 10);
        if (isNaN(oldPid)) return false;
        // Check if process exists
        try {
          process.kill(oldPid, 0); // signal 0 = test existence
          return false; // still alive
        } catch {
          // Stale — clean up and retry
          try { await rmdir(lockDir, { recursive: true }); } catch {}
          try {
            await mkdir(lockDir, { recursive: false });
            await writeFile(join(lockDir, "pid"), String(pid), "utf-8");
            return true;
          } catch {
            return false; // lost race
          }
        }
      }
    } catch {}
    return false;
  }
}

/**
 * Acquire an exclusive lock on `resourceName`.
 * Blocks (polls) until the lock is obtained.
 */
export async function acquireLock(
  resourceName: string,
  options?: { timeoutMs?: number; pollMs?: number }
): Promise<() => Promise<void>> {
  await ensureLockDir();
  const ldir = lockPath(resourceName);
  const pid = process.pid;
  const timeout = options?.timeoutMs ?? 60_000;
  const pollMs = options?.pollMs ?? 500;
  const deadline = Date.now() + timeout;

  while (Date.now() < deadline) {
    if (await tryAcquire(ldir, pid)) {
      return async () => {
        try { await rmdir(ldir, { recursive: true }); } catch {}
      };
    }
    await new Promise(r => setTimeout(r, pollMs));
  }

  throw new Error(`lock timeout ${timeout}ms: ${resourceName} (held by pid from ${ldir}/pid)`);
}

/**
 * Run `fn` while holding an exclusive lock on `resourceName`.
 */
export async function withLock<T>(
  resourceName: string,
  fn: () => Promise<T>,
  options?: { timeoutMs?: number; pollMs?: number }
): Promise<T> {
  const release = await acquireLock(resourceName, options);
  try {
    return await fn();
  } finally {
    await release();
  }
}
