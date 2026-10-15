/**
 * Tampermonkey-style GM_* config shim for Bun.
 * Provides a persistent config store that mirrors GM_setValue/GM_getValue
 * semantics, so pipeline stages can be configured at runtime like a userscript.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const CONFIG_DIR = join(homedir(), ".forgemscp");
const CONFIG_FILE = join(CONFIG_DIR, "config.json");

const DEFAULTS: Record<string, any> = {
  // musescope input
  inputPath: "/home/toxic/Downloads/musescope-1791619413821.json",
  outputDir: "/home/toxic/musescope_parquet",

  // parquet
  compression: "snappy",
  maxRowGroupSize: 1024,

  // ferret-den
  ferretDenPath: "/home/toxic/estate/ranch/ferret-den",
  pdToolsDir: "/home/toxic/.pdtm/go/bin",
  reconDomain: "",  // auto-extracted from musescope if left blank

  // analysis
  runRecon: true,
  runApiRecon: false,
  runNuclei: false,        // requires confirm: true at every call
  nucleiTemplates: "cve,fuzzing",

  // logging
  verbose: false,
  harCapture: true,
  logMax: 1500,
  logRatePerSec: 60,

  // pipeline
  parallelStages: true,
  deadlineSec: 30,
};

export interface Config extends Record<string, any> {}

export class GMConfig {
  private data: Record<string, any>;
  private dirty: Set<string>;

  constructor() {
    this.data = { ...DEFAULTS };
    this.dirty = new Set();
    this._load();
  }

  private _load() {
    try {
      if (existsSync(CONFIG_FILE)) {
        const raw = JSON.parse(readFileSync(CONFIG_FILE, "utf-8"));
        Object.assign(this.data, raw);
      } else {
        // First run: persist defaults
        this._flush();
      }
    } catch (e) {
      // corrupted — fall back to defaults
      console.error(`[GMConfig] load error: ${e}`);
    }
  }

  private _flush() {
    try {
      if (!existsSync(CONFIG_DIR)) mkdirSync(CONFIG_DIR, { recursive: true });
      writeFileSync(CONFIG_FILE, JSON.stringify(this.data, null, 2));
    } catch (e) {
      console.error(`[GMConfig] flush error: ${e}`);
    }
  }

  // Tampermonkey-compatible API
  getValue<T>(key: string, defaultValue?: T): T {
    return (this.data[key] ?? defaultValue) as T;
  }

  setValue<T>(key: string, value: T): void {
    this.data[key] = value;
    this.dirty.add(key);
    this._flush();
  }

  deleteValue(key: string): void {
    delete this.data[key];
    this._flush();
  }

  listValues(): string[] {
    return Object.keys(this.data);
  }

  // Bulk helpers
  getAll(): Record<string, any> {
    return { ...this.data };
  }

  reset(): void {
    this.data = { ...DEFAULTS };
    this.dirty.clear();
    this._flush();
  }

  // Tampermonkey-style menu command registry (in-process only, no UI in CLI)
  private _cmds: Map<string, () => void> = new Map();

  registerMenuCommand(name: string, fn: () => void): void {
    this._cmds.set(name, fn);
  }

  /** Run a registered command. */
  runCommand(name: string): boolean {
    const fn = this._cmds.get(name);
    if (fn) {
      fn();
      return true;
    }
    return false;
  }

  listCommands(): string[] {
    return [...this._cmds.keys()];
  }
}

export const config = new GMConfig();

// Tampermonkey-compatible exported functions for any module that wants them
export const GM_getValue = <T>(key: string, defaultValue?: T): T => config.getValue(key, defaultValue);
export const GM_setValue = <T>(key: string, value: T): void => config.setValue(key, value);
export const GM_deleteValue = (key: string): void => config.deleteValue(key);
export const GM_listValues = (): string[] => config.listValues();
export const GM_registerMenuCommand = (name: string, fn: () => void): void => config.registerMenuCommand(name, fn);

export function loadConfig(overrides?: Partial<Config>): Config {
  if (overrides) {
    for (const [k, v] of Object.entries(overrides)) {
      config.setValue(k, v);
    }
  }
  return config.getAll();
}
