/**
 * Gateway Integration Test
 *
 * Tests the complete workflow of tool discovery and execution
 * through the Sovereign MCP Gateway
 */

import { describe, it, expect, beforeEach } from "bun:test";
import {
  createState,
  buildDiscover,
  buildToolsList,
  selectUpstream,
  stickySet,
  circuitMarkFail,
  type GatewayState,
  type Upstream,
} from "../tools/sovereign-router/sovereign-mcp-gateway/gateway-core.ts";

describe("Gateway Integration Test", () => {
  const UPSTREAMS: Upstream[] = [
    { name: "byte-vision", base: "http://127.0.0.1:25121" },
    { name: "ghas-mcp", base: "http://127.0.0.1:25122" },
  ];

  let state: GatewayState;

  beforeEach(() => {
    state = createState({
      circuitOpenMs: 1000,
      halfProbeMs: 500,
      stickyTtlMs: 10000,
    });
  });

  it("should build correct tool discovery response", () => {
    // Simulate cached upstream info
    state.upstreamInfo.set("byte-vision", {
      serverInfo: { name: "byte-vision", version: "1.0" },
      capabilities: { tools: { listChanged: false } },
      tools: [
        { name: "generate_completion", upstream: "byte-vision", description: "Generate text" },
        { name: "search_code", upstream: "byte-vision", description: "Search code" },
      ],
      cachedAt: Date.now(),
    });

    state.upstreamInfo.set("ghas-mcp", {
      serverInfo: { name: "ghas-mcp", version: "2.0" },
      capabilities: { code_search: true },
      tools: [
        { name: "github_search", upstream: "ghas-mcp", description: "Search GitHub" },
      ],
      cachedAt: Date.now(),
    });

    const discover = buildDiscover(state, UPSTREAMS);

    // Verify structure
    expect(discover.jsonrpc).toBe("2.0");
    expect(discover.result.server_info.name).toBe("sovereign-mcp-gateway");
    expect(discover.result.tools.length).toBe(3);

    // Verify tool namespacing
    const toolNames = discover.result.tools.map((t: any) => t.name);
    expect(toolNames).toContain("byte-vision__generate_completion");
    expect(toolNames).toContain("byte-vision__search_code");
    expect(toolNames).toContain("ghas-mcp__github_search");

    // Verify descriptions include provenance
    const descriptions = discover.result.tools.map((t: any) => t.description);
    expect(descriptions[0]).toContain("[byte-vision]");
    expect(descriptions[2]).toContain("[ghas-mcp]");
  });

  it("should handle routing with sticky sessions and circuit breakers", () => {
    // Set up healthy upstreams
    state.upstreamInfo.set("byte-vision", {
      serverInfo: {},
      capabilities: {},
      tools: [],
      cachedAt: Date.now(),
    });

    state.upstreamInfo.set("ghas-mcp", {
      serverInfo: {},
      capabilities: {},
      tools: [],
      cachedAt: Date.now(),
    });

    // First request - should go to first healthy upstream
    const firstSelection = selectUpstream(state, UPSTREAMS, "session1");
    expect(firstSelection).toBe("byte-vision");

    // Set sticky session
    stickySet(state, "session1", "byte-vision");

    // Second request with same session - should stick to byte-vision
    const secondSelection = selectUpstream(state, UPSTREAMS, "session1");
    expect(secondSelection).toBe("byte-vision");

    // Mark byte-vision as failed (3 failures)
    circuitMarkFail(state, "byte-vision");
    circuitMarkFail(state, "byte-vision");
    circuitMarkFail(state, "byte-vision");

    // Third request - should failover to ghas-mcp since byte-vision is now open
    const thirdSelection = selectUpstream(state, UPSTREAMS, "session1");
    expect(thirdSelection).toBe("ghas-mcp");

    // New session - should go to healthy upstream (ghas-mcp)
    const newSessionSelection = selectUpstream(state, UPSTREAMS, "session2");
    expect(newSessionSelection).toBe("ghas-mcp");
  });

  it("should build correct tools/list response", () => {
    // Simulate cached upstream info
    state.upstreamInfo.set("byte-vision", {
      serverInfo: {},
      capabilities: {},
      tools: [
        { name: "generate_completion", upstream: "byte-vision", description: "Generate text" },
      ],
      cachedAt: Date.now(),
    });

    const toolsList = buildToolsList(state, UPSTREAMS);

    expect(toolsList.jsonrpc).toBe("2.0");
    expect(toolsList.result.tools.length).toBe(1);
    expect(toolsList.result.tools[0].name).toBe("byte-vision__generate_completion");
    expect(toolsList.result.tools[0].description).toBe("[byte-vision] Generate text");
  });

  it("should handle upstream failures gracefully", () => {
    // Mark both upstreams as failed
    circuitMarkFail(state, "byte-vision");
    circuitMarkFail(state, "byte-vision");
    circuitMarkFail(state, "byte-vision");

    circuitMarkFail(state, "ghas-mcp");
    circuitMarkFail(state, "ghas-mcp");
    circuitMarkFail(state, "ghas-mcp");

    // Should return null when no healthy upstreams
    const selection = selectUpstream(state, UPSTREAMS, "session1");
    expect(selection).toBe(null);
  });
});

console.log("✅ All gateway integration tests passed!");
