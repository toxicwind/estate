/**
 * sessions.ts — In-memory LRU session store for multi-turn cascade conversations.
 *
 * Stores cascadeId → session metadata with LRU eviction at MAX_SESSIONS.
 * Exposed as a shared module used by both chat/completions and DELETE /v1/chat/sessions/:id.
 */

export interface SessionEntry {
  cascadeId: string;
  model: string;
  createdAt: number;
  lastUsedAt: number;
  turnCount: number;
}

const MAX_SESSIONS = 100;

// Map preserves insertion order; we re-insert on access to implement LRU.
const store = new Map<string, SessionEntry>();

/** Insert or update a session, evicting LRU if at capacity. */
export function upsertSession(cascadeId: string, model: string): SessionEntry {
  const now = Date.now();

  // Re-insert to update LRU order
  if (store.has(cascadeId)) {
    const existing = store.get(cascadeId)!;
    store.delete(cascadeId);
    const updated: SessionEntry = {
      ...existing,
      lastUsedAt: now,
      turnCount: existing.turnCount + 1,
    };
    store.set(cascadeId, updated);
    return updated;
  }

  // Evict oldest entry if at capacity
  if (store.size >= MAX_SESSIONS) {
    const oldest = store.keys().next().value;
    if (oldest !== undefined) {
      process.stderr.write(`[sessions] LRU evict cascadeId=${oldest}\n`);
      store.delete(oldest);
    }
  }

  const entry: SessionEntry = {
    cascadeId,
    model,
    createdAt: now,
    lastUsedAt: now,
    turnCount: 1,
  };
  store.set(cascadeId, entry);
  return entry;
}

/** Touch an existing session to update LRU order and lastUsedAt. */
export function touchSession(cascadeId: string): SessionEntry | null {
  const entry = store.get(cascadeId);
  if (!entry) return null;
  return upsertSession(cascadeId, entry.model);
}

/** Retrieve session metadata without updating LRU order. */
export function getSession(cascadeId: string): SessionEntry | null {
  return store.get(cascadeId) ?? null;
}

/** Remove a session from the store. Returns true if it existed. */
export function deleteSession(cascadeId: string): boolean {
  return store.delete(cascadeId);
}

/** Return all sessions (for health/debug). */
export function listSessions(): SessionEntry[] {
  return Array.from(store.values());
}

/** Return session count. */
export function sessionCount(): number {
  return store.size;
}
