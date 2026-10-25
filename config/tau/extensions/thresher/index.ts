/**
 * Thresher MCP Federation Extension for Tau.
 *
 * Bridges the estate's :25127 Thresher MCP federation gateway directly into Tau:
 * - Exposes gatehouse_discover: list connected MCP servers (exa, ffs, github, filesystem)
 * - Exposes gatehouse_retrieve_tools: natural language search for tools across servers
 * - Exposes gatehouse_call_tool: call any federated tool through Thresher
 * - Exposes gatehouse_activity: audit log of tool execution
 */

import type { ExtensionAPI } from "tau";

const GATEHOUSE_URL = process.env.GATEHOUSE_URL || "http://127.0.0.1:25127";

export default function (pi: ExtensionAPI) {
  // 1. Tool discovery
  pi.registerTool({
    name: "gatehouse_discover",
    description: "List all MCP servers connected to the estate Thresher federation gateway (:25127) with their status and tool counts.",
    parameters: {
      type: "object",
      properties: {},
    },
    handler: async () => {
      const res = await fetch(`${GATEHOUSE_URL}/api/v1/servers`, {
        headers: { Accept: "application/json" },
      });
      return res.json();
    },
  });

  // 2. BM25 tool search
  pi.registerTool({
    name: "gatehouse_retrieve_tools",
    description: "Search across all connected Thresher MCP servers (exa, ffs, github, filesystem, etc.) for tools matching a query.",
    parameters: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search query describing the capability needed" },
        limit: { type: "number", description: "Maximum tools to return (default: 10)" },
      },
      required: ["query"],
    },
    handler: async ({ query, limit = 10 }: { query: string; limit?: number }) => {
      const res = await fetch(`${GATEHOUSE_URL}/api/v1/tools/retrieve`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ query, limit }),
      });
      return res.json();
    },
  });

  // 3. Federated tool execution
  pi.registerTool({
    name: "gatehouse_call_tool",
    description: "Execute a tool on any MCP server connected to Thresher (e.g. server: 'exa', tool: 'search').",
    parameters: {
      type: "object",
      properties: {
        server: { type: "string", description: "Target MCP server name (e.g. exa, ffs, github)" },
        tool: { type: "string", description: "Target tool name" },
        args: { type: "object", description: "Arguments for the tool" },
      },
      required: ["server", "tool"],
    },
    handler: async ({ server, tool, args = {} }: { server: string; tool: string; args?: Record<string, unknown> }) => {
      const res = await fetch(`${GATEHOUSE_URL}/api/v1/servers/${encodeURIComponent(server)}/tools/${encodeURIComponent(tool)}/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ args }),
      });
      return res.json();
    },
  });

  // 4. Activity inspection
  pi.registerTool({
    name: "gatehouse_activity",
    description: "Query the Thresher audit log for recent federated tool calls and results.",
    parameters: {
      type: "object",
      properties: {
        limit: { type: "number", description: "Number of records to fetch (default: 20)" },
      },
    },
    handler: async ({ limit = 20 }: { limit?: number }) => {
      const res = await fetch(`${GATEHOUSE_URL}/api/v1/activity?limit=${limit}`, {
        headers: { Accept: "application/json" },
      });
      return res.json();
    },
  });
}
