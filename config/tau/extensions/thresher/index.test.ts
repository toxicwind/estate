import { describe, expect, it } from "bun:test";
import gatehouseExtension from "./index";

describe("gatehouse extension", () => {
  it("registers federation discovery and execution tools", () => {
    const tools: Record<string, any> = {};
    const mockPi: any = {
      registerTool: (t: any) => { tools[t.name] = t; },
    };
    gatehouseExtension(mockPi);

    expect(tools.gatehouse_discover).toBeDefined();
    expect(tools.gatehouse_retrieve_tools).toBeDefined();
    expect(tools.gatehouse_call_tool).toBeDefined();
    expect(tools.gatehouse_activity).toBeDefined();
  });
});
