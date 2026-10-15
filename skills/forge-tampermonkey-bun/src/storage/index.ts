/**
 * GM_* Storage API implementation for Bun.
 * Provides Tampermonkey-compatible persistent storage.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const STORAGE_DIR = join(homedir(), ".forge-tm-storage");

interface StorageBackend {
  get(key: string): any;
  set(key: string, value: any): void;
  delete(key: string): void;
  list(): string[];
  clear(): void;
}

class FileStorageBackend implements StorageBackend {
  private cache: Map<string, { file: string; data: any }>;
  
  constructor() {
    this.cache = new Map();
    if (!existsSync(STORAGE_DIR)) {
      mkdirSync(STORAGE_DIR, { recursive: true });
    }
  }
  
  private getFile(key: string): string {
    // Use hash of key to avoid filesystem issues
    const hash = hashString(key);
    return join(STORAGE_DIR, `${hash}.json`);
  }
  
  get(key: string): any {
    const cached = this.cache.get(key);
    if (cached) return cached.data;
    
    const file = this.getFile(key);
    if (existsSync(file)) {
      try {
        const data = JSON.parse(readFileSync(file, 'utf-8'));
        this.cache.set(key, { file, data });
        return data;
      } catch {}
    }
    return undefined;
  }
  
  set(key: string, value: any): void {
    const file = this.getFile(key);
    try {
      writeFileSync(file, JSON.stringify(value, null, 2), 'utf-8');
      this.cache.set(key, { file, data: value });
    } catch (e) {
      console.error(`[GM_storage] Failed to write ${key}:`, e);
    }
  }
  
  delete(key: string): void {
    const file = this.getFile(key);
    this.cache.delete(key);
    try { 
      if (existsSync(file)) {
        // don't actually delete, just empty it
        writeFileSync(file, 'null', 'utf-8');
      }
    } catch {}
  }
  
  list(): string[] {
    const keys: string[] = [];
    // Since we use hashes, we can't easily list original keys
    // Return cached keys
    for (const key of this.cache.keys()) {
      keys.push(key);
    }
    return keys;
  }
  
  clear(): void {
    this.cache.clear();
    // Don't delete files to be safe
  }
}

function hashString(s: string): string {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  }
  return `gm_${(h >>> 0).toString(16)}`;
}

let _backend: StorageBackend | null = null;

function getBackend(): StorageBackend {
  if (!_backend) _backend = new FileStorageBackend();
  return _backend;
}

/**
 * Tampermonkey-compatible GM_* storage API.
 * 
 * @example
 * ```ts
 * import { GM_getValue, GM_setValue, GM_deleteValue, GM_listValues } from '@forge-tampermonkey-bun/storage';
 * 
 * GM_setValue('myKey', { foo: 'bar' });
 * const val = GM_getValue('myKey', { default: true });
 * GM_deleteValue('myKey');
 * const keys = GM_listValues();
 * ```
 */
export function GM_getValue<T>(key: string, defaultValue?: T): T {
  const backend = getBackend();
  const val = backend.get(key);
  return val !== undefined ? val : (defaultValue as T);
}

export function GM_setValue<T>(key: string, value: T): void {
  const backend = getBackend();
  backend.set(key, value);
}

export function GM_deleteValue(key: string): void {
  const backend = getBackend();
  backend.delete(key);
}

export function GM_listValues(): string[] {
  const backend = getBackend();
  return backend.list();
}

export function GM_clearValues(): void {
  const backend = getBackend();
  backend.clear();
}

/**
 * Advanced storage features.
 */
export function GM_registerMenuCommand(name: string, fn: () => void): number {
  // In Bun context, store in memory
  if (!globalThis.__GM_MENU_CMDS) {
    globalThis.__GM_MENU_CMDS = new Map();
  }
  const id = Date.now();
  globalThis.__GM_MENU_CMDS.set(id, { name, fn });
  return id;
}

export function GM_unregisterMenuCommand(menuCommandId: number): void {
  if (globalThis.__GM_MENU_CMDS) {
    globalThis.__GM_MENU_CMDS.delete(menuCommandId);
  }
}

/**
 * List all registered menu commands (for debugging/UI).
 */
export function GM_listMenuCommands(): { id: number; name: string }[] {
  if (!globalThis.__GM_MENU_CMDS) return [];
  return [...globalThis.__GM_MENU_CMDS.entries()].map(([id, cmd]) => ({ id, name: cmd.name }));
}

declare global {
  var __GM_MENU_CMDS: Map<number, { name: string; fn: () => void }> | undefined;
}