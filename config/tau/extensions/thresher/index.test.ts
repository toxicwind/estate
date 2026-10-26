import { describe, expect, it } from "bun:test";
import thresherExtension from "./index";

describe("thresher extension", () => {
  it("registers federation discovery and execution tools", () => {
    const tools: Record<string, any> = {};
    const mockPi: any = {
      registerTool: (t: any) => { tools[t.name] = t; },
    };
    thresherExtension(mockPi);

    expect(tools.thresher_discover).toBeDefined();
    expect(tools.thresher_retrieve_tools).toBeDefined();
    expect(tools.thresher_call_tool).toBeDefined();
    expect(tools.thresher_activity).toBeDefined();
  });
});
