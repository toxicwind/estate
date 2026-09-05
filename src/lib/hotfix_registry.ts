// ============================================================================
// SOVEREIGN — Hotfix Resolution Engine (Live, Persistent, Non-Monkey-Patch)
// Pattern: Registry + Persistent Store + Live File Reload
// "Don't patch the object. Patch the resolution."
// ============================================================================

import fs from "node:fs";
import path from "node:path";
import { EventEmitter } from "node:events";

export interface PatchMetadata {
  target: string;
  version?: string;
  author?: string;
  reason?: string;
  enabled?: boolean;
  timestamp?: string;
}

export interface PatchModule<T = unknown> {
  TARGET: string;
  VERSION?: string;
  AUTHOR?: string;
  REASON?: string;
  ENABLED?: boolean;
  filePath: string;
  impl: T;
}

export class HotfixRegistry extends EventEmitter {
  private readonly patchDir: string;
  private readonly overrides = new Map<string, PatchModule>();
  private watcher: fs.FSWatcher | null = null;
  private isLoaded = false;

  constructor(patchDir?: string) {
    super();
    this.patchDir = patchDir ?? path.resolve(__dirname, "../../patches");
    if (!fs.existsSync(this.patchDir)) {
      fs.mkdirSync(this.patchDir, { recursive: true });
    }
  }

  /**
   * Resolve an implementation at runtime.
   * Core code calls this instead of hardcoding or monkey-patching:
   * const service = hotfixRegistry.resolve("service.tau", defaultService);
   */
  public resolve<T>(targetPath: string, defaultImpl: T): T {
    if (!this.isLoaded) {
      this.loadAllSync();
    }
    const patch = this.overrides.get(targetPath);
    if (patch && patch.ENABLED !== false) {
      return patch.impl as T;
    }
    return defaultImpl;
  }

  /**
   * Persist a hotfix permanently to disk. Survives all restarts.
   */
  public async persistPatch(targetPath: string, sourceCode: string, meta?: PatchMetadata): Promise<string> {
    if (!fs.existsSync(this.patchDir)) {
      fs.mkdirSync(this.patchDir, { recursive: true });
    }
    const sanitizedName = targetPath.replace(/[^a-zA-Z0-9_.-]/g, "_");
    const filePath = path.join(this.patchDir, `${sanitizedName}.ts`);

    let code = sourceCode;
    if (!code.includes("export const TARGET")) {
      const header = `// Live Hotfix: ${targetPath}\n` +
        `// Author: ${meta?.author ?? "sovereign"}\n` +
        `// Reason: ${meta?.reason ?? "live resolution hotfix"}\n` +
        `// Date: ${meta?.timestamp ?? new Date().toISOString()}\n\n` +
        `export const TARGET = "${targetPath}";\n` +
        `export const VERSION = "${meta?.version ?? "1.0.0"}";\n` +
        `export const ENABLED = ${meta?.enabled !== false};\n\n`;
      code = header + code;
    }

    await fs.promises.writeFile(filePath, code, "utf-8");
    await this.loadPatch(filePath);
    this.emit("patch:persisted", { target: targetPath, file: filePath });
    return filePath;
  }

  /**
   * Load a single patch file dynamically into memory.
   */
  public async loadPatch(filePath: string): Promise<boolean> {
    try {
      // Dynamic import exception: loading user hotfix modules selected from disk at runtime
      const url = `${path.resolve(filePath)}?t=${Date.now()}`;
      const mod = await import(url);

      const target = mod.TARGET || mod.default?.TARGET;
      const impl = mod.impl ?? mod.default?.impl ?? mod.default;

      if (!target || impl === undefined) {
        console.warn(`[hotfix] Skipping ${filePath}: missing TARGET or impl export`);
        return false;
      }

      const patchMod: PatchModule = {
        TARGET: target,
        VERSION: mod.VERSION ?? "1.0.0",
        AUTHOR: mod.AUTHOR ?? "sovereign",
        REASON: mod.REASON ?? "",
        ENABLED: mod.ENABLED !== false,
        filePath,
        impl,
      };

      this.overrides.set(target, patchMod);
      this.emit("patch:loaded", { target, version: patchMod.VERSION });
      return true;
    } catch (err) {
      console.error(`[hotfix] Failed to load patch from ${filePath}:`, err);
      return false;
    }
  }

  /**
   * Load all patch files from disk on boot.
   */
  public async loadAll(): Promise<void> {
    if (!fs.existsSync(this.patchDir)) {
      fs.mkdirSync(this.patchDir, { recursive: true });
    }
    this.overrides.clear();
    const files = await fs.promises.readdir(this.patchDir);
    const patchFiles = files.filter(f => (f.endsWith(".ts") || f.endsWith(".js")) && !f.endsWith(".disabled"));

    for (const file of patchFiles) {
      await this.loadPatch(path.join(this.patchDir, file));
    }
    this.isLoaded = true;
    this.emit("loaded", { count: this.overrides.size });
  }

  /**
   * Synchronous load on first access if not yet async-loaded.
   */
  public loadAllSync(): void {
    if (!fs.existsSync(this.patchDir)) {
      fs.mkdirSync(this.patchDir, { recursive: true });
    }
    this.overrides.clear();
    try {
      const files = fs.readdirSync(this.patchDir);
      const patchFiles = files.filter(f => (f.endsWith(".ts") || f.endsWith(".js")) && !f.endsWith(".disabled"));
      for (const file of patchFiles) {
        const fullPath = path.join(this.patchDir, file);
        try {
          const mod = require(fullPath);
          const target = mod.TARGET || mod.default?.TARGET;
          const impl = mod.impl ?? mod.default?.impl ?? mod.default;
          if (target && impl !== undefined) {
            this.overrides.set(target, {
              TARGET: target,
              VERSION: mod.VERSION ?? "1.0.0",
              AUTHOR: mod.AUTHOR ?? "sovereign",
              REASON: mod.REASON ?? "",
              ENABLED: mod.ENABLED !== false,
              impl,
            });
          }
        } catch {
          // Dynamic async reload will capture on file change
        }
      }
    } catch (e) {
      console.error("[hotfix] Synchronous directory read error:", e);
    }
    this.isLoaded = true;
  }

  /**
   * Start watching the patch directory for live updates without restarting.
   */
  public startWatcher(): fs.FSWatcher {
    if (this.watcher) return this.watcher;
    if (!fs.existsSync(this.patchDir)) {
      fs.mkdirSync(this.patchDir, { recursive: true });
    }

    this.watcher = fs.watch(this.patchDir, { recursive: false }, async (_eventType, filename) => {
      if (!filename || (!filename.endsWith(".ts") && !filename.endsWith(".js"))) return;
      const fullPath = path.join(this.patchDir, filename);
      if (fs.existsSync(fullPath)) {
        await this.loadPatch(fullPath);
      } else {
        const base = filename.replace(/\.(ts|js|disabled)$/, "");
        for (const [key] of this.overrides.entries()) {
          const sanitized = key.replace(/[^a-zA-Z0-9_.-]/g, "_");
          if (sanitized === base) {
            this.overrides.delete(key);
            this.emit("patch:removed", { target: key });
            break;
          }
        }
      }
    });
    if (typeof this.watcher.unref === "function") {
      this.watcher.unref();
    }

    return this.watcher;
  }

  /**
   * Instant rollback / disable of a patch.
   */
  public disablePatch(targetPath: string): boolean {
    const patch = this.overrides.get(targetPath);
    if (!patch) return false;
    patch.ENABLED = false;
    if (fs.existsSync(patch.filePath)) {
      fs.renameSync(patch.filePath, `${patch.filePath}.disabled`);
    }
    this.emit("patch:disabled", { target: targetPath });
    return true;
  }

  /**
   * Re-enable a previously disabled patch.
   */
  public async enablePatch(targetPath: string): Promise<boolean> {
    const candidates = [
      targetPath.replace(/[^a-zA-Z0-9_-]/g, "_"),
      targetPath.replace(/[^a-zA-Z0-9_.-]/g, "_"),
    ];
    for (const sanitized of candidates) {
      for (const ext of [".ts", ".js"]) {
        const disabledPath = path.join(this.patchDir, `${sanitized}${ext}.disabled`);
        const targetFilePath = path.join(this.patchDir, `${sanitized}${ext}`);
        if (fs.existsSync(disabledPath)) {
          fs.renameSync(disabledPath, targetFilePath);
          await this.loadPatch(targetFilePath);
          this.emit("patch:enabled", { target: targetPath });
          return true;
        }
      }
    }
    const patch = this.overrides.get(targetPath);
    if (patch) {
      patch.ENABLED = true;
      return true;
    }
    return false;
  }

  /**
   * Get all registered patches (both active and disabled).
   */
  public listPatches(): Array<PatchMetadata & { hasOverride: boolean }> {
    const results: Array<PatchMetadata & { hasOverride: boolean }> = [];
    for (const [target, p] of this.overrides.entries()) {
      results.push({
        target,
        version: p.VERSION,
        author: p.AUTHOR,
        reason: p.REASON,
        enabled: p.ENABLED !== false,
        hasOverride: true,
      });
    }

    // Also scan for .disabled files on disk
    if (fs.existsSync(this.patchDir)) {
      const files = fs.readdirSync(this.patchDir);
      for (const file of files) {
        if (file.endsWith(".disabled")) {
          const baseName = file.replace(/\.(ts|js)\.disabled$/, "");
          const target = baseName.replace(/_/g, ".");
          if (!results.some(r => r.target === target || r.target.replace(/[^a-zA-Z0-9_-]/g, "_") === baseName)) {
            results.push({
              target,
              version: "1.0.0",
              author: "sovereign",
              reason: "Disabled hotfix on disk",
              enabled: false,
              hasOverride: false,
            });
          }
        }
      }
    }
    return results;
  }
}

// Global Singleton Instance
export const hotfixRegistry = new HotfixRegistry();
hotfixRegistry.startWatcher();
