// ============================================================================
// SOVEREIGN — Service Test Framework
// Reusable, non-destructive tests for all services
// Uses curl for HTTP (handles compression) and Bun.connect for TCP
// ============================================================================

import { loadSovereignPorts } from "../../src/lib/ports.ts";
loadSovereignPorts();

export interface ServiceTestConfig {
  name: string;
  port: number;
  healthEndpoints: string[];
  expectedResponse?: (body: string) => boolean;
  tcpOnly?: boolean;
  skipHttpCheck?: boolean;
}

export interface TestResult {
  service: string;
  passed: boolean;
  latencyMs: number;
  error?: string;
  details?: Record<string, any>;
}

export class ServiceTester {
  private results: TestResult[] = [];
  private baseUrl = "http://127.0.0.1";

  async testService(config: ServiceTestConfig): Promise<TestResult> {
    const start = Date.now();
    const errors: string[] = [];
    const details: Record<string, any> = { port: config.port };

    try {
      if (!config.skipHttpCheck) {
        let httpOk = false;
        let lastError = "";

        for (const endpoint of config.healthEndpoints) {
          try {
            const result = await this.curlHealthCheck(config.port, endpoint);
            details[endpoint] = { status: result.status, bodyLength: result.body.length, headers: result.headers };

            if (result.status === 200 && (config.expectedResponse ? config.expectedResponse(result.body) : true)) {
              httpOk = true;
              break;
            }
            lastError = `HTTP ${result.status}`;
          } catch (e) {
            lastError = String(e);
            details[endpoint] = { error: lastError };
          }
        }

        if (!httpOk) {
          errors.push(`No healthy HTTP endpoint: ${lastError}`);
        }
      }

      // TCP check as fallback
      if (!config.skipHttpCheck || config.tcpOnly) {
        try {
          const conn = await this.checkTcp(config.port);
          details.tcp = conn ? "connected" : "refused";
          if (!conn && errors.length > 0) {
            errors.push("TCP connection failed");
          }
        } catch {
          details.tcp = "failed";
          if (errors.length > 0) errors.push("TCP check failed");
        }
      }

    } catch (e) {
      errors.push(String(e));
    }

    const latencyMs = Date.now() - start;
    const passed = errors.length === 0;

    const result: TestResult = {
      service: config.name,
      passed,
      latencyMs,
      error: errors.join("; ") || undefined,
      details,
    };

    this.results.push(result);
    return result;
  }

  private async curlHealthCheck(port: number, endpoint: string): Promise<{ status: number; body: string; headers: Record<string, string> }> {
    const proc = Bun.spawn({
      cmd: ["curl", "-sf", "-m", "5", "-H", "Accept: application/json, text/html, */*", "-H", "Accept-Encoding: gzip, deflate", "-D", "-", `${this.baseUrl}:${port}${endpoint}`],
      stdout: "pipe",
      stderr: "pipe",
    });

    const [stdout, stderr] = await Promise.all([
      new Response(proc.stdout).text(),
      new Response(proc.stderr).text(),
    ]);

    const exitCode = await proc.exited;

    // Parse headers and body from curl -D - output
    const lines = stdout.split("\n");
    const headers: Record<string, string> = {};
    let bodyStart = 0;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.trim() === "") {
        bodyStart = i + 1;
        break;
      }
      const colonIdx = line.indexOf(":");
      if (colonIdx > 0) {
        headers[line.slice(0, colonIdx).toLowerCase()] = line.slice(colonIdx + 1).trim();
      }
    }

    const body = lines.slice(bodyStart).join("\n");
    const status = exitCode === 0 ? 200 : 0;

    if (exitCode !== 0) {
      throw new Error(stderr || `curl failed with code ${exitCode}`);
    }

    return { status, body, headers };
  }

  private async checkTcp(port: number): Promise<boolean> {
    try {
      const conn = await Bun.connect({ hostname: "127.0.0.1", port, timeout: 2000 });
      conn.end();
      return true;
    } catch {
      return false;
    }
  }

  async testRedis(port: number): Promise<TestResult> {
    const start = Date.now();
    try {
      const proc = Bun.spawn({
        cmd: ["redis-cli", "-p", String(port), "PING"],
        stdout: "pipe",
        stderr: "pipe",
      });
      const stdout = await new Response(proc.stdout).text();
      await proc.exited;
      return {
        service: "redis",
        passed: stdout.trim() === "PONG",
        latencyMs: Date.now() - start,
        details: { response: stdout.trim() },
      };
    } catch (e) {
      return {
        service: "redis",
        passed: false,
        latencyMs: Date.now() - start,
        error: String(e),
      };
    }
  }

  getResults(): TestResult[] {
    return this.results;
  }

  printSummary(): void {
    console.log("\n=== TEST SUMMARY ===");
    for (const r of this.results) {
      const status = r.passed ? "✅ PASS" : "❌ FAIL";
      console.log(`${status} ${r.service} (${r.latencyMs}ms)${r.error ? " - " + r.error : ""}`);
    }
    const passed = this.results.filter(r => r.passed).length;
    console.log(`\n${passed}/${this.results.length} tests passed`);
  }

  clear(): void {
    this.results = [];
  }
}

// ============================================================================
// Service Test Configurations
// ============================================================================

export function getServiceTests(): ServiceTestConfig[] {
  const ports = {
    LLAMA_SWAP_PORT: parseInt(process.env.LLAMA_SWAP_PORT || "25100"),
    MCPPROXY_PORT: parseInt(process.env.MCPPROXY_PORT || "25109"),
    GHAS_API_PORT: parseInt(process.env.GHAS_API_PORT || "25112"),
    GHAS_MCP_PORT: parseInt(process.env.GHAS_MCP_PORT || "25113"),
    GHAS_FRONTEND_PORT: parseInt(process.env.GHAS_FRONTEND_PORT || "25114"),
    PROMETHEUS_PORT: parseInt(process.env.PROMETHEUS_PORT || "25105"),
    GRAFANA_PORT: parseInt(process.env.GRAFANA_PORT || "25110"),
    OPENFANG_PORT: parseInt(process.env.OPENFANG_PORT || "25103"),
    RUST_WEB_BACKEND_PORT: parseInt(process.env.RUST_WEB_BACKEND_PORT || "25101"),
    HF_DOWNLOADER_PORT: parseInt(process.env.HF_DOWNLOADER_PORT || "25106"),
    PI_WEB_DASHBOARD_PORT: parseInt(process.env.PI_WEB_DASHBOARD_PORT || "25192"),
    QDRANT_PORT: parseInt(process.env.QDRANT_PORT || "25133"),
    REDIS_PORT: parseInt(process.env.REDIS_PORT || "25199"),
    PI_AGENT_PORT: parseInt(process.env.PI_AGENT_PORT || "25125"),
    KIMI_CODE_PORT: parseInt(process.env.KIMI_CODE_PORT || "25126"),
  };

  return [
    {
      name: "llama-swap",
      port: ports.LLAMA_SWAP_PORT,
      healthEndpoints: ["/health", "/v1/models"],
      expectedResponse: (body) => body.includes("OK") || body.includes("models"),
    },
    {
      name: "mcpproxy",
      port: ports.MCPPROXY_PORT,
      healthEndpoints: ["/health"],
    },
    {
      name: "ghas-api",
      port: ports.GHAS_API_PORT,
      healthEndpoints: ["/health"],
    },
    {
      name: "ghas-mcp",
      port: ports.GHAS_MCP_PORT,
      healthEndpoints: ["/health"],
    },
    {
      name: "ghas-frontend",
      port: ports.GHAS_FRONTEND_PORT,
      healthEndpoints: ["/", "/health"],
    },
    {
      name: "prometheus",
      port: ports.PROMETHEUS_PORT,
      healthEndpoints: ["/-/healthy", "/-/ready"],
    },
    {
      name: "grafana",
      port: ports.GRAFANA_PORT,
      healthEndpoints: ["/api/health"],
    },
    {
      name: "openfang",
      port: ports.OPENFANG_PORT,
      healthEndpoints: ["/api/health"],
    },
    {
      name: "rust-web",
      port: ports.RUST_WEB_BACKEND_PORT,
      healthEndpoints: ["/health"],
    },
    {
      name: "hf-downloader",
      port: ports.HF_DOWNLOADER_PORT,
      healthEndpoints: ["/api/health"],
    },
    {
      name: "pi-web-dashboard",
      port: ports.PI_WEB_DASHBOARD_PORT,
      healthEndpoints: ["/api/health"],
    },
    {
      name: "qdrant",
      port: ports.QDRANT_PORT,
      healthEndpoints: ["/"],
    },
    {
      name: "redis",
      port: ports.REDIS_PORT,
      healthEndpoints: [],
      skipHttpCheck: true,
      tcpOnly: true,
    },
    {
      name: "kimi-code",
      port: ports.KIMI_CODE_PORT,
      healthEndpoints: ["/health"],
    },
  ];
}

// ============================================================================
// Main Test Runner
// ============================================================================

export async function runAllTests(): Promise<TestResult[]> {
  const tester = new ServiceTester();
  const tests = getServiceTests();

  console.log("Running service health tests...\n");

  for (const test of tests) {
    if (test.name === "redis") {
      const result = await tester.testRedis(test.port);
      tester.results.push(result);
      console.log(`${result.passed ? "✅" : "❌"} ${result.service} (${result.latencyMs}ms)${result.error ? " - " + result.error : ""}`);
    } else {
      const result = await tester.testService(test);
      console.log(`${result.passed ? "✅" : "❌"} ${result.service} (${result.latencyMs}ms)${result.error ? " - " + result.error : ""}`);
    }
  }

  // Test Redis separately
  if (!tests.find(t => t.name === "redis")) {
    const redisResult = await tester.testRedis(parseInt(process.env.REDIS_PORT || "25199"));
    tester.results.push(redisResult);
  }

  return tester.getResults();
}

// CLI entry point
if (import.meta.main) {
  const results = await runAllTests();
  const tester = new ServiceTester();
  tester.results = results;
  tester.printSummary();

  const failed = results.filter(r => !r.passed);
  if (failed.length > 0) {
    console.error(`\n${failed.length} test(s) failed`);
    process.exit(1);
  }
  process.exit(0);
}