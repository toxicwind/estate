import { describe, expect, it } from "bun:test";
import vansrouterExtension from "./index";

describe("vansrouter extension", () => {
  it("registers dynamic provider configuration", () => {
    let config: any = null;
    const mockPi: any = {
      registerProvider: (name: string, cfg: any) => { config = cfg; },
      on: () => {},
    };
    vansrouterExtension(mockPi);

    expect(config).toBeDefined();
    expect(config.baseUrl).toBe("http://127.0.0.1:20128/v1");
    expect(config.api).toBe("openai-completions");
  });
});
