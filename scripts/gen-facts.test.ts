// sync test — the backstop. Byte-diffs a fresh generation against the
// checked-in README; failure message names the fix (skill: generated-facts-backstop).
import { expect, test } from "bun:test";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { syncFacts } from "./gen-facts";

test("checked-in FACTS block matches a fresh generation", async () => {
	const dir = await mkdtemp(join(tmpdir(), "pens-facts-"));
	try {
		const tmp = join(dir, "README.md");
		await writeFile(tmp, await readFile(join(import.meta.dir, "..", "README.md"), "utf8"));
		syncFacts(tmp);
		expect(await readFile(tmp, "utf8")).toBe(await readFile(join(import.meta.dir, "..", "README.md"), "utf8"));
	} finally {
		await rm(dir, { recursive: true, force: true });
	}
});
