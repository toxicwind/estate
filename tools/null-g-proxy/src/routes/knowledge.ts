/**
 * knowledge.ts — Knowledge Base routes.
 *
 * GET  /v1/knowledge/list        → list knowledge items
 * GET  /v1/knowledge/search?q=   → full-text search
 * POST /v1/knowledge/items       → create new knowledge item
 */

import { Hono } from 'hono';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';

const log = (msg: string) => process.stderr.write(`[knowledge] ${msg}\n`);

const KNOWLEDGE_DIR = path.join(os.homedir(), '.gemini', 'antigravity', 'knowledge');

export const knowledgeRoutes = new Hono();

// ─── Helpers ──────────────────────────────────────────────────────────────────

interface KnowledgeItem {
  name: string;
  filename: string;
  path: string;
  size: number;
  createdAt: number;
  modifiedAt: number;
  preview: string;
}

function ensureKnowledgeDir(): void {
  if (!fs.existsSync(KNOWLEDGE_DIR)) {
    fs.mkdirSync(KNOWLEDGE_DIR, { recursive: true });
  }
}

function readKnowledgeItems(): KnowledgeItem[] {
  ensureKnowledgeDir();

  let files: fs.Dirent[];
  try {
    files = fs.readdirSync(KNOWLEDGE_DIR, { withFileTypes: true });
  } catch {
    return [];
  }

  const items: KnowledgeItem[] = [];

  for (const file of files) {
    if (!file.isFile()) continue;

    const filePath = path.join(KNOWLEDGE_DIR, file.name);
    let stat: fs.Stats;
    try {
      stat = fs.statSync(filePath);
    } catch {
      continue;
    }

    let preview = '';
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      preview = content.slice(0, 200).replace(/\n/g, ' ').trim();
    } catch {
      // skip unreadable
    }

    items.push({
      name: path.basename(file.name, path.extname(file.name)),
      filename: file.name,
      path: filePath,
      size: stat.size,
      createdAt: Math.floor(stat.birthtimeMs / 1000),
      modifiedAt: Math.floor(stat.mtimeMs / 1000),
      preview,
    });
  }

  return items.sort((a, b) => b.modifiedAt - a.modifiedAt);
}

// ─── GET /v1/knowledge/list ───────────────────────────────────────────────────

knowledgeRoutes.get('/list', (c) => {
  const items = readKnowledgeItems();
  log(`list returning ${items.length} items from ${KNOWLEDGE_DIR}`);
  return c.json({
    items,
    total: items.length,
    directory: KNOWLEDGE_DIR,
  });
});

// ─── GET /v1/knowledge/search ─────────────────────────────────────────────────

knowledgeRoutes.get('/search', (c) => {
  const query = c.req.query('q')?.trim();
  if (!query) {
    return c.json(
      { error: { message: '`q` query parameter is required', type: 'invalid_request_error' } },
      400,
    );
  }

  const items = readKnowledgeItems();
  const queryLower = query.toLowerCase();

  const results: Array<KnowledgeItem & { content: string; matches: number }> = [];

  for (const item of items) {
    let content = '';
    try {
      content = fs.readFileSync(item.path, 'utf8');
    } catch {
      continue;
    }

    const contentLower = content.toLowerCase();
    const nameLower = item.name.toLowerCase();

    // Count occurrences
    let matches = 0;
    let idx = 0;
    while ((idx = contentLower.indexOf(queryLower, idx)) !== -1) {
      matches++;
      idx += queryLower.length;
    }
    if (nameLower.includes(queryLower)) matches += 5; // name match weighted higher

    if (matches > 0) {
      results.push({ ...item, content, matches });
    }
  }

  // Sort by match count descending
  results.sort((a, b) => b.matches - a.matches);

  log(`search q="${query}" found ${results.length} results`);
  return c.json({
    query,
    results: results.map(({ matches, ...r }) => ({ ...r, relevance: matches })),
    total: results.length,
  });
});

// ─── POST /v1/knowledge/items ─────────────────────────────────────────────────

interface CreateKnowledgeRequest {
  name: string;
  content: string;
  projectDir?: string;
}

knowledgeRoutes.post('/items', async (c) => {
  let body: CreateKnowledgeRequest;
  try {
    body = await c.req.json<CreateKnowledgeRequest>();
  } catch {
    return c.json(
      { error: { message: 'Invalid JSON body', type: 'invalid_request_error' } },
      400,
    );
  }

  if (!body.name || !body.content) {
    return c.json(
      { error: { message: '`name` and `content` are required', type: 'invalid_request_error' } },
      400,
    );
  }

  // Sanitize filename: allow alphanumeric, dash, underscore, space, dot
  const safeName = body.name.replace(/[^a-zA-Z0-9\-_ .]/g, '_').trim();
  if (!safeName) {
    return c.json(
      { error: { message: 'Invalid knowledge item name', type: 'invalid_request_error' } },
      400,
    );
  }

  // Determine target directory (project-local or global)
  let targetDir = KNOWLEDGE_DIR;
  if (body.projectDir) {
    const projectKnowledge = path.join(body.projectDir, '.antigravity', 'knowledge');
    targetDir = projectKnowledge;
  }

  ensureKnowledgeDir();

  try {
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
  } catch (e) {
    return c.json(
      {
        error: {
          message: `Failed to create knowledge directory: ${e instanceof Error ? e.message : String(e)}`,
          type: 'server_error',
        },
      },
      500,
    );
  }

  const filename = safeName.endsWith('.md') ? safeName : `${safeName}.md`;
  const filePath = path.join(targetDir, filename);

  // Prevent overwrite without explicit flag
  if (fs.existsSync(filePath)) {
    return c.json(
      {
        error: {
          message: `Knowledge item "${filename}" already exists. Use a different name.`,
          type: 'conflict',
          code: 'already_exists',
        },
      },
      409,
    );
  }

  try {
    fs.writeFileSync(filePath, body.content, 'utf8');
  } catch (e) {
    return c.json(
      {
        error: {
          message: `Failed to write knowledge item: ${e instanceof Error ? e.message : String(e)}`,
          type: 'server_error',
        },
      },
      500,
    );
  }

  const stat = fs.statSync(filePath);
  log(`created knowledge item "${filename}" at ${filePath}`);

  return c.json(
    {
      name: safeName,
      filename,
      path: filePath,
      size: stat.size,
      createdAt: Math.floor(stat.birthtimeMs / 1000),
      modifiedAt: Math.floor(stat.mtimeMs / 1000),
    },
    201,
  );
});
