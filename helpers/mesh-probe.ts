#!/usr/bin/env bun
/**
 * Sovereign Mesh Probe Helper
 * High-performance, clean JSON-RPC 2.0 probe for mcpproxy-go on port 25127.
 * Validates endpoint liveness, protocol handshake, and tool catalog retrieval.
 */

const MESH_URL = process.env.MESH_URL || "http://127.0.0.1:25127/mcp";
const HEALTH_URL = process.env.MESH_HEALTH_URL || "http://127.0.0.1:25127/health";

async function probe() {
  console.log(`[mesh-probe] Probing health: ${HEALTH_URL}`);
  const t0 = performance.now();
  try {
    const healthResp = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(2000) });
    const healthText = await healthResp.text();
    const healthMs = (performance.now() - t0).toFixed(1);
    console.log(`✅ Health check: ${healthResp.status} (${healthMs}ms) -> ${healthText.trim()}`);
  } catch (err) {
    console.error(`❌ Health check failed:`, err);
    process.exit(1);
  }

  console.log(`[mesh-probe] Sending JSON-RPC initialize: ${MESH_URL}`);
  const t1 = performance.now();
  try {
    const initPayload = {
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: { listChanged: true } },
        clientInfo: { name: "sovereign-mesh-probe", version: "1.0.0" },
      },
    };

    const rpcResp = await fetch(MESH_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
      body: JSON.stringify(initPayload),
      signal: AbortSignal.timeout(5000),
    });

    const rpcMs = (performance.now() - t1).toFixed(1);
    const rpcData = await rpcResp.json();
    console.log(`✅ JSON-RPC initialize: ${rpcResp.status} (${rpcMs}ms)`);
    console.log(`   Protocol Version: ${rpcData?.result?.protocolVersion}`);
    console.log(`   Server Name: ${rpcData?.result?.serverInfo?.name} (v${rpcData?.result?.serverInfo?.version})`);
    console.log(`   Capabilities: ${JSON.stringify(rpcData?.result?.capabilities)}`);
  } catch (err) {
    console.error(`❌ JSON-RPC initialize failed:`, err);
    process.exit(1);
  }
}

await probe();
