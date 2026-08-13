// ============================================================================
// SOVEREIGN — Extended Service Tests (Yote, Openfang, AST Matrix)
// Reusable, non-destructive, uses curl + redis-cli + native TCP checks
// ============================================================================

import { ServiceTestConfig, ServiceTester } from "./test-framework";

export interface ExtendedServiceTest {
  service: string;
  portKey: string;
  tests: ServiceTestConfig[];
  specialChecks?: (() => Promise<{ name: string; passed: boolean; error?: string; details?: any }>)[];
}

export const extendedTests: ExtendedServiceTest[] = [
  {
    service: "yote",
    portKey: "YOTE_PORT",
    tests: [
      {
        name: "yote-http",
        port: 25102,
        healthEndpoints: ["/", "/health"],
        skipHttpCheck: true,
        tcpOnly: true,
      },
    ],
    specialChecks: [
      async () => {
        // Check if yote binary exists
        const proc = Bun.spawn({ cmd: ["ls", "/home/toxic/projects/yote/src/index.ts"], stdout: "pipe" });
        const stdout = await new Response(proc.stdout).text();
        await proc.exited;
        return {
          name: "yote-source-exists",
          passed: stdout.trim().length > 0,
          details: { path: "/home/toxic/projects/yote/src/index.ts", stdout: stdout.trim() },
        };
      },
      async () => {
        // Check build artifacts
        const proc = Bun.spawn({ cmd: ["ls", "/home/toxic/projects/yote/build/"], stdout: "pipe" });
        const stdout = await new Response(proc.stdout).text();
        await proc.exited;
        return {
          name: "yote-build-dir",
          passed: stdout.trim().includes("yote"),
          details: { stdout: stdout.trim() },
        };
      },
    ],
  },
  {
    service: "openfang",
    portKey: "OPENFANG_PORT",
    tests: [
      {
        name: "openfang-health",
        port: 25103,
        healthEndpoints: ["/api/health", "/"],
        expectedResponse: (body) => body.length > 0,
      },
      {
        name: "openfang-tcp",
        port: 25103,
        healthEndpoints: [],
        skipHttpCheck: true,
        tcpOnly: true,
      },
    ],
    specialChecks: [
      async () => {
        // Verify openfang binary/script exists
        const proc = Bun.spawn({ cmd: ["test", "-f", "/home/toxic/sovereign/stack/services/openfang.sh"], stdout: "pipe" });
        await proc.exited;
        return {
          name: "openfang-script-exists",
          passed: proc.exitCode === 0,
          details: { exitCode: proc.exitCode },
        };
      },
      async () => {
        // Check openfang process
        const proc = Bun.spawn({ cmd: ["pgrep", "-f", "openfang"], stdout: "pipe", stderr: "pipe" });
        const stdout = await new Response(proc.stdout).text();
        await proc.exited;
        return {
          name: "openfang-process-running",
          passed: stdout.trim().length > 0,
          details: { stdout: stdout.trim(), exitCode: proc.exitCode ?? null },
        };
      },
    ],
  },
  {
    service: "astmatrix",
    portKey: "ASTMATRIX_PORT",
    tests: [
      {
        name: "astmatrix-api",
        port: 25115,
        healthEndpoints: ["/", "/api/health", "/mesh/"],
        skipHttpCheck: false,
      },
    ],
    specialChecks: [
      async () => {
        // Check astmatrix source/config presence
        const proc = Bun.spawn({ cmd: ["ls", "/home/toxic/projects/llama-swap-main/internal/astmatrix/"], stdout: "pipe" });
        const stdout = await new Response(proc.stdout).text();
        await proc.exited;
        return {
          name: "astmatrix-source-dir",
          passed: stdout.trim().includes("router"),
          details: { stdout: stdout.trim() },
        };
      },
      async () => {
        // Check astmatrix config in llama-swap config
        const proc = Bun.spawn({ cmd: ["bash", "-c", "grep -q astmatrix /home/toxic/sovereign/config/llama-swap.yaml && echo FOUND || echo MISSING"], stdout: "pipe", stderr: "pipe" });
        const stdout = await new Response(proc.stdout).text();
        await proc.exited;
        return {
          name: "astmatrix-config-present",
          passed: stdout.trim() === "FOUND" || stdout.trim().includes("astmatrix"),
          details: { stdout: stdout.trim(), exitCode: proc.exitCode ?? null },
        };
      },
      async () => {
        // Check astmatrix router initialization in source
        const proc = Bun.spawn({ cmd: ["grep", "-r", "astmatrix.NewRouter", "/home/toxic/projects/llama-swap-main/internal/", "--include=*.go"], stdout: "pipe", stderr: "pipe" });
        const stdout = await new Response(proc.stdout).text();
        await proc.exited;
        return {
          name: "astmatrix-router-code",
          passed: stdout.trim().includes("astmatrix"),
          details: { stdout: stdout.trim(), exitCode: proc.exitCode ?? null },
        };
      },
    ],
  },
];

// ============================================================================
// Extended test runner
// ============================================================================

export async function runExtendedTests(): Promise<void> {
  const tester = new ServiceTester();
  const allResults: { service: string; checks: { name: string; passed: boolean; error?: string; details?: any; latencyMs?: number }[] }[] = [];

  for (const ext of extendedTests) {
    const checks: any[] = [];
    const servicePort = parseInt(process.env[ext.portKey] ?? ext.tests[0]?.port?.toString() ?? "0");

    console.log(`\n=== EXTENDED TESTS: ${ext.service.toUpperCase()} ===`);

    // Run standard HTTP/TCP tests
    for (const test of ext.tests) {
      const port = test.port || servicePort;
      if (test.skipHttpCheck && test.tcpOnly) {
        // TCP-only check
        const start = Date.now();
        try {
          const conn = await tester["checkTcp"](port);
          checks.push({ name: test.name, passed: conn, latencyMs: Date.now() - start, details: { tcp: conn ? "connected" : "refused" } });
          console.log(`${conn ? "TCP-CONN" : "TCP-FAIL"} ${test.name} (${Date.now() - start}ms) port=${port}`);
        } catch (e) {
          checks.push({ name: test.name, passed: false, error: String(e), latencyMs: Date.now() - start, details: { error: String(e) } });
          console.log(`TCP-FAIL ${test.name} - ${e}`);
        }
      } else {
        const result = await tester.testService({ ...test, port: test.port || servicePort });
        checks.push({ name: result.service, passed: result.passed, error: result.error, details: result.details, latencyMs: result.latencyMs });
        console.log(`${result.passed ? "PASS" : "FAIL"} ${result.service} (${result.latencyMs}ms)${result.error ? " - " + result.error : ""}`);
      }
    }

    // Run special checks
    if (ext.specialChecks) {
      for (const checkFn of ext.specialChecks) {
        const start = Date.now();
        try {
          const checkResult = await checkFn();
          const latencyMs = Date.now() - start;
          checks.push({ ...checkResult, latencyMs });
          console.log(`${checkResult.passed ? "PASS" : "FAIL"} ${checkResult.name} (${latencyMs}ms)${checkResult.error ? " - " + checkResult.error : ""}`);
        } catch (e) {
          const latencyMs = Date.now() - start;
          checks.push({ name: "special-check", passed: false, error: String(e), latencyMs, details: { exception: String(e) } });
          console.log(`FAIL special-check (${latencyMs}ms) - ${e}`);
        }
      }
    }

    allResults.push({ service: ext.service, checks });
  }

  // Summary
  console.log("\n=== EXTENDED TEST SUMMARY ===");
  let totalPassed = 0;
  let totalChecks = 0;
  for (const res of allResults) {
    console.log(`\n--- ${res.service.toUpperCase()} ---`);
    for (const c of res.checks) {
      totalChecks++;
      if (c.passed) totalPassed++;
      console.log(`  ${c.passed ? "PASS" : "FAIL"} ${c.name} (${c.latencyMs ?? 0}ms)${c.error ? " - " + c.error : ""}`);
    }
  }
  console.log(`\nTotal: ${totalPassed}/${totalChecks} passed`);
}

if (import.meta.main) {
  await runExtendedTests();
}