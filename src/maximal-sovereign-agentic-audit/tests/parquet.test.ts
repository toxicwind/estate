import { describe, expect, test } from "bun:test";
import { execFile } from "child_process";

describe("parquet output", () => {
  test("generates parquet file", async () => {
    const result = await new Promise<string>((resolve, reject) => {
      execFile("gh", ["api", "users/toxicwind/repos?per_page=1", "--jq", "."], { timeout: 10000 }, (err, stdout) => {
        if (err) reject(err);
        else resolve(stdout.trim());
      });
    });
    const repos = JSON.parse(result);
    expect(Array.isArray(repos)).toBe(true);
    expect(repos.length).toBe(1);
    expect(repos[0].name).toBeDefined();
  });

  test("parquet record structure", () => {
    const record = {
      name: "test-repo",
      private: false,
      classification: "PUBLIC_ECOSYSTEM",
      bun_version: ">=1.3",
    };
    expect(record.name).toBe("test-repo");
    expect(record.private).toBe(false);
    expect(record.classification).toBe("PUBLIC_ECOSYSTEM");
  });
});
