import { McpGateway } from "./gateway.ts"
// local mcpproxy aggregator -> exposes /health and /mcp for tools/list and tools/call
// talks to gatehouse :25127 and herd :25100, uses SCOUT_BASE_URL if set
Bun.serve({
  port: Number(process.env.MCP_GATEWAY_PORT || 25155),
  fetch(req) {
    const url = new URL(req.url)
    if (url.pathname === "/health") return new Response("ok")
    if (url.pathname === "/mcp") return McpGateway.handle(req)
    return new Response("not found", {status: 404})
  }
})
console.log("mcp-gateway listening on", process.env.MCP_GATEWAY_PORT || 25155)
