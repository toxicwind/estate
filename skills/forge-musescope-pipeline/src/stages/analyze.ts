/**
 * Stage 4: Analysis of parquet data - SQL queries, aggregations, pattern detection.
 */

import { config } from "../config.js";
import { spawn } from "node:child_process";

export interface AnalysisResult {
  query: string;
  results: any[];
  latencyMs: number;
  rowCount: number;
}

export async function runAnalysis(
  parquetFiles: string[],
  config: Record<string, any>
): Promise<AnalysisResult[]> {
  const outputDir = config.outputDir || "/home/toxic/musescope_parquet";
  const results: AnalysisResult[] = [];
  
  console.log(`🔍 Running analysis on parquet files...`);
  
  // Define analytical queries
  const queries = [
    {
      name: "all_tables",
      sql: `SELECT table_name, 
              (SELECT COUNT(*) FROM read_parquet('${outputDir}/' || table_name || '.parquet')) as row_count
           FROM (VALUES 
             ('brand'), ('generated'), ('join'), ('hatch_meta'), ('crypto_ops'),
             ('hatch_handshake'), ('hatch_noise'), ('indicators')
           ) AS t(table_name)`
    },
    {
      name: "brand_info",
      sql: `SELECT * FROM read_parquet('${outputDir}/brand.parquet')`
    },
    {
      name: "join_vm_info",
      sql: `SELECT vm_id, notary_identity, notary_restrictions_hostname, notary_restrictions_timeout
            FROM read_parquet('${outputDir}/join.parquet')`
    },
    {
      name: "hatch_handshake_analysis",
      sql: `SELECT message, byte_count, min_byte, max_byte, avg_byte
            FROM read_parquet('${outputDir}/hatch_handshake.parquet')`
    },
    {
      name: "noise_state_analysis",
      sql: `SELECT noise_index, h_len, ck_len, k_len, n_len, re_len,
            h_avg, ck_avg, k_avg, n_avg, re_avg
            FROM read_parquet('${outputDir}/hatch_noise.parquet')`
    },
    {
      name: "indicators_summary",
      sql: `SELECT type, value, source FROM read_parquet('${outputDir}/indicators.parquet')`
    },
    {
      name: "crypto_operations",
      sql: `SELECT * FROM read_parquet('${outputDir}/crypto_ops.parquet')`
    }
  ];
  
  // Check if duckdb is available
  const duckdbAvailable = await checkDuckDB();
  if (!duckdbAvailable) {
    console.warn("⚠️  duckdb not available, skipping SQL analysis");
    return results;
  }
  
  for (const q of queries) {
    try {
      const start = Date.now();
      const rows = await runDuckDBQuery(q.sql);
      results.push({
        query: q.name,
        results: rows,
        latencyMs: Date.now() - start,
        rowCount: rows.length
      });
      console.log(`  ✓ ${q.name}: ${rows.length} rows (${Date.now() - start}ms)`);
    } catch (err) {
      console.warn(`  ✗ ${q.name} failed: ${err.message}`);
      results.push({
        query: q.name,
        results: [],
        latencyMs: 0,
        rowCount: 0
      });
    }
  }
  
  return results;
}

async function checkDuckDB(): Promise<boolean> {
  return new Promise((resolve) => {
    const child = spawn("duckdb", ["--version"], { stdio: "ignore" });
    child.on("close", (code) => resolve(code === 0));
    child.on("error", () => resolve(false));
  });
}

async function runDuckDBQuery(sql: string): Promise<any[]> {
  return new Promise((resolve, reject) => {
    const child = spawn("duckdb", ["-noheader", "-json", "-c", sql], {
      stdio: ["ignore", "pipe", "pipe"]
    });
    
    let stdout = "";
    let stderr = "";
    
    child.stdout?.on("data", (data) => { stdout += data.toString(); });
    child.stderr?.on("data", (data) => { stderr += data.toString(); });
    
    child.on("close", (code) => {
      if (code === 0) {
        try {
          // duckdb -json outputs JSON lines
          const lines = stdout.trim().split('\n').filter(Boolean);
          const rows = lines.map(l => JSON.parse(l));
          resolve(rows);
        } catch (e) {
          resolve([]);
        }
      } else {
        reject(new Error(`duckdb failed (${code}): ${stderr}`));
      }
    });
    
    child.on("error", (err) => reject(err));
  });
}