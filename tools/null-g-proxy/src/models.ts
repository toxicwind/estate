/**
 * models.ts — Model registry and bidirectional name mapping.
 *
 * Supports both Antigravity internal IDs (MODEL_PLACEHOLDER_M37) and
 * human-readable OpenAI-compatible names (antigravity/gemini-3.1-pro-high).
 */

export interface ModelDef {
  /** Internal Antigravity enum ID (protobuf integer) */
  internalId: number;
  /** Antigravity string enum name (e.g. MODEL_PLACEHOLDER_M37) */
  enumName: string;
  /** OpenAI-compatible model name (e.g. antigravity/gemini-3.1-pro-high) */
  openaiName: string;
  /** Human-readable display name */
  displayName: string;
  /** Max poll timeout for this model in ms */
  timeoutMs: number;
}

/** All known models */
export const MODEL_LIST: ModelDef[] = [
  {
    internalId: 1037,
    enumName: 'MODEL_PLACEHOLDER_M37',
    openaiName: 'antigravity/gemini-3.1-pro-high',
    displayName: 'Gemini 3.1 Pro (High)',
    timeoutMs: 120_000,
  },
  {
    internalId: 1036,
    enumName: 'MODEL_PLACEHOLDER_M36',
    openaiName: 'antigravity/gemini-3.1-pro-low',
    displayName: 'Gemini 3.1 Pro (Low)',
    timeoutMs: 90_000,
  },
  {
    internalId: 1018,
    enumName: 'MODEL_PLACEHOLDER_M18',
    openaiName: 'antigravity/gemini-3-flash',
    displayName: 'Gemini 3 Flash',
    timeoutMs: 60_000,
  },
  {
    internalId: 1035,
    enumName: 'MODEL_PLACEHOLDER_M35',
    openaiName: 'antigravity/claude-sonnet-4.6-thinking',
    displayName: 'Claude Sonnet 4.6 (Thinking)',
    timeoutMs: 180_000,
  },
  {
    internalId: 1026,
    enumName: 'MODEL_PLACEHOLDER_M26',
    openaiName: 'antigravity/claude-opus-4.6-thinking',
    displayName: 'Claude Opus 4.6 (Thinking)',
    timeoutMs: 300_000,
  },
  {
    internalId: 1014,
    enumName: 'MODEL_OPENAI_GPT_OSS_120B_MEDIUM',
    openaiName: 'antigravity/gpt-oss-120b',
    displayName: 'GPT OSS 120B Medium',
    timeoutMs: 120_000,
  },
];

/** Default model to use when none is specified */
export const DEFAULT_MODEL = MODEL_LIST[0]!;

// Build lookup indexes
const byOpenaiName = new Map<string, ModelDef>(MODEL_LIST.map((m) => [m.openaiName, m]));
const byEnumName   = new Map<string, ModelDef>(MODEL_LIST.map((m) => [m.enumName, m]));
const byId         = new Map<number, ModelDef>(MODEL_LIST.map((m) => [m.internalId, m]));

/**
 * Resolve a model from any of:
 * - OpenAI-compatible name (antigravity/gemini-3-flash)
 * - Antigravity enum name (MODEL_PLACEHOLDER_M18)
 * - Numeric internal ID
 *
 * Returns DEFAULT_MODEL if not found.
 */
export function resolveModel(input: string | number | undefined): ModelDef {
  if (!input) return DEFAULT_MODEL;

  if (typeof input === 'number') {
    return byId.get(input) ?? DEFAULT_MODEL;
  }

  // Try exact OpenAI name
  const byOpenai = byOpenaiName.get(input);
  if (byOpenai) return byOpenai;

  // Try exact enum name
  const byEnum = byEnumName.get(input);
  if (byEnum) return byEnum;

  // Try case-insensitive / partial match on openaiName
  const lower = input.toLowerCase();
  for (const m of MODEL_LIST) {
    if (m.openaiName.toLowerCase().includes(lower)) return m;
    if (m.displayName.toLowerCase().includes(lower)) return m;
  }

  process.stderr.write(`[proxy] Unknown model "${input}", using default\n`);
  return DEFAULT_MODEL;
}

/**
 * Build the OpenAI /v1/models response body.
 */
export function buildModelsResponse(): object {
  const now = Math.floor(Date.now() / 1000);
  return {
    object: 'list',
    data: MODEL_LIST.map((m) => ({
      id: m.openaiName,
      object: 'model',
      created: now,
      owned_by: 'antigravity',
      permission: [],
      root: m.openaiName,
      parent: null,
    })),
  };
}
