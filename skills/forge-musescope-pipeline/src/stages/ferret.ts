/**
 * Stage 3: Ferret-den integration for reconnaissance analysis.
 * Extracts domains/IPs from parquet data and runs ferret-den tools.
 */

import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, basename } from "node:path";
import { spawn } from "node:child_process";

export interface FerretDenConfig {
  ferretDenPath: string;
  pdToolsDir: string;
  reconDomain: string;
}

export interface FerretDenResult {
  tool: string;
  ok: boolean;
  output: any;
  error?: string;
  latencyMs: number;
}

export async function runFerretDenRecon(
  parquetFiles: string[],
  config: Record<string, any>
): Promise<FerretDenResult[]> {
  const ferretConfig: FerretDenConfig = {
    ferretDenPath: config.ferretDenPath || "/home/toxic/estate/ranch/ferret-den",
    pdToolsDir: config.pdToolsDir || "/home/toxic/.pdtm/go/bin",
    reconDomain: config.reconDomain || ""
  };
  
  const results: FerretDenResult[] = [];
  
  // Check if ferret-den exists
  if (!existsSync(ferretConfig.ferretDenPath)) {
    console.warn(`⚠️  Ferret-den not found at ${ferretDenPath}, skipping recon`);
    return results;
  }
  
  // Extract domains from indicators
  const domain = ferretConfig.reconDomain;
  if (!domain) {
    console.log("  ⚠️  No recon domain configured, skipping ferret-den recon");
    return results;
  }
  
  console.log(`🕵️  Running ferret-den recon on: ${domain}`);
  
  // Run recon workflow
  const reconResult = await runReconWorkflow(domain, ferretConfig);
  results.push(reconResult);
  
  return results;
}

async function runReconWorkflow(
  domain: string,
  cfg: FerretDenConfig
): Promise<FerretDenResult> {
  const startTime = Date.now();
  
  return new Promise((resolve) => {
    const env = {
      ...process.env,
      PD_TOOLS_DIR: cfg.pdToolsDir
    };
    
    // First, discover subdomains
    const subfinderPath = join(cfg.pdToolsDir, "subfinder");
    
    if (!existsSync(subfinderPath)) {
      resolve({
        tool: "subfinder",
        ok: false,
        output: null,
        error: "subfinder binary not found",
        latencyMs: Date.now() - startTime
      });
      return;
    }
    
    const child = spawn(subfinderPath, [domain, "-silent"], {
      env,
      timeout: 120000,
      stdio: ["ignore", "pipe", "pipe"]
    });
    
    let stdout = "";
    let stderr = "";
    
    child.stdout?.on("data", (data) => { stdout += data.toString(); });
    child.stderr?.on("data", (data) => { stderr += data.toString(); });
    
    child.on("close", (code) => {
      const subdomains = stdout.trim().split('\n').filter(Boolean);
      resolve({
        tool: "subfinder",
        ok: code === 0,
        output: { domain, subdomains, count: subdomains.length },
        error: code !== 0 ? stderr : undefined,
        latencyMs: Date.now() - startTime
      });
    });
    
    child.on("error", (err) => {
      resolve({
        tool: "subfinder",
        ok: false,
        output: null,
        error: err.message,
        latencyMs: Date.now() - startTime
      });
    });
  });
}

export async function runDnsxResolution(
  domains: string[],
  cfg: FerretDenConfig
): Promise<FerretDenResult> {
  const startTime = Date.now();
  
  return new Promise((resolve) => {
    const dnsxPath = join(cfg.pdToolsDir, "dnsx");
    
    if (!existsSync(dnsxPath)) {
      resolve({
        tool: "dnsx",
        ok: false,
        output: null,
        error: "dnsx binary not found",
        latencyMs: Date.now() - startTime
      });
      return;
    }
    
    const inputFile = `/tmp/musescope-dnsx-input-${Date.now()}.txt`;
    writeFileSync(inputFile, domains.join('\n'), 'utf-8');
    
    const child = spawn(dnsxPath, [
      "-silent",
      "-l", inputFile
    ], {
      env: process.env,
      timeout: 120000,
      stdio: ["ignore", "pipe", "pipe"]
    });
    
    let stdout = "";
    child.stdout?.on("data", (data) => { stdout += data.toString(); });
    
    child.on("close", (code) => {
      const hosts = stdout.trim().split('\n').filter(Boolean);
      resolve({
        tool: "dnsx",
        ok: code === 0,
        output: { hosts, count: hosts.length },
        latencyMs: Date.now() - startTime
      });
    });
    
    child.on("error", (err) => {
      resolve({
        tool: "dnsx",
        ok: false,
        output: null,
        error: err.message,
        latencyMs: Date.now() - startTime
      });
    });
  });
}

export async function runNucleiScanner(
  hosts: string[],
  cfg: FerretDenConfig
): Promise<FerretDenResult> {
  const startTime = Date.now();
  
  return new Promise((resolve) => {
    const nucleiPath = join(cfg.pdToolsDir, "nuclei");
    
    if (!existsSync(nucleiPath)) {
      resolve({
        tool: "nuclei",
        ok: false,
        output: null,
        error: "nuclei binary not found (requires confirm: true)",
        latencyMs: Date.now() - startTime
      });
      return;
    }
    
    // Warning: nuclei requires explicit confirmation
    console.warn("⚠️  nuclei requires 'confirm: true' - skipping automated scan for safety");
    
    resolve({
      tool: "nuclei",
      ok: false,
      output: null,
      error: "nuclei requires manual confirmation for safety",
      latencyMs: Date.now() - startTime
    });
  });
}