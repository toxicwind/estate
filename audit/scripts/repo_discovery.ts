// GitHub Advanced Repo Discovery Engine
// Adaptive multi-strategy search with feature scoring
// Run: bun run audit/scripts/repo_discovery.ts [topic] [count]

interface RepoScore {
  name: string;
  stars: number;
  description: string;
  topics: string[];
  updated: string;
  hasRules: boolean;
  ruleCount: number;
  score: number;
  url: string;
}

interface SearchStrategy {
  name: string;
  query: string;
  weight: number;
}

const STRATEGIES: SearchStrategy[] = [
  { name: "ast-grep-rules", q: "ast-grep+rules+language:yaml", w: 1.0 },
  { name: "ast-grep-lints", q: "ast-grep+lint+language:typescript", w: 0.9 },
  { name: "ast-grep-convert", q: "ast-grep+convert+OR+migrate+OR+transform", w: 0.85 },
  { name: "ast-grep-codemod", q: "ast-grep+codemod+OR+refactor", w: 0.8 },
  { name: "ast-grep-patterns", q: "ast-grep+pattern+OR+snippet+OR+example", w: 0.7 },
  { name: "ast-grep-presets", q: "ast-grep+preset+OR+collection+OR+pack", w: 0.75 },
  { name: "ast-grep-config", q: "ast-grep+config+OR+sgconfig+OR+setup", w: 0.6 },
  { name: "ast-grep-bun", q: "ast-grep+bun+OR+nodejs+OR+typescript+rules", w: 0.65 },
  { name: "ast-grep-go", q: "ast-grep+go+OR+golang+rules", w: 0.55 },
  { name: "ast-grep-rust", q: "ast-grep+rust+rules+OR+convert", w: 0.5 },
  { name: "sgconfig-rules", q: "sgconfig+rules+ast-grep", w: 0.45 },
  { name: "ast-grep-mcp", q: "ast-grep+mcp+server+OR+tool", w: 0.4 },
];

async function searchGitHub(query: string, perPage: number): Promise<any[]> {
  const url = `https://api.github.com/search/repositories?q=${encodeURIComponent(query)}&sort=stars&order=desc&per_page=${perPage}`;
  const res = await fetch(url, {
    headers: { "Accept": "application/vnd.github.v3+json", "User-Agent": "sovereign-audit" },
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.items || [];
}

async function checkRulesRepo(fullName: string): Promise<{ hasRules: boolean; ruleCount: number }> {
  const contentsUrl = `https://api.github.com/repos/${fullName}/contents/`;
  const res = await fetch(contentsUrl, {
    headers: { "Accept": "application/vnd.github.v3+json", "User-Agent": "sovereign-audit" },
  });
  if (!res.ok) return { hasRules: false, ruleCount: 0 };
  const contents = await res.json();
  const ruleFiles = (contents as any[]).filter((f: any) =>
    f.name.endsWith(".yml") || f.name.endsWith(".yaml") ||
    f.name === "rules" || f.type === "dir" && f.name.includes("rule")
  );
  return { hasRules: ruleFiles.length > 0, ruleCount: ruleFiles.length };
}

function scoreRepo(repo: any, strategy: SearchStrategy, ruleInfo: RepoScore["hasRules"] | any): RepoScore {
  const stars = repo.stargazers_count || 0;
  const hasRules = ruleInfo?.hasRules || false;
  const ruleCount = ruleInfo?.ruleCount || 0;

  // Multi-feature scoring
  const starScore = Math.min(Math.log10(stars + 1) / 5, 1) * 30; // 0-30 points
  const ruleBonus = hasRules ? 25 : 0; // big bonus for having rules
  const ruleCountScore = Math.min(ruleCount * 2, 20); // 0-20 points
  const strategyWeight = strategy.w * 25; // 0-25 points

  const totalScore = starScore + ruleBonus + ruleCountScore + strategyWeight;

  return {
    name: repo.full_name,
    stars,
    description: repo.description || "",
    topics: repo.topics || [],
    updated: repo.updated_at || "",
    hasRules,
    ruleCount,
    score: Math.round(totalScore * 100) / 100,
    url: repo.html_url,
  };
}

async function main() {
  const topic = process.argv[2] || "ast-grep";
  const targetCount = parseInt(process.argv[3] || "8");

  console.log(`=== ADAPTIVE REPO DISCOVERY: "${topic}" ===\n`);
  console.log(`Target: ${targetCount} repos | Strategies: ${STRATEGIES.length}`);

  const allRepos = new Map<string, RepoScore>();
  const seenNames = new Set<string>();

  for (const strategy of STRATEGIES) {
    if (allRepos.size >= targetCount * 3) break; // Get extras for dedup

    console.log(`\n▶ Strategy: ${strategy.name} (weight: ${strategy.w})`);
    const items = await searchGitHub(strategy.q, 15);

    for (const item of items) {
      if (seenNames.has(item.full_name)) continue;
      seenNames.add(item.full_name);

      // Check if it actually has rules
      const ruleInfo = await checkRulesRepo(item.full_name);
      const scored = scoreRepo(item, strategy, ruleInfo);
      allRepos.set(item.full_name, scored);

      console.log(`  + ${item.full_name} (score: ${scored.score}, stars: ${scored.stars}, rules: ${ruleInfo.hasRules})`);
    }
  }

  // Sort by score descending
  const sorted = [...allRepos.values()].sort((a, b) => b.score - a.score);
  const top = sorted.slice(0, targetCount);

  console.log(`\n=== TOP ${targetCount} REPOS (scored) ===\n`);
  top.forEach((r, i) => {
    console.log(`${i + 1}. ${r.name}`);
    console.log(`   Score: ${r.score} | Stars: ${r.stars} | Rules: ${r.hasRules} (${r.ruleCount})`);
    console.log(`   URL: ${r.url}`);
    console.log(`   ${r.description?.slice(0, 80) || "No description"}`);
    console.log("");
  });

  // Save results
  const output = {
    topic,
    targetCount,
    strategies: STRATEGIES.length,
    totalFound: allRepos.size,
    top,
    all: sorted,
  };
  await Bun.write(
    `/home/toxic/sovereign/audit/discovery_${topic.replace(/[^a-z0-9]/gi, "_")}.json`,
    JSON.stringify(output, null, 2)
  );
  console.log(`Saved to audit/discovery_${topic.replace(/[^a-z0-9]/gi, "_")}.json`);
}

main();
