/**
 * Userscript metadata block parser.
 * Parses // ==UserScript== ... // ==/UserScript== blocks.
 */

export interface UserscriptMeta {
  name: string;
  namespace?: string;
  version: string;
  description?: string;
  author?: string;
  match: string[];
  excludeMatch?: string[];
  include?: string[];
  exclude?: string[];
  require?: string[];
  grant: string[];
  runAt?: 'document-start' | 'document-body' | 'document-end' | 'document-idle';
  noframes?: boolean;
  unwrap?: boolean;
  connect?: string[];
  [key: string]: any;
}

const KNOWN_KEYS = new Set([
  'name', 'namespace', 'version', 'description', 'author',
  'match', 'excludeMatch', 'include', 'exclude',
  'require', 'grant', 'runAt', 'noframes', 'unwrap', 'connect',
  'license', 'icon', 'icon64', 'iconURL', 'defaulticon', 'updateURL', 'downloadURL'
]);

export function parseMetadata(source: string): UserscriptMeta | null {
  const lines = source.split('\n');
  const metaLines: string[] = [];
  let inBlock = false;
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed === '// ==UserScript==') {
      inBlock = true;
      continue;
    }
    if (trimmed === '// ==/UserScript==') {
      inBlock = false;
      break;
    }
    if (inBlock) {
      metaLines.push(trimmed);
    }
  }
  
  if (metaLines.length === 0) return null;
  
  const meta: Partial<UserscriptMeta> = {
    match: [],
    grant: [],
    require: [],
    connect: [],
    excludeMatch: [],
    include: [],
    exclude: []
  };
  
  for (const line of metaLines) {
    if (!line.startsWith('@')) continue;
    
    const [key, ...rest] = line.slice(1).split(/\s+/);
    const value = rest.join(' ').trim();
    
    if (!key) continue;
    
    const normalizedKey = key.toLowerCase().replace(/-/g, '');
    
    switch (normalizedKey) {
      case 'name':
        meta.name = value;
        break;
      case 'namespace':
        meta.namespace = value;
        break;
      case 'version':
        meta.version = value;
        break;
      case 'description':
        meta.description = value;
        break;
      case 'author':
        meta.author = value;
        break;
      case 'match':
        meta.match.push(value);
        break;
      case 'excludematch':
        meta.excludeMatch.push(value);
        break;
      case 'include':
        meta.include.push(value);
        break;
      case 'exclude':
        meta.exclude.push(value);
        break;
      case 'require':
        meta.require.push(value);
        break;
      case 'grant':
        meta.grant.push(value);
        break;
      case 'runat':
        meta.runAt = value as any;
        break;
      case 'noframes':
        meta.noframes = true;
        break;
      case 'unwrap':
        meta.unwrap = true;
        break;
      case 'connect':
        meta.connect.push(value);
        break;
      default:
        meta[key] = value;
        break;
    }
  }
  
  if (!meta.name || !meta.version) return null;
  
  return meta as UserscriptMeta;
}

export function extractMetadata(source: string): { meta: UserscriptMeta | null; code: string } {
  const meta = parseMetadata(source);
  if (!meta) return { meta: null, code: source };
  
  // Remove the metadata block from the source
  const lines = source.split('\n');
  const codeLines: string[] = [];
  let inBlock = false;
  let blockEnded = false;
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed === '// ==UserScript==') {
      inBlock = true;
      continue;
    }
    if (trimmed === '// ==/UserScript==') {
      inBlock = false;
      blockEnded = true;
      continue;
    }
    if (!inBlock && blockEnded) {
      codeLines.push(line);
    } else if (!inBlock && !blockEnded) {
      // Before metadata block (shebang, etc.)
      codeLines.push(line);
    }
  }
  
  return { meta, code: codeLines.join('\n') };
}