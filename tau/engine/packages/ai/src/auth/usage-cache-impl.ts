/**
 * In-memory usage cache implementation (AuthStorageUsageCache + entry parsing/racing helpers).
 *
 * Extracted verbatim from auth-storage.ts (surgical split 2026-09-14).
 * Re-exported through auth-storage.ts; import from there.
 */
import * as AIError from "../error";
import type { Provider } from "../types";
import type { StoredCredential } from "../auth-storage";
import type { AuthCredential, AuthCredentialStore } from "./storage-contract";
import type { UsageCache, UsageCacheEntry } from "./usage-metrics";

export const USAGE_CACHE_PREFIX = "usage_cache:";
export const USAGE_FORCE_REFRESH_CACHE_PREFIX = "force-refresh:";
export const USAGE_HEADER_INGEST_INTERVAL_MS = 60_000;
export const USAGE_LAST_GOOD_RETENTION_MS = 24 * 60 * 60_000;
/**
 * Per-credential cool-down after a usage fetch fails. While this window is
 * active we serve the last successful value to avoid dropping the credential
 * from the report; without a previous value we just return null and retry
 * on the next poll.
 */
export const USAGE_FAILURE_BACKOFF_MS = 10_000;
/**
 * A manual invalidation persists across the next CLI process and serializes
 * same-provider probes, avoiding a cold-account burst against IP-limited
 * upstream usage endpoints.
 */
export const USAGE_FORCE_REFRESH_TTL_MS = 5 * 60_000;
// Bumped from 3s — Claude usage retries up to 3 times with exponential backoff
// (~3.5s total worst case); a tight per-request budget aborts retries mid-cycle.
export const DEFAULT_USAGE_REQUEST_TIMEOUT_MS = 10_000;
export const USAGE_REPORT_CACHE_KEY_VERSION_OVERRIDES: Partial<Record<Provider, number>> = {
	"google-antigravity": 2,
	zai: 2,
	// v2: retires cached reports from the OMP-observed spend estimator (dollar
	// units) now that limits come from the upstream percent-based `/usage`
	// endpoint; the 24h last-good retention would otherwise keep serving them.
	"opencode-go": 2,
	// v2: cache identity gained an `org:` component so two subscriptions on one
	// account email stop sharing a slot. v3 retires parsed reports created before
	// Anthropic extra-usage rows existed; header ingestion can otherwise keep
	// renewing those incomplete reports throughout the 24h last-good retention.
	anthropic: 3,
};

export function parseUsageCacheEntry<T>(raw: string): UsageCacheEntry<T> | undefined {
	try {
		const parsed = JSON.parse(raw) as { value?: T; expiresAt?: unknown };
		const expiresAt = typeof parsed.expiresAt === "number" ? parsed.expiresAt : undefined;
		if (!expiresAt || !Number.isFinite(expiresAt)) return undefined;
		return { value: parsed.value as T, expiresAt };
	} catch {
		return undefined;
	}
}

/**
 * Race `promise` against `signal`, rejecting only this caller when the signal
 * fires. The underlying promise keeps running so other awaiters on the same
 * single-flight fetch aren't punished by a peer's cancel.
 */
export function raceUsageWithSignal<T>(promise: Promise<T>, signal: AbortSignal | undefined): Promise<T> {
	if (!signal) return promise;
	if (signal.aborted) return Promise.reject(new AIError.AbortError("usage fetch aborted"));
	return new Promise<T>((resolve, reject) => {
		const onAbort = (): void => {
			signal.removeEventListener("abort", onAbort);
			reject(new AIError.AbortError("usage fetch aborted"));
		};
		signal.addEventListener("abort", onAbort, { once: true });
		promise.then(
			value => {
				signal.removeEventListener("abort", onAbort);
				resolve(value);
			},
			err => {
				signal.removeEventListener("abort", onAbort);
				reject(err);
			},
		);
	});
}

export function raceCredentialRefreshWithSignal<T>(
	promise: Promise<T>,
	signal: AbortSignal | undefined,
	message = "credential refresh aborted",
): Promise<T> {
	if (!signal) return promise;
	if (signal.aborted) return Promise.reject(new AIError.AbortError(message));
	const abort = Promise.withResolvers<never>();
	const onAbort = (): void => abort.reject(new AIError.AbortError(message));
	signal.addEventListener("abort", onAbort, { once: true });
	return Promise.race([promise, abort.promise]).finally(() => {
		signal.removeEventListener("abort", onAbort);
	});
}

export function authCredentialEquals(left: AuthCredential, right: AuthCredential): boolean {
	if (left.type !== right.type) return false;
	if (left.type === "api_key") {
		return right.type === "api_key" && left.key === right.key;
	}
	if (right.type !== "oauth") return false;
	return (
		left.access === right.access &&
		left.refresh === right.refresh &&
		left.expires === right.expires &&
		left.accountId === right.accountId &&
		left.email === right.email &&
		left.projectId === right.projectId &&
		left.enterpriseUrl === right.enterpriseUrl
	);
}

export function storedCredentialArraysEqual(left: StoredCredential[], right: StoredCredential[]): boolean {
	if (left.length !== right.length) return false;
	for (let index = 0; index < left.length; index += 1) {
		const leftEntry = left[index];
		const rightEntry = right[index];
		if (!leftEntry || !rightEntry) return false;
		if (leftEntry.id !== rightEntry.id) return false;
		if (!authCredentialEquals(leftEntry.credential, rightEntry.credential)) return false;
	}
	return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// Usage Cache (backed by AuthCredentialStore)
// ─────────────────────────────────────────────────────────────────────────────

export class AuthStorageUsageCache implements UsageCache {
	constructor(private store: AuthCredentialStore) {}

	get<T>(key: string): UsageCacheEntry<T> | undefined {
		const raw = this.store.getCache(`${USAGE_CACHE_PREFIX}${key}`);
		if (!raw) return undefined;
		return parseUsageCacheEntry<T>(raw);
	}

	getStale<T>(key: string): UsageCacheEntry<T> | undefined {
		const raw = this.store.getCache(`${USAGE_CACHE_PREFIX}${key}`, {
			includeExpired: true,
		});
		if (!raw) return undefined;
		return parseUsageCacheEntry<T>(raw);
	}

	set<T>(key: string, entry: UsageCacheEntry<T>): void {
		const payload = JSON.stringify({
			value: entry.value,
			expiresAt: entry.expiresAt,
		});
		const durableExpiresAt =
			entry.value === null ? entry.expiresAt : Math.max(entry.expiresAt, Date.now() + USAGE_LAST_GOOD_RETENTION_MS);
		this.store.setCache(`${USAGE_CACHE_PREFIX}${key}`, payload, Math.floor(durableExpiresAt / 1000));
	}

	deletePrefix(prefix: string): boolean {
		if (!this.store.deleteCachePrefix) return false;
		this.store.deleteCachePrefix(`${USAGE_CACHE_PREFIX}${prefix}`);
		return true;
	}

	cleanup(): void {
		this.store.cleanExpiredCache();
	}
}
