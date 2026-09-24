export interface CapabilityEntry {
  name: string;
  kind: "export" | "hook" | "tool" | "provider" | "config";
  provider: string;
  aliases?: string[];
  synthesize?: string;
}

export interface CapabilityManifest {
  schemaVersion: string;
  generatedAt: string;
  entries: CapabilityEntry[];
}
