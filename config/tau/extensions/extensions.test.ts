import { describe, expect, it } from "bun:test";
import gatehouseExtension from "./gatehouse";
import vansrouterExtension from "./vansrouter";
import strictBashGuard from "./strict-bash-guard";

describe("Tau Extensions Suite", () => {
  it("registers gatehouse MCP tools with expected signatures", () => {
    const registeredTools: Record<string, any> = {};
    const mockPi: any = {
      registerTool: (tool: any) => {
        registeredTools[tool.name] = tool;
      },
    };

    gatehouseExtension(mockPi);

    expect(registeredTools.gatehouse_discover).toBeDefined();
    expect(registeredTools.gatehouse_retrieve_tools).toBeDefined();
    expect(registeredTools.gatehouse_call_tool).toBeDefined();
    expect(registeredTools.gatehouse_activity).toBeDefined();

    expect(registeredTools.gatehouse_call_tool.parameters.required).toContain("server");
    expect(registeredTools.gatehouse_call_tool.parameters.required).toContain("tool");
  });

  it("registers vansrouter provider with dynamic models fetcher", () => {
    let registeredProvider: any = null;
    let registeredName = "";
    const mockPi: any = {
      registerProvider: (name: string, config: any) => {
        registeredName = name;
        registeredProvider = config;
      },
      on: () => {},
    };

    vansrouterExtension(mockPi);

    expect(registeredName).toBe("vansrouter");
    expect(registeredProvider).toBeDefined();
    expect(registeredProvider.baseUrl).toBe("http://127.0.0.1:20128/v1");
    expect(registeredProvider.api).toBe("openai-completions");
    expect(typeof registeredProvider.fetchDynamicModels).toBe("function");
  });

  it("blocks dangerous duplicate shell commands in strict-bash-guard", async () => {
    let hook: any = null;
    const mockPi: any = {
      on: (event: string, fn: any) => {
        if (event === "tool_call") hook = fn;
      },
    };

    strictBashGuard(mockPi);
    expect(hook).toBeDefined();

    // Test find blocked
    const resFind = await hook({ tool: "bash", input: { command: "find /home/toxic -name '*.txt'" } });
    expect(resFind?.block).toBe(true);

    // Test cat blocked
    const resCat = await hook({ tool: "bash", input: { command: "cat /home/toxic/.bashrc" } });
    expect(resCat?.block).toBe(true);

    // Test safe command allowed
    const resSafe = await hook({ tool: "bash", input: { command: "git status" } });
    expect(resSafe?.block).toBeUndefined();
  });
});
