import { describe, expect, it } from "bun:test";
import strictBashGuard from "./index";

describe("strict-bash-guard extension", () => {
  it("blocks duplicate shell utilities", async () => {
    let hook: any = null;
    const mockPi: any = {
      on: (event: string, fn: any) => { if (event === "tool_call") hook = fn; },
    };
    strictBashGuard(mockPi);

    const res = await hook({ tool: "bash", input: { command: "find . -name '*.ts'" } });
    expect(res?.block).toBe(true);
  });
});
