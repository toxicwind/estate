/**
 * Stage 1: Parse musescope JSON file and extract meaningful sections.
 * Returns structured data ready for parquet conversion.
 */

import { readFileSync } from "node:fs";
import { existsSync } from "node:fs";
import { join } from "node:path";

export interface MusescopeData {
  brand: Record<string, any>;
  generated: string;
  join: Record<string, any>;
  hatch: Record<string, any>;
  crypto: Record<string, any>;
  // Optional sections that might be populated
  entries?: any[];
  decrypted?: any[];
}

export async function parseMusescopeJson(config: Record<string, any>): Promise<MusescopeData> {
  const inputPath = config.inputPath || "/home/toxic/Downloads/musescope-1791619413821.json";
  
  if (!existsSync(inputPath)) {
    throw new Error(`Input file not found: ${inputPath}`);
  }
  
  console.log(`📖 Parsing musescope JSON: ${inputPath}`);
  
  try {
    const raw = readFileSync(inputPath, "utf-8");
    const data = JSON.parse(raw);
    
    // Validate required sections
    if (!data.brand || !data.generated || !data.join) {
      throw new Error("Missing required sections in musescope JSON");
    }
    
    // Extract and structure the data for downstream processing
    const result: MusescopeData = {
      brand: data.brand,
      generated: data.generated,
      join: data.join,
      hatch: data.hatch || {},
      crypto: data.crypto || {},
      entries: data.entries || [],
      decrypted: data.decrypted || []
    };
    
    console.log(`✅ Parsed JSON: ${Object.keys(result).length} top-level sections`);
    return result;
  } catch (err) {
    throw new Error(`Failed to parse musescope JSON: ${err.message}`);
  }
}