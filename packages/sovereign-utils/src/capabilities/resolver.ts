import { readFile } from "node:fs/promises";
import type { CapabilityEntry, CapabilityManifest } from "./manifest";

let activeManifest: CapabilityManifest | null = null;

export async function loadManifest(manifestPath: string): Promise<CapabilityManifest> {
  const content = await readFile(manifestPath, "utf-8");
  activeManifest = JSON.parse(content) as CapabilityManifest;
  return activeManifest;
}

export function setManifest(manifest: CapabilityManifest): void {
  activeManifest = manifest;
}

export function resolveCapability(name: string): string | null {
  if (!activeManifest) {
    throw new Error("Manifest not loaded. Call loadManifest or setManifest first.");
  }
  const entry = activeManifest.entries.find((e) => e.name === name || e.aliases?.includes(name));
  return entry ? entry.provider : null;
}

export function getAllCapabilities(): CapabilityEntry[] {
  if (!activeManifest) {
    throw new Error("Manifest not loaded. Call loadManifest or setManifest first.");
  }
  return [...activeManifest.entries];
}

export function getSynthesisHint(name: string): string | undefined {
  if (!activeManifest) {
    throw new Error("Manifest not loaded. Call loadManifest or setManifest first.");
  }
  const entry = activeManifest.entries.find((e) => e.name === name || e.aliases?.includes(name));
  return entry?.synthesize;
}
