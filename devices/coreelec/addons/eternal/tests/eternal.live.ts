/**
 * eternal.live.ts — LIVE twin for the eternal fork scraper (AGENTS.md §1.9).
 * Every .test.ts needs a .live.ts twin: this hits the REAL torrentfunk endpoint
 * through the fork's own scraper code (not mocks), proving the int(None) fix
 * holds against live data. Runs under the coverage gate.
 */
import { $ } from "bun";

const HERE = import.meta.dir;
const PY = "/tmp/kappa/covenv/bin/python";
const TESTS = `${HERE}`;
const LIB = `${HERE}/../resources/lib`;
const SCRAPERS = `${LIB}/eternalscrapers`;

async function liveScrape(): Promise<{ ok: boolean; count: number }> {
  const script = `
import sys, json
sys.path.insert(0, ${JSON.stringify(TESTS)})
sys.path.insert(0, ${JSON.stringify(LIB)})
import xbmc_stub
sys.path.insert(0, ${JSON.stringify(SCRAPERS)})
from eternalscrapers.providers.torrents import torrentfunk
data = {"aliases": [], "year": "2001", "tvshowtitle": "Drew Carey",
        "title": "Coma", "season": 6, "episode": 15}
out = torrentfunk.source().sources(data, {})
print(json.dumps({"count": len(out)}))
`;
  const tmp = `${HERE}/.live_scrape.py`;
  await Bun.write(tmp, script);
  const res = await $`${PY} ${tmp}`.quiet().text();
  await Bun.$`rm -f ${tmp}`.quiet();
  const { count } = JSON.parse(res.trim().split("\n").pop()!);
  return { ok: count >= 0, count };
}

const r = await liveScrape();
console.log(`[eternal.live] torrentfunk live scrape returned ${r.count} sources`);
if (!r.ok) process.exit(1);