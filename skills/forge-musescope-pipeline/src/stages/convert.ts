/**
 * Stage 2: Convert parsed musescope data to parquet files.
 * Each section becomes its own parquet table for efficient querying.
 */

import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { MusescopeData } from "./parse.js";

// Use Bun's native Python bridge via pyarrow if available
// Fallback to manual parquet row group construction

interface ParquetTable {
  name: string;
  columns: string[];
  rows: any[];
  dtype: Record<string, string>;
}

export async function convertToParquet(data: MusescopeData, config: Record<string, any>): Promise<string[]> {
  const outputDir = config.outputDir || "/home/toxic/musescope_parquet";
  
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }
  
  console.log(`🔧 Converting to parquet: ${outputDir}`);
  
  // Build tables for each section
  const tables: ParquetTable[] = [];
  
  // Brand table (single row)
  tables.push({
    name: "brand",
    columns: Object.keys(data.brand),
    rows: [data.brand],
    dtype: inferDtypes(data.brand)
  });
  
  // Generated table (single row)
  tables.push({
    name: "generated",
    columns: ["timestamp"],
    rows: [{ timestamp: data.generated }],
    dtype: { timestamp: "utf8" }
  });
  
  // Join table (flat, single row)
  const joinFlat = flattenJoin(data.join);
  tables.push({
    name: "join",
    columns: Object.keys(joinFlat),
    rows: [joinFlat],
    dtype: inferDtypes(joinFlat)
  });
  
  // Crypto operations table (single row of counts)
  tables.push({
    name: "crypto_ops",
    columns: Object.keys(data.crypto),
    rows: [data.crypto],
    dtype: inferDtypes(data.crypto)
  });
  
  // Hatch metadata (frames count, cipherReady boolean)
  const hatchMeta = {
    frames: data.hatch.frames,
    cipherReady: data.hatch.cipherReady
  };
  tables.push({
    name: "hatch_meta",
    columns: Object.keys(hatchMeta),
    rows: [hatchMeta],
    dtype: inferDtypes(hatchMeta)
  });
  
  // Hatch handshake messages (as byte arrays)
  const handshakeMessages: any[] = [];
  const handshake = data.hatch.handshake || {};
  for (const [msgName, msgData] of Object.entries(handshake)) {
    if (typeof msgData === 'object' && !Array.isArray(msgData) && msgName.startsWith('msg')) {
      const bytes = Object.entries(msgData as Record<string, number>)
        .sort(([a], [b]) => parseInt(a) - parseInt(b))
        .map(([_, val]) => val);
      handshakeMessages.push({
        message: msgName,
        byte_count: bytes.length,
        bytes: JSON.stringify(bytes), // Store as JSON array string
        hex: bytes.map(b => b.toString(16).padStart(2, '0')).join(''),
        min_byte: min(bytes),
        max_byte: max(bytes),
        avg_byte: avg(bytes)
      });
    } else if (typeof msgData === 'string') {
      handshakeMessages.push({
        message: msgName,
        byte_count: msgData.length / 2,
        bytes: "",
        hex: msgData,
        min_byte: 0,
        max_byte: 0,
        avg_byte: 0
      });
    }
  }
  if (handshakeMessages.length > 0) {
    tables.push({
      name: "hatch_handshake",
      columns: Object.keys(handshakeMessages[0]),
      rows: handshakeMessages,
      dtype: inferDtypes(handshakeMessages[0])
    });
  }
  
  // Hatch noise state (list of 5 objects with h, ck, k, n, re)
  const noiseStates = data.hatch.noise;
  if (Array.isArray(noiseStates) && noiseStates.length > 0) {
    const noiseRows: any[] = [];
    for (let i = 0; i < noiseStates.length; i++) {
      const state = noiseStates[i];
      const row: any = { noise_index: i };
      for (const field of ['h', 'ck', 'k', 'n', 're']) {
        if (state[field] && typeof state[field] === 'object') {
          const bytes = Object.entries(state[field] as Record<string, number>)
            .sort(([a], [b]) => parseInt(a) - parseInt(b))
            .map(([_, val]) => val);
          row[`${field}_array`] = JSON.stringify(bytes);
          row[`${field}_len`] = bytes.length;
          row[`${field}_hex`] = bytes.map(b => b.toString(16).padStart(2, '0')).join('');
          if (bytes.length > 0) {
            row[`${field}_min`] = min(bytes);
            row[`${field}_max`] = max(bytes);
            row[`${field}_avg`] = avg(bytes);
            row[`${field}_sum`] = sum(bytes);
            row[`${field}_zero_count`] = bytes.filter(b => b === 0).length;
          }
        }
      }
      noiseRows.push(row);
    }
    tables.push({
      name: "hatch_noise",
      columns: Object.keys(noiseRows[0]),
      rows: noiseRows,
      dtype: inferDtypes(noiseRows[0])
    });
  }
  
  // Indicators table (extracted from all strings)
  const indicators = extractIndicators(data);
  tables.push({
    name: "indicators",
    columns: Object.keys(indicators[0]),
    rows: indicators,
    dtype: inferDtypes(indicators[0])
  });
  
  // Write each table as a parquet file
  // Use pyarrow via Bun's Python bridge, or fall back to writing as JSON+binary
  const writtenFiles: string[] = [];
  
  for (const table of tables) {
    const outputPath = join(outputDir, `${table.name}.parquet`);
    
    try {
      // Try using pyarrow (Python integration)
      await writeParquetViaPyarrow(table.rows, table.columns, outputPath, config);
      writtenFiles.push(outputPath);
    } catch (pyErr) {
      // Fallback: write as parquet using duckdb or manual binary format
      try {
        await writeParquetViaDuckdb(table.rows, table.name, outputPath, config);
        writtenFiles.push(outputPath);
      } catch (duckErr) {
        // Ultimate fallback: write as CSV (still useful for analysis)
        const csvPath = outputPath.replace('.parquet', '.csv');
        await writeAsCSV(table.rows, table.columns, csvPath);
        writtenFiles.push(csvPath);
        console.warn(`⚠️  Parque write failed, fell back to CSV: ${csvPath}`);
      }
    }
    
    console.log(`  ✓ ${table.name}.parquet (${table.rows.length} rows, ${table.columns.length} cols)`);
  }
  
  return writtenFiles;
}

function flattenJoin(join: Record<string, any>): Record<string, any> {
  const flat: Record<string, any> = {};
  for (const [k, v] of Object.entries(join)) {
    if (k === 'notary' && typeof v === 'object') {
      for (const [nk, nv] of Object.entries(v)) {
        if (nk === 'restrictions' && typeof nv === 'object') {
          for (const [rk, rv] of Object.entries(nv)) {
            flat[`notary_restrictions_${rk}`] = rv;
          }
        } else if (nk === 'public_key' && typeof nv === 'object') {
          for (const [pk, pv] of Object.entries(nv)) {
            flat[`notary_public_key_${pk}`] = pv;
          }
        } else {
          flat[`notary_${nk}`] = nv;
        }
      }
    } else {
      flat[k] = v;
    }
  }
  return flat;
}

function extractIndicators(data: MusescopeData): any[] {
  const indicators: any[] = [];
  
  // Hostname
  const hostname = data.join.notary?.restrictions?.hostname;
  if (hostname) {
    indicators.push({
      type: "hostname",
      value: hostname,
      source: "join.notary.restrictions.hostname"
    });
  }
  
  // UUIDs
  const vmId = data.join.vm_id;
  if (vmId) {
    indicators.push({ type: "uuid", value: vmId, source: "join.vm_id" });
  }
  
  const requestId = data.join.request_id;
  if (requestId) {
    indicators.push({ type: "uuid", value: requestId, source: "join.request_id" });
  }
  
  // Base64 key
  const pubKey = data.join.notary?.public_key?.key;
  if (pubKey) {
    indicators.push({ type: "public_key", value: pubKey, source: "join.notary.public_key.key" });
  }
  
  // Timeout
  const timeout = data.join.notary?.restrictions?.timeout;
  if (timeout) {
    indicators.push({ type: "timeout", value: timeout, source: "join.notary.restrictions.timeout" });
  }
  
  // Auth prefix
  const auth = data.join.auth;
  if (auth) {
    indicators.push({ type: "auth", value: auth, source: "join.auth" });
  }
  
  // Crypto operations counts
  for (const [op, count] of Object.entries(data.crypto)) {
    indicators.push({ type: "crypto_op", value: op, count: count, source: "crypto" });
  }
  
  // Frames and cipher
  if (typeof data.hatch.frames === 'number') {
    indicators.push({ type: "frames_count", value: data.hatch.frames, source: "hatch.frames" });
  }
  if (typeof data.hatch.cipherReady === 'boolean') {
    indicators.push({ type: "cipher_ready", value: data.hatch.cipherReady, source: "hatch.cipherReady" });
  }
  
  return indicators;
}

function inferDtypes(row: Record<string, any>): Record<string, string> {
  const dtypes: Record<string, string> = {};
  for (const [k, v] of Object.entries(row)) {
    if (typeof v === 'boolean') dtypes[k] = 'bool';
    else if (typeof v === 'number') dtypes[k] = Number.isInteger(v) ? 'int64' : 'double';
    else dtypes[k] = 'utf8';
  }
  return dtypes;
}

function min(arr: number[]): number { return Math.min(...arr); }
function max(arr: number[]): number { return Math.max(...arr); }
function avg(arr: number[]): number { return arr.reduce((a, b) => a + b, 0) / arr.length; }
function sum(arr: number[]): number { return arr.reduce((a, b) => a + b, 0); }

async function writeParquetViaPyarrow(rows: any[], columns: string[], outputPath: string, config: Record<string, any>): Promise<void> {
  // Use Bun's child_process to call python3 with pyarrow
  const { spawn } = require("node:child_process");
  
  return new Promise((resolve, reject) => {
    const script = `
import json, sys
import pyarrow as pa
import pyarrow.parquet as pq

rows = json.loads(sys.argv[1])
columns = json.loads(sys.argv[2])
output = sys.argv[3]
compression = sys.argv[4] if len(sys.argv) > 4 else "snappy"

table = pa.table({col: [r.get(col) for r in rows] for col in columns})
pq.write_table(table, output, compression=compression)
print(f"Written {table.num_rows} rows to {output}")
`;
    
    const child = spawn("python3", ["-c", script, JSON.stringify(rows), JSON.stringify(columns), outputPath, config.compression], {
      stdio: ["pipe", "pipe", "pipe"]
    });
    
    let stderr = "";
    child.stderr.on("data", (data: Buffer) => { stderr += data.toString(); });
    
    child.on("close", (code: number) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`pyarrow failed (code ${code}): ${stderr}`));
      }
    });
    
    child.on("error", (err: Error) => {
      reject(err);
    });
  });
}

async function writeParquetViaDuckdb(rows: any[], tableName: string, outputPath: string, config: Record<string, any>): Promise<void> {
  const { spawn } = require("node:child_process");
  
  return new Promise((resolve, reject) => {
    // Write temp CSV first, then convert with duckdb
    const tempCsv = outputPath.replace(".parquet", ".tmp.csv");
    const csvContent = [
      rows.map(r => Object.keys(r)).join(","),
      ...rows.map(r => Object.values(r).map(v => 
        typeof v === 'string' ? `"${v.replace(/"/g, '""')}"` : v
      ).join(","))
    ].join("\n");
    
    const fs = require("node:fs");
    fs.writeFileSync(tempCsv, csvContent);
    
    const script = `
INSTALL parquet;
LOAD parquet;
COPY (SELECT * FROM read_csv_auto('${tempCsv}')) TO '${outputPath}' (FORMAT PARQUET, COMPRESSION ${config.compression || "snappy"});
`;
    
    const child = spawn("duckdb", ["-c", script], {
      stdio: ["pipe", "pipe", "pipe"]
    });
    
    let stderr = "";
    child.stderr.on("data", (data: Buffer) => { stderr += data.toString(); });
    
    child.on("close", (code: number) => {
      fs.unlinkSync(tempCsv);
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`duckdb failed (code ${code}): ${stderr}`));
      }
    });
    
    child.on("error", (err: Error) => {
      try { fs.unlinkSync(tempCsv); } catch {}
      reject(err);
    });
  });
}

async function writeAsCSV(rows: any[], columns: string[], csvPath: string): Promise<void> {
  const fs = require("node:fs");
  const lines: string[] = [];
  // Header
  lines.push(columns.join(","));
  // Rows
  for (const row of rows) {
    const values = columns.map(col => {
      const v = row[col];
      if (v === null || v === undefined) return "";
      if (typeof v === 'object') return `"${JSON.stringify(v).replace(/"/g, '""')}"`;
      if (typeof v === 'string') return `"${v.replace(/"/g, '""')}"`;
      return String(v);
    });
    lines.push(values.join(","));
  }
  fs.writeFileSync(csvPath, lines.join("\n") + "\n");
}
