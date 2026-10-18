import { describe, test, expect } from "bun:test";

describe("Estate Core Stack Verification", () => {
  test("Cuttinggate (:25200) health and live catalog", async () => {
    const res = await fetch("http://127.0.0.1:25200/health");
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.ok).toBe(true);
  });

  test("Herd (:25100) engine endpoint", async () => {
    const res = await fetch("http://127.0.0.1:25100/health");
    expect(res.status).toBe(200);
    const text = await res.text();
    expect(text.trim()).toBe("OK");
  });

  test("Hodos (:25193) engine endpoint", async () => {
    const res = await fetch("http://127.0.0.1:25193/health");
    expect(res.status).toBe(200);
    const text = await res.text();
    expect(text.trim()).toBe("ok");
  });

  test("Gatehouse (:25127) health check", async () => {
    const res = await fetch("http://127.0.0.1:25127/health");
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.status).toBe("ok");
  });

  test("Keeper CDP (:9223) version info", async () => {
    const res = await fetch("http://127.0.0.1:9223/json/version");
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.Browser).toBeDefined();
    expect(data.Browser).toContain("Chrome");
  });
});
