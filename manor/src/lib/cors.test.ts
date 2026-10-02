import { describe, it, expect, vi, afterEach } from "vitest";
import {
  defaultCorsConfig,
  isHttpToken,
  isValidCorsOrigin,
  validateCorsConfig,
  corsConfigToYaml,
  probeCorsPolicy,
  describeEffectivePolicy,
  DEFAULT_CORS_MAX_AGE,
  type CorsConfig,
  type CorsProbeResult,
} from "./cors";

describe("isHttpToken", () => {
  it("accepts methods and header names", () => {
    for (const t of ["GET", "POST", "X-Custom-Header", "Content-Type", "X-Requested-With"]) {
      expect(isHttpToken(t), t).toBe(true);
    }
  });

  it("rejects empty strings and separators", () => {
    for (const t of ["", "X Header", "X:Header", "X/Header", "héader"]) {
      expect(isHttpToken(t), JSON.stringify(t)).toBe(false);
    }
  });
});

describe("isValidCorsOrigin", () => {
  it("accepts the wildcard marker", () => {
    expect(isValidCorsOrigin("*")).toBe(true);
  });

  it("accepts bare scheme://host[:port] origins", () => {
    for (const o of [
      "https://dashboard.example.com",
      "http://localhost:25100",
      "https://192.168.1.10:8443",
    ]) {
      expect(isValidCorsOrigin(o), o).toBe(true);
    }
  });

  it("rejects paths, queries, fragments, userinfo and bare hosts", () => {
    for (const o of [
      "https://example.com/",
      "https://example.com/app",
      "https://example.com?x=1",
      "https://example.com#frag",
      "https://user@example.com",
      "example.com",
      "",
      "  https://example.com  ",
    ]) {
      expect(isValidCorsOrigin(o), JSON.stringify(o)).toBe(false);
    }
  });
});

describe("validateCorsConfig", () => {
  it("accepts an empty config (legacy permissive)", () => {
    expect(validateCorsConfig(defaultCorsConfig())).toEqual([]);
  });

  it("accepts a fully specified restricted policy", () => {
    const cfg: CorsConfig = {
      ...defaultCorsConfig(),
      allowedOrigins: ["https://dashboard.example.com"],
      allowCredentials: true,
      allowedMethods: ["GET", "POST"],
      allowedHeaders: ["Content-Type", "Authorization"],
      exposedHeaders: ["X-Request-Id"],
      maxAge: 3600,
    };
    expect(validateCorsConfig(cfg)).toEqual([]);
  });

  it("requires allowedOrigins when any other field is set", () => {
    const cfg = { ...defaultCorsConfig(), allowCredentials: true };
    const problems = validateCorsConfig(cfg);
    expect(problems.length).toBe(1);
    expect(problems[0]).toContain("allowedOrigins is required");
  });

  it("rejects wildcard paired with credentials or private network", () => {
    const creds: CorsConfig = {
      ...defaultCorsConfig(),
      allowedOrigins: ["*"],
      allowCredentials: true,
    };
    expect(validateCorsConfig(creds)[0]).toContain('may not contain "*"');

    const pna: CorsConfig = {
      ...defaultCorsConfig(),
      allowedOrigins: ["*"],
      allowPrivateNetwork: true,
    };
    expect(validateCorsConfig(pna)[0]).toContain('may not contain "*"');
  });

  it("accepts an explicit wildcard alone", () => {
    const cfg: CorsConfig = { ...defaultCorsConfig(), allowedOrigins: ["*"] };
    expect(validateCorsConfig(cfg)).toEqual([]);
  });

  it("rejects malformed origins, methods, headers and negative maxAge", () => {
    const cfg: CorsConfig = {
      allowedOrigins: ["not-an-origin"],
      allowCredentials: false,
      allowPrivateNetwork: false,
      allowedMethods: ["GE T"],
      allowedHeaders: ["X:Bad"],
      exposedHeaders: ["X Bad"],
      maxAge: -5,
    };
    const problems = validateCorsConfig(cfg);
    expect(problems.length).toBe(5);
  });
});

describe("corsConfigToYaml", () => {
  it("renders an empty block as a commented placeholder", () => {
    const yaml = corsConfigToYaml(defaultCorsConfig());
    expect(yaml).toBe("security:\n  cors:\n    # (empty — herd keeps the legacy permissive policy)\n");
  });

  it("renders a full policy with lists and scalars", () => {
    const cfg: CorsConfig = {
      allowedOrigins: ["https://dashboard.example.com", "http://localhost:25100"],
      allowCredentials: true,
      allowPrivateNetwork: true,
      allowedMethods: ["GET", "POST"],
      allowedHeaders: ["Content-Type"],
      exposedHeaders: ["X-Request-Id"],
      maxAge: 3600,
    };
    expect(corsConfigToYaml(cfg)).toBe(
      [
        "security:",
        "  cors:",
        "    allowedOrigins:",
        "      - https://dashboard.example.com",
        "      - http://localhost:25100",
        "    allowCredentials: true",
        "    allowPrivateNetwork: true",
        "    allowedMethods:",
        "      - GET",
        "      - POST",
        "    allowedHeaders:",
        "      - Content-Type",
        "    exposedHeaders:",
        "      - X-Request-Id",
        "    maxAge: 3600",
        "",
      ].join("\n"),
    );
  });

  it("quotes the wildcard origin so YAML does not read it as an alias", () => {
    const cfg: CorsConfig = { ...defaultCorsConfig(), allowedOrigins: ["*"] };
    expect(corsConfigToYaml(cfg)).toContain('      - "*"');
  });

  it("omits empty lists and the default maxAge", () => {
    const cfg: CorsConfig = {
      ...defaultCorsConfig(),
      allowedOrigins: ["https://dashboard.example.com"],
      maxAge: DEFAULT_CORS_MAX_AGE,
    };
    const yaml = corsConfigToYaml(cfg);
    expect(yaml).toContain("allowedOrigins:");
    expect(yaml).not.toContain("maxAge");
    expect(yaml).not.toContain("allowedMethods");
  });

  it("trims and drops blank entries", () => {
    const cfg: CorsConfig = {
      ...defaultCorsConfig(),
      allowedOrigins: ["  https://a.example.com  ", ""],
      allowedHeaders: ["   "],
    };
    const yaml = corsConfigToYaml(cfg);
    expect(yaml).toContain("      - https://a.example.com");
    expect(yaml).not.toContain("allowedHeaders");
  });
});

describe("probeCorsPolicy", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function mockFetch(headers: Record<string, string>, status = 204): typeof fetch {
    const h = new Headers();
    for (const [k, v] of Object.entries(headers)) h.set(k, v);
    return (async () =>
      ({ ok: status >= 200 && status < 300, status, headers: h }) as unknown as Response) as unknown as typeof fetch;
  }

  it("reads the effective policy headers off a 204 preflight", async () => {
    const fetchFn = mockFetch({
      "access-control-allow-origin": "https://dashboard.example.com",
      "access-control-allow-methods": "GET, POST",
      "access-control-max-age": "3600",
    });
    const probe = await probeCorsPolicy(fetchFn, () => "https://dashboard.example.com");
    expect(probe.ok).toBe(true);
    expect(probe.status).toBe(204);
    expect(probe.probedOrigin).toBe("https://dashboard.example.com");
    expect(probe.allowOrigin).toBe("https://dashboard.example.com");
    expect(probe.allowMethods).toBe("GET, POST");
    expect(probe.maxAge).toBe("3600");
    expect(probe.allowPrivateNetwork).toBeNull();
  });

  it("issues a same-origin OPTIONS with preflight request headers", async () => {
    const calls: { url: string; init?: RequestInit }[] = [];
    const fetchFn = (async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return { ok: true, status: 204, headers: new Headers() } as unknown as Response;
    }) as unknown as typeof fetch;
    await probeCorsPolicy(fetchFn, () => "http://localhost:25100");
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toBe("/v1/models");
    expect(calls[0].init?.method).toBe("OPTIONS");
    const headers = calls[0].init?.headers as Record<string, string>;
    expect(headers["Access-Control-Request-Method"]).toBe("POST");
  });

  it("surfaces fetch failures as a probe error", async () => {
    const fetchFn = (async () => {
      throw new Error("connection refused");
    }) as unknown as typeof fetch;
    const probe = await probeCorsPolicy(fetchFn, () => "http://localhost:25100");
    expect(probe.ok).toBe(false);
    expect(probe.error).toContain("connection refused");
  });
});

describe("describeEffectivePolicy", () => {
  const base: CorsProbeResult = {
    ok: true,
    status: 204,
    probedOrigin: "https://x.example.com",
    allowOrigin: null,
    allowCredentials: null,
    allowMethods: null,
    allowHeaders: null,
    exposeHeaders: null,
    maxAge: null,
    allowPrivateNetwork: null,
  };

  it("names the permissive, restricted and denied outcomes", () => {
    expect(describeEffectivePolicy({ ...base, allowOrigin: "*" })).toContain("permissive");
    expect(
      describeEffectivePolicy({ ...base, allowOrigin: "https://x.example.com" }),
    ).toContain("restricted");
    expect(describeEffectivePolicy({ ...base })).toContain("not allowed");
  });

  it("reports probe failures", () => {
    expect(describeEffectivePolicy({ ...base, ok: false, error: "boom" })).toContain("boom");
  });
});
