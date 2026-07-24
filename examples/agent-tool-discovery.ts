/**
 * Agent Tool Discovery Demo
 *
 * Demonstrates how an agent uses the Sovereign MCP Gateway for tool discovery
 * and execution following the ReAct/Reflexion agentic loop.
 */

import { runWithFallback, newContext } from "../tools/sovereign-monitor/recursive-fallback.ts";

// Mock MCP client that simulates the gateway's tool discovery API
class MockMcpClient {
  private sessionId: string;
  private upstream: string;

  constructor(sessionId: string = "agent-demo") {
    this.sessionId = sessionId;
    this.upstream = "byte-vision"; // Would be determined by gateway routing
  }

  /** Simulate server/discover call to gateway */
  async discover(): Promise<any> {
    return {
      jsonrpc: "2.0",
      id: null,
      result: {
        supported_versions: ["2024-11-05"],
        capabilities: {
          tools: { listChanged: false },
          multiToolUse: true
        },
        server_info: {
          name: "sovereign-mcp-gateway",
          version: "v1"
        },
        instructions: "Tools are namespaced as <upstream>__<tool>. The gateway load-balances and circuit-breaks across upstreams.",
        tools: [
          {
            name: "byte-vision__generate_completion",
            description: "[byte-vision] Generate text completions using LLM",
            inputSchema: {
              type: "object",
              properties: {
                prompt: { type: "string" },
                max_tokens: { type: "number" }
              }
            }
          },
          {
            name: "byte-vision__search_code",
            description: "[byte-vision] Search codebase for patterns",
            inputSchema: {
              type: "object",
              properties: {
                query: { type: "string" },
                language: { type: "string" }
              }
            }
          },
          {
            name: "byte-vision__analyze_image",
            description: "[byte-vision] Analyze images using vision models",
            inputSchema: {
              type: "object",
              properties: {
                image_url: { type: "string" },
                question: { type: "string" }
              }
            }
          }
        ]
      }
    };
  }

  /** Simulate tools/list call to gateway */
  async listTools(): Promise<any> {
    return {
      jsonrpc: "2.0",
      id: null,
      result: {
        tools: [
          {
            name: "byte-vision__generate_completion",
            description: "[byte-vision] Generate text completions using LLM"
          },
          {
            name: "byte-vision__search_code",
            description: "[byte-vision] Search codebase for patterns"
          },
          {
            name: "byte-vision__analyze_image",
            description: "[byte-vision] Analyze images using vision models"
          }
        ]
      }
    };
  }

  /** Simulate tool execution */
  async callTool(toolName: string, params: any): Promise<any> {
    console.log(`[${this.upstream}] Executing ${toolName} with params:`, params);

    // Simulate different tool responses
    if (toolName === "byte-vision__generate_completion") {
      return {
        jsonrpc: "2.0",
        id: "call-1",
        result: {
          content: [
            {
              type: "text",
              text: `Generated completion for: "${params.prompt}"

This is a simulated response from the byte-vision upstream showing how the gateway routes tool calls through circuit breakers and sticky sessions.`
            }
          ]
        }
      };
    }

    if (toolName === "byte-vision__search_code") {
      return {
        jsonrpc: "2.0",
        id: "call-2",
        result: {
          content: [
            {
              type: "text",
              text: `Found ${Math.floor(Math.random() * 10) + 1} matches for "${params.query}" in ${params.language || 'all'} files`
            }
          ]
        }
      };
    }

    return {
      jsonrpc: "2.0",
      id: "call-3",
      result: {
        content: [
          {
            type: "text",
            text: `Executed ${toolName} successfully`
          }
        ]
      }
    };
  }
}

// Agent workflow following ReAct pattern
async function agentWorkflow() {
  console.log("=== Sovereign Agent Tool Discovery Demo ===\n");

  const client = new MockMcpClient("demo-session-123");

  // Step 1: Discover available tools (OBSERVE phase)
  console.log("🔍 OBSERVE: Discovering available tools...");
  const discoverResponse = await client.discover();
  const availableTools = discoverResponse.result.tools;

  console.log(`\n📋 Available tools (${availableTools.length} total):`);
  availableTools.forEach((tool: any) => {
    console.log(`  • ${tool.name}`);
    console.log(`    ${tool.description}`);
  });

  // Step 2: Think about what tools to use (THINK phase)
  console.log("\n🤖 THINK: Planning tool execution...");
  const task = "Generate documentation for the MCP gateway system";
  const selectedTool = availableTools.find((t: any) =>
    t.name.includes("generate_completion")
  );

  if (!selectedTool) {
    console.log("❌ No suitable tool found!");
    return;
  }

  console.log(`✅ Selected tool: ${selectedTool.name}`);
  console.log(`🎯 Task: ${task}`);

  // Step 3: Execute the tool (ACT phase)
  console.log("\n⚡ ACT: Executing tool...");
  const executionResult = await client.callTool(selectedTool.name, {
    prompt: `Write comprehensive documentation for: ${task}\n\nInclude sections on:\n1. Circuit breaker pattern\n2. Sticky session affinity\n3. Tool discovery mechanism\n4. Routing decision logic\n5. Health monitoring`,
    max_tokens: 500
  });

  console.log("\n📄 RESULT:");
  console.log(executionResult.result.content[0].text);

  // Step 4: Reflect on the result (REFLECT phase)
  console.log("\n🔄 REFLECT: Evaluating execution...");
  const resultText = executionResult.result.content[0].text;

  if (resultText.includes("circuit breaker") &&
      resultText.includes("sticky session") &&
      resultText.includes("tool discovery")) {
    console.log("✅ Execution successful! All key concepts covered.");
  } else {
    console.log("⚠️  Execution incomplete. Missing key concepts.");
    console.log("🔄 Would trigger fallback mechanism in real scenario...");
  }

  // Demonstrate fallback with recursive-fallback module
  console.log("\n🛡️  DEMO: Recursive Fallback Mechanism");
  console.log("=" .repeat(50));

  const ctx = newContext(3, 10000); // 3 attempts, 10s budget

  const riskyWork = (input: any) => {
    // Simulate work that might fail
    if (Math.random() > 0.7) {
      throw new Error("Simulated failure in primary execution");
    }
    return { success: true, result: "Primary execution succeeded" };
  };

  const result = runWithFallback(
    { task: "demo" },
    riskyWork,
    ctx
  );

  console.log(`\nFallback result: ${result.ok ? 'SUCCESS' : 'FAILED'}`);
  console.log(`Strategy used: ${result.strategy}`);
  console.log(`Attempts: ${ctx.attempts}`);
  console.log(`Log entries: ${ctx.log.length}`);

  if (result.log.length > 0) {
    console.log("\nFallback log:");
    result.log.forEach((entry: string) => console.log(`  • ${entry}`));
  }
}

// Run the demo
agentWorkflow().catch(console.error);
