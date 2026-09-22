#!/usr/bin/env bun
/**
 * doc-graph-builder.ts — Autonomous Documentation Knowledge Graph & Deeplink Generator
 * 
 * Pattern Borrow:
 * - Graph-based Agent Memory (arXiv:2602.05665): Relational dependencies & hierarchical retrieval.
 * - Adaptive Knowledge Graph Exploration (arXiv:2601.13969): Multi-hop permalink indexing.
 */

import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, relative, basename, resolve } from "node:path";

export interface DocNode {
  path: string;
  filename: string;
  title: string;
  category: string;
  tags: string[];
  links: string[];
  sizeBytes: number;
}

export interface DocGraph {
  nodes: Record<string, DocNode>;
  categories: Record<string, string[]>;
  tagIndex: Record<string, string[]>;
  totalFiles: number;
  generatedAt: string;
}

const SCRIPT_DIR = import.meta.dir;
const DOCS_ROOT = process.env.SOVEREIGN_DOCS_ROOT || resolve(SCRIPT_DIR, "..", "docs");

export function buildDocumentationGraph(): DocGraph {
  const nodes: Record<string, DocNode> = {};
  const categories: Record<string, string[]> = {};
  const tagIndex: Record<string, string[]> = {};

  function scanDir(dir: string) {
    const entries = readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!entry.name.startsWith(".")) {
          scanDir(fullPath);
        }
      } else if (entry.isFile() && entry.name.endsWith(".md")) {
        const relPath = relative(DOCS_ROOT, fullPath);
        if (relPath === "README.md" || relPath === "README-INDEX.md") continue;

        const content = readFileSync(fullPath, "utf8");
        const titleMatch = content.match(/^#\s+(.+)$/m);
        const title = titleMatch ? titleMatch[1].trim() : entry.name;
        
        // Extract category from folder structure
        const parts = relPath.split("/");
        const category = parts.length > 1 ? parts[0] : "general";

        // Extract markdown links
        const linkMatches = [...content.matchAll(/\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)/g)];
        const links = linkMatches.map(m => m[2]);

        // Extract hashtags / category tags
        const inferredTags: string[] = [category];
        if (parts.length > 2) inferredTags.push(parts[1]);
        if (content.toLowerCase().includes("pitchfork")) inferredTags.push("pitchfork");
        if (content.toLowerCase().includes("port")) inferredTags.push("ports");
        if (content.toLowerCase().includes("mcp")) inferredTags.push("mcp");
        if (content.toLowerCase().includes("audit")) inferredTags.push("audit");
        if (content.toLowerCase().includes("router")) inferredTags.push("router");

        const node: DocNode = {
          path: relPath,
          filename: entry.name,
          title,
          category,
          tags: [...new Set(inferredTags)],
          links,
          sizeBytes: statSync(fullPath).size,
        };

        nodes[relPath] = node;

        if (!categories[category]) categories[category] = [];
        categories[category].push(relPath);

        for (const tag of node.tags) {
          if (!tagIndex[tag]) tagIndex[tag] = [];
          tagIndex[tag].push(relPath);
        }
      }
    }
  }

  scanDir(DOCS_ROOT);

  const graph: DocGraph = {
    nodes,
    categories,
    tagIndex,
    totalFiles: Object.keys(nodes).length,
    generatedAt: new Date().toISOString(),
  };

  return graph;
}

// Generate markdown graph index
export function renderMarkdownIndex(graph: DocGraph): string {
  const lines: string[] = [
    "# Sovereign Documentation Knowledge Graph (11ty-Style Collections Index)",
    "",
    `> **Automated Relational Knowledge Graph** generated on \`${graph.generatedAt}\` across **${graph.totalFiles} modular documents** in \`sovereign/docs/\`.`,
    "",
    "## Tagged Collections Index",
    "",
    "| Tag / Collection | Document Count | Deep Permalinks |",
    "|---|---|---|",
  ];

  for (const [tag, docList] of Object.entries(graph.tagIndex).sort((a, b) => b[1].length - a[1].length)) {
    const samples = docList.slice(0, 4).map(p => {
      return `[\`${basename(p)}\`](${p})`;
    }).join(" · ");
    const extra = docList.length > 4 ? ` *(+${docList.length - 4} more)*` : "";
    lines.push(`| **\`#${tag}\`** | ${docList.length} | ${samples}${extra} |`);
  }

  lines.push("", "## Relational Category Hierarchy", "");

  for (const [cat, docList] of Object.entries(graph.categories).sort()) {
    lines.push(`### 📁 \`${cat}/\``, "");
    for (const docPath of docList.sort()) {
      const node = graph.nodes[docPath];
      const linkInfo = node.links.length > 0 ? ` ── *(${node.links.length} outgoing links)*` : "";
      lines.push(`- **[${node.title}](${docPath})** \`(${node.path})\`${linkInfo}`);
    }
    lines.push("");
  }

  return lines.join("\n");
}

if (import.meta.main) {
  console.log("== Building Sovereign Documentation Knowledge Graph ==");
  const graph = buildDocumentationGraph();
  const graphPath = join(DOCS_ROOT, "DOCS_GRAPH.json");
  writeFileSync(graphPath, JSON.stringify(graph, null, 2), "utf8");
  console.log(`✓ Generated ${graphPath} (${graph.totalFiles} documents indexed)`);

  const indexMd = renderMarkdownIndex(graph);
  const indexMdPath = join(DOCS_ROOT, "README-INDEX.md");
  writeFileSync(indexMdPath, indexMd, "utf8");
  console.log(`✓ Updated ${indexMdPath}`);
}
