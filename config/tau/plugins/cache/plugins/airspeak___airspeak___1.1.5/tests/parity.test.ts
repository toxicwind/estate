// Parity test (SC-002): the packaged checks MUST produce the exact issue
// lists captured in baseline.json before any behavior changes were made.
// Any rule drift breaks this test.
import { describe, expect, test } from "bun:test";
import { loadBaseline, loadCorpus, runChecks } from "./helpers.ts";

const baseline = loadBaseline();
const corpus = loadCorpus();

for (const family of Object.keys(corpus.en)) {
  describe(`parity: en.${family}`, () => {
    test("violating matches baseline exactly", () => {
      const samples = corpus.en[family];
      expect(runChecks("en", samples.violating)).toEqual(baseline.en[family].violating);
    });
    test("conforming stays silent", () => {
      const samples = corpus.en[family];
      expect(runChecks("en", samples.conforming)).toEqual(baseline.en[family].conforming);
    });
  });
}
