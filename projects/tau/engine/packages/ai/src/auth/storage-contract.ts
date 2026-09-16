/**
 * Credential and storage contract types (ApiKeyCredential, OAuthCredential, AuthCredentialStore, AuthStorageOptions, ...).
 *
 * Extracted verbatim from auth-storage.ts (surgical split 2026-09-14).
 * Re-exported through auth-storage.ts; import from there.
 */
import type { OAuthCredentials } from "../registry/oauth/types";
import type { Provider } from "../types";
import type { ClientUsageIdentity, ClientUsageReport, ClientUsageSummary, CredentialRankingStrategy, ObservedUsageEntry, UsageHistoryEntry, UsageHistoryQuery, UsageLogger, UsageProvider, UsageReport } from "../usage";

export type ApiKeyCredential = {
	type: "api_key";
	key: string;
	source?: "login";
};

export type OAuthCredential = {
	type: "oauth";
} & OAuthCredentials;

export type AuthCredential = ApiKeyCredential | OAuthCredential;

export type AuthCredentialEntry = AuthCredential | AuthCredential[];

export type AuthStorageData = Record<string, AuthCredentialEntry>;

/**
 * Cascade leg that supplies a provider's active credential, highest precedence
 * first — mirrors {@link AuthStorage.getApiKey}'s resolution order.
 */
export type CredentialOriginKind = "runtime" | "config" | "oauth" | "api_key" | "env" | "fallback";

/**
 * Structured provenance for a provider's auth, for UI that needs a machine
 * tag (the `/login` provider list) rather than the prose of
 * {@link AuthStorage.describeCredentialSource}.
 */
export interface CredentialOrigin {
	kind: CredentialOriginKind;
	/** Env var name when `kind === "env"` and a single named variable backs it. */
	envVar?: string;
}

/**
 * Serialized representation of AuthStorage for passing to subagent workers.
 * Contains only the essential credential data, not runtime state.
 */
export interface SerializedAuthStorage {
	credentials: Record<
		string,
		Array<{
			id: number;
			type: "api_key" | "oauth";
			data: Record<string, unknown>;
		}>
	>;
	runtimeOverrides?: Record<string, string>;
	dbPath?: string;
}

/**
 * Auth credential with database row ID for updates/deletes.
 * Wraps AuthCredential with storage metadata.
 */
export interface StoredAuthCredential {
	id: number;
	provider: string;
	credential: AuthCredential;
	disabledCause: string | null;
}

/** One persisted rate-limit block: credential row id + provider-type key + optional scope. */
export interface StoredCredentialBlock {
	/** SQLite row id of the credential (auth_credentials.id). */
	credentialId: number;
	/** `${provider}:${credentialType}` — same value as AuthStorage's in-memory providerKey. */
	providerKey: string;
	/** Block scope (e.g. "tier:fable"); empty string = unscoped. Never NUL-delimited. */
	blockScope: string;
	/** Epoch milliseconds. */
	blockedUntilMs: number;
	/** Last row update timestamp in epoch milliseconds, when provided by the backing store. */
	updatedAtMs?: number;
}

/**
 * Identity slice of a disabled (soft-deleted) credential tombstone — cause and
 * account identity only, never token material. Surfaced so auto-disabled
 * accounts (e.g. an expired Anthropic OAuth grant) stay visible in `omp usage`
 * instead of silently vanishing until the user notices missing quota.
 */
export interface DisabledCredentialSummary {
	/** Database row id (matches {@link StoredAuthCredential.id}). */
	id: number;
	provider: string;
	type: AuthCredential["type"];
	email?: string;
	accountId?: string;
	/** Organization/workspace the credential was scoped to (Anthropic/ChatGPT multi-subscription). */
	orgId?: string;
	orgName?: string;
	/** Verbatim disable cause captured when the row was torn down. */
	cause: string;
	/** Epoch ms the row was disabled (SQLite `updated_at`), when known. */
	disabledAtMs?: number;
}

/**
 * Per-credential health record returned by {@link AuthStorage.checkCredentials}.
 *
 * Use this to identify which credential in a multi-account pool is causing
 * auth errors. `ok` is tri-state:
 *
 * - `true` — credential authenticated against the provider's auth-verifying
 *   probe (today: the usage endpoint). For OAuth this also exercises refresh
 *   when the access token was expired.
 * - `false` — the probe rejected the credential (401/403/refresh failure/etc).
 *   `reason` carries the upstream error string.
 * - `null` — no probe is configured for this provider (or the configured
 *   probe doesn't support this credential type). The credential's auth
 *   status is unverifiable from here.
 */
export interface CredentialHealthResult {
	/** Database row id (matches {@link StoredAuthCredential.id}). */
	id: number;
	provider: string;
	type: AuthCredential["type"];
	/** OAuth email if known on the stored credential or surfaced by the probe. */
	email?: string;
	/** OAuth account id if known. */
	accountId?: string;
	/** Organization/workspace the credential is scoped to (Anthropic/ChatGPT multi-subscription). */
	orgId?: string;
	orgName?: string;
	/** `true` when the refresh token lives on a remote broker (sentinel was present). */
	remoteRefresh?: true;
	ok: boolean | null;
	/** Failure / unverifiable reason; absent when `ok === true`. */
	reason?: string;
	/** Probe usage report (raw payload stripped) when `ok === true`. */
	report?: Omit<UsageReport, "raw">;
	/**
	 * Result of the optional end-to-end completion probe (see
	 * {@link CheckCredentialsOptions.completionProbe}). Absent when no probe was
	 * supplied. The completion probe exercises the provider's chat-completion
	 * endpoint with the credential's bearer bytes, which is a stricter signal
	 * than the usage endpoint (some providers happily 200 a `/usage` call while
	 * the chat endpoint 401s the same bearer).
	 */
	completion?: CredentialCompletionResult;
}

/**
 * Outcome of the end-to-end completion probe. `null` means the probe was
 * skipped (no bearer bytes were available — e.g. OAuth refresh failed
 * upstream of the probe).
 */
export interface CredentialCompletionResult {
	ok: boolean | null;
	/** Failure / unverifiable reason; absent when `ok === true`. */
	reason?: string;
	/** Probe model id used (carried back from the caller for display). */
	modelId?: string;
	/** Round-trip latency in milliseconds. */
	latencyMs?: number;
}

/**
 * Credential payload handed to {@link CompletionProbe}. For API-key
 * credentials only the bytes are exposed; for OAuth, every identity field
 * carried by the refreshed credential is included so the probe can compose
 * provider-specific apiKey shapes (e.g. GitHub Copilot / Google Gemini CLI
 * expect a JSON blob with `token` + `projectId`, not the raw access token).
 *
 * `refreshToken` may be {@link REMOTE_REFRESH_SENTINEL} when the credential
 * lives behind a broker; the chat endpoint never reads it, so the probe can
 * forward it verbatim into the structured shape without harm.
 */
export type CompletionProbeCredential =
	| { type: "api_key"; apiKey: string }
	| {
			type: "oauth";
			accessToken: string;
			refreshToken?: string;
			expiresAt?: number;
			accountId?: string;
			projectId?: string;
			email?: string;
			enterpriseUrl?: string;
			apiEndpoint?: string;
	  };

/**
 * Caller-supplied bearer probe. Receives the post-refresh credential for a
 * single row and reports whether a real chat-completion round-trip succeeds.
 * The check-credentials pipeline calls this AFTER any OAuth refresh so the
 * bytes match what a live request would send.
 */
export interface CompletionProbeInput {
	provider: Provider;
	credentialId: number;
	credential: CompletionProbeCredential;
	signal: AbortSignal;
}

export type CompletionProbe = (input: CompletionProbeInput) => Promise<CredentialCompletionResult>;

export interface CheckCredentialsOptions {
	signal?: AbortSignal;
	/** Per-credential probe timeout (ms). Defaults to the configured usage request timeout. */
	timeoutMs?: number;
	/** Provider → base URL override, same shape as {@link AuthStorage.fetchUsageReports}. */
	baseUrlResolver?: (provider: Provider) => string | undefined;
	/**
	 * Optional end-to-end probe. When provided, `checkCredentials` invokes it
	 * for every credential where a usable bearer is available (API key, or
	 * OAuth access token after refresh-on-expiry succeeded). The result lands
	 * on {@link CredentialHealthResult.completion}.
	 *
	 * The probe runs INDEPENDENTLY of whether a {@link UsageProvider} is
	 * configured: providers without a usage endpoint still benefit from the
	 * extra signal. The probe is NOT invoked when OAuth refresh fails — the
	 * bytes would be stale anyway and the upstream failure is already captured
	 * on `reason`.
	 */
	completionProbe?: CompletionProbe;
	/** Per-credential completion probe timeout (ms). Defaults to `timeoutMs`. */
	completionTimeoutMs?: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Auth Broker Snapshot Types
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Sentinel value placed in OAuth `refresh` fields when a credential is shared
 * via {@link AuthStorage.exportSnapshot}. Refresh tokens never leave the broker;
 * clients must call back to refresh.
 */
export const REMOTE_REFRESH_SENTINEL = "__remote__" as const;
export type RemoteRefreshSentinel = typeof REMOTE_REFRESH_SENTINEL;

/** OAuth credential with refresh token replaced by the broker sentinel. */
export type RemoteOAuthCredential = Omit<OAuthCredential, "refresh"> & {
	refresh: RemoteRefreshSentinel;
};

/** Discriminated credential payload as published by the broker. */
export type SnapshotCredential = ApiKeyCredential | RemoteOAuthCredential;

export interface AuthCredentialSnapshotEntry {
	id: number;
	provider: string;
	credential: SnapshotCredential;
	identityKey: string | null;
}

/**
 * Wire-shaped snapshot exported by {@link AuthStorage.exportSnapshot} and
 * served by the auth-broker server on `GET /v1/snapshot`.
 */
export interface AuthCredentialSnapshot {
	generation: number;
	generatedAt: number;
	credentials: AuthCredentialSnapshotEntry[];
}

// ─────────────────────────────────────────────────────────────────────────────
// AuthCredentialStore interface
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Persistence abstraction consumed by {@link AuthStorage}.
 *
 * Concrete implementations:
 * - {@link SqliteAuthCredentialStore} — local SQLite-backed store (default).
 * - `RemoteAuthCredentialStore` from `./auth-broker` — client-side snapshot of
 *   a remote broker; mutating methods (`replace*`, `upsert*`, `delete*ForProvider`)
 *   throw because login flows route through the broker, not the client.
 */
export interface CredentialRefreshLeaseFence {
	owner: string;
	nowMs: number;
}

export interface AuthCredentialStore {
	close(): void;
	/**
	 * Stateful probe for commits made by another process to the backing store.
	 * Returns true once per observed change.
	 */
	pollExternalChanges?(): boolean;
	/** Record the current auth revision after a local mutation already notified consumers. */
	acknowledgeLocalChanges?(): void;
	/** Optional hook to notify the underlying store that usage report cache is stale. */
	invalidateUsageCache?(signal?: AbortSignal): Promise<void>;
	listAuthCredentials(provider?: string): StoredAuthCredential[];
	/**
	 * Optional store hook to re-hydrate the credential snapshot from its
	 * backing source. Remote broker stores re-fetch `GET /v1/snapshot` so a
	 * disk-cached snapshot (up to an hour stale) cannot be paired with live
	 * per-credential data; local SQLite stores omit it — their reads are
	 * always current.
	 */
	refreshSnapshot?(): Promise<unknown>;
	/**
	 * Disabled credential tombstones (see {@link DisabledCredentialSummary}).
	 * Optional: remote stores forward to the broker's
	 * `GET /v1/credentials/disabled` (empty list when the broker predates the
	 * endpoint); stores without tombstones omit it.
	 */
	listDisabledCredentials?(provider?: string, signal?: AbortSignal): Promise<DisabledCredentialSummary[]>;
	updateAuthCredential(id: number, credential: AuthCredential): void;
	deleteAuthCredential(id: number, disabledCause: string): void;
	tryDisableAuthCredentialIfMatches(
		id: number,
		expectedData: string,
		disabledCause: string,
		lease?: CredentialRefreshLeaseFence,
	): boolean;
	tryUpdateAuthCredentialIfMatches?(
		id: number,
		expectedData: string,
		credential: AuthCredential,
		lease?: CredentialRefreshLeaseFence,
	): boolean;
	replaceAuthCredentialsForProvider(provider: string, credentials: AuthCredential[]): StoredAuthCredential[];
	upsertAuthCredentialForProvider(provider: string, credential: AuthCredential): StoredAuthCredential[];
	deleteAuthCredentialsForProvider(provider: string, disabledCause: string): void;
	getCache(key: string, options?: { includeExpired?: boolean }): string | null;
	setCache(key: string, value: string, expiresAtSec: number): void;
	/** Drop all cache rows whose keys start with the supplied prefix. */
	deleteCachePrefix?(prefix: string): void;
	cleanExpiredCache(): void;
	/** Non-expired block for one (credential, providerKey, scope) key, or undefined. */
	getCredentialBlock?(credentialId: number, providerKey: string, blockScope: string): number | undefined;
	/** Earliest time a shared-store block should be eligible for live-usage reconciliation. */
	getCredentialBlockReconcileAfter?(credentialId: number, providerKey: string, blockScope: string): number | undefined;
	/** Upsert with MAX semantics: keep the later blockedUntilMs on conflict. */
	upsertCredentialBlock?(block: StoredCredentialBlock): void;
	/** Drop one block row for a credential/provider/scope key. */
	deleteCredentialBlock?(credentialId: number, providerKey: string, blockScope: string): void;
	/** Drop every block row for a credential (all providerKeys/scopes). */
	deleteCredentialBlocks?(credentialId: number): void;
	/** Prune rows with blocked_until_ms <= nowMs. */
	cleanExpiredCredentialBlocks?(nowMs: number): void;
	/** List non-expired blocks for broker snapshots. */
	listCredentialBlocks?(credentialIds: readonly number[]): StoredCredentialBlock[];
	tryAcquireCredentialRefreshLease?(credentialId: number, owner: string, expiresAtMs: number): boolean;
	getCredentialRefreshLeaseExpiresAt?(credentialId: number): number | undefined;
	releaseCredentialRefreshLease?(credentialId: number, owner: string): void;
	renewCredentialRefreshLease?(credentialId: number, owner: string, expiresAtMs: number): boolean;
	/**
	 * Append usage-limit snapshots for trend history. Optional: stores without
	 * durable storage (e.g. the broker remote store) omit it and recording is
	 * skipped — the broker host records into its own database instead.
	 */
	recordUsageSnapshots?(entries: UsageHistoryEntry[]): void;
	/** Read recorded usage-limit snapshots, oldest first. */
	listUsageHistory?(query?: UsageHistoryQuery): UsageHistoryEntry[];
	/**
	 * Client hook: forward locally observed request usage. Remote broker stores
	 * batch these to the broker so it can attribute token burn per install;
	 * local stores omit it and observation is skipped.
	 * `client` overrides the reporting identity (gateway requests attribute to
	 * the originating client, not the gateway host).
	 */
	recordObservedUsage?(entries: ObservedUsageEntry[], client?: ClientUsageIdentity): void;
	/** Broker host: persist one client's observed-usage report. */
	recordClientUsage?(report: ClientUsageReport): void;
	/** Broker host: aggregate recorded per-client usage since a timestamp. */
	getClientUsageSummary?(sinceMs: number): ClientUsageSummary;
	/**
	 * Optional store-supplied OAuth refresh. When present, `AuthStorage` uses
	 * it before the per-provider local refresh path. `RemoteAuthCredentialStore`
	 * implements this against the broker; SQLite stores leave it undefined.
	 *
	 * Precedence: `AuthStorageOptions.refreshOAuthCredential` > this hook > local.
	 *
	 * `signal` propagates the agent's cancel (ESC, request abort, …) all the
	 * way to the broker fetch so a hung connection can't strand the caller
	 * for `timeoutMs * (maxRetries + 1)`.
	 */
	refreshOAuthCredential?(
		provider: Provider,
		credentialId: number,
		credential: OAuthCredential,
		signal?: AbortSignal,
	): Promise<OAuthCredentials>;
	/**
	 * Optional async pre-read hook invoked after AuthStorage selects a stored
	 * credential but before it returns that credential for an outbound request.
	 * Remote broker stores use this to wait out imminent rotations and refresh
	 * their local snapshot before the caller sees a stale access token.
	 */
	prepareForRequest?(credentialId: number, opts?: { signal?: AbortSignal }): Promise<boolean | undefined>;
	/**
	 * Optional store-supplied aggregate usage fetch. When present, `AuthStorage`
	 * routes `fetchUsageReports()` here instead of fanning out per-credential.
	 * `RemoteAuthCredentialStore` proxies to the broker (whose datacenter IP
	 * isn't rate-limited like a heavy residential client).
	 *
	 * Precedence: `AuthStorageOptions.fetchUsageReports` > this hook > local fan-out.
	 *
	 * `signal` propagates the agent's cancel down to the broker fetch.
	 */
	fetchUsageReports?(signal?: AbortSignal): Promise<UsageReport[] | null>;
	/**
	 * Optional store-supplied per-credential usage report lookup. When present,
	 * `AuthStorage` consults this before its own per-credential upstream fetch
	 * (`#getUsageReport`). `RemoteAuthCredentialStore` implements this against
	 * the broker's aggregate `/v1/usage` (one coalesced round-trip shared across
	 * all callers) so multi-credential ranking on the client never hits the
	 * upstream provider's rate-limited usage endpoint from the laptop IP.
	 *
	 * Returning `null` is authoritative — `AuthStorage` does NOT fall back to
	 * the local fetch path. The store hook owns the decision, since falling
	 * back would re-introduce the per-IP rate-limit problem the broker exists
	 * to avoid.
	 *
	 * `signal` propagates the agent's cancel down to the broker fetch.
	 */
	getUsageReport?(provider: Provider, credential: OAuthCredential, signal?: AbortSignal): Promise<UsageReport | null>;
	/**
	 * Optional store hook to ingest a parsed provider usage report for one OAuth
	 * credential. Remote broker stores use this to overlay header-derived limits
	 * onto their cached aggregate `/v1/usage` response without mutating broker
	 * state.
	 */
	ingestUsageReport?(provider: Provider, credential: OAuthCredential, report: UsageReport): boolean;
	/**
	 * Optional store hook to invalidate a specific credential after the upstream
	 * provider returned 401 on a supposedly-fresh key. Remote stores force the
	 * broker to re-issue the row; local stores can leave it undefined and let
	 * {@link AuthStorage.invalidateCredentialMatching} fall back to `reload()`.
	 */
	markCredentialSuspect?(credentialId: number, opts?: { signal?: AbortSignal }): Promise<void>;
	/**
	 * Optional async write hook for upserting a single credential. When present,
	 * `AuthStorage.#upsertOAuthCredential` routes through this instead of the
	 * sync `upsertAuthCredentialForProvider`. `RemoteAuthCredentialStore` uses
	 * it to send the upsert to the broker via `POST /v1/credential`.
	 *
	 * Implementations MUST update the in-memory snapshot before returning so the
	 * post-write read path is consistent.
	 */
	upsertAuthCredentialRemote?(provider: string, credential: AuthCredential): Promise<StoredAuthCredential[]>;
	/**
	 * Optional async write hook for replace-all semantics (e.g. API-key login
	 * overwriting any previous keys for the same provider). When present,
	 * `AuthStorage.set` routes through this instead of the sync
	 * `replaceAuthCredentialsForProvider`.
	 */
	replaceAuthCredentialsRemote?(provider: string, credentials: AuthCredential[]): Promise<StoredAuthCredential[]>;
	/**
	 * Optional async write hook for disabling one stored credential. Remote stores
	 * use it to await broker persistence before AuthStorage updates its snapshot.
	 */
	deleteAuthCredentialRemote?(id: number, disabledCause: string): Promise<boolean>;
	/**
	 * Optional async write hook for clearing every credential for a provider
	 * (logout). When present, `AuthStorage.remove` routes through this instead
	 * of the sync `deleteAuthCredentialsForProvider`.
	 */
	deleteAuthCredentialsRemote?(provider: string, disabledCause: string): Promise<void>;
}

// ─────────────────────────────────────────────────────────────────────────────
// AuthStorage Options
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Event payload describing a credential that was just soft-disabled.
 *
 * Today the only call site is OAuth refresh failures with a definitive cause
 * (`invalid_grant`, `401/403` not from a network blip, etc.) — the
 * disabled_cause string is the verbatim error captured for forensics.
 *
 * Subscribers can use this to surface a notification, banner, or auto-launch
 * a re-login flow instead of letting the credential silently disappear.
 */
export interface CredentialDisabledEvent {
	provider: string;
	disabledCause: string;
}

export type AuthStorageOptions = {
	usageProviderResolver?: (provider: Provider) => UsageProvider | undefined;
	rankingStrategyResolver?: (provider: Provider) => CredentialRankingStrategy | undefined;
	usageFetch?: typeof fetch;
	usageRequestTimeoutMs?: number;
	usageLogger?: UsageLogger;
	/**
	 * Resolve a config value (API key, header value, etc.) to an actual value.
	 * - coding-agent injects its resolveConfigValue (supports "!command" syntax via pi-natives)
	 * - Default: checks environment variable first, then treats as literal
	 */
	configValueResolver?: (config: string) => Promise<string | undefined>;
	/**
	 * Optional callback fired when AuthStorage automatically disables a
	 * credential because something detected it as no longer usable — today
	 * that's the OAuth refresh-failure path in `getApiKey`. NOT fired for
	 * user-initiated `remove()` (the user already knows) or dedup of
	 * duplicate credentials (uninteresting hygiene).
	 */
	onCredentialDisabled?: (event: CredentialDisabledEvent) => void | Promise<void>;
	/**
	 * Override OAuth refresh. When set, `AuthStorage` calls this instead of the
	 * per-provider local refresh function. Receives the credential id so the
	 * implementation can address remote credentials.
	 *
	 * Must return updated {@link OAuthCredentials} with at least `access` and
	 * `expires`. `refresh` may be an opaque sentinel (e.g. `"__remote__"`) when
	 * the actual refresh token never leaves the broker.
	 */
	refreshOAuthCredential?: (
		provider: Provider,
		credentialId: number,
		credential: OAuthCredential,
		signal?: AbortSignal,
	) => Promise<OAuthCredentials>;
	/**
	 * Human-readable description of the credential store backing this
	 * AuthStorage instance. Surfaced through {@link AuthStorage.describeCredentialSource}
	 * so the TUI can show where a token came from (broker URL or local SQLite path).
	 *
	 * Examples:
	 * - `"local ~/.omp/agent/agent.db"`
	 * - `"broker http://omp.internal:8765"`
	 */
	sourceLabel?: string;
	/**
	 * Override `fetchUsageReports`. When set, `AuthStorage.fetchUsageReports`
	 * calls this instead of fanning out per-credential. The primary use case is
	 * routing through a broker that egresses from a less-throttled IP — e.g. a
	 * residential laptop trips Anthropic's per-IP rate limit on the usage
	 * endpoint and drops 2-of-5 credentials, while the VPS broker gets all 5.
	 *
	 * Implementations may return null when no usage data is available; the
	 * AuthStorage caller surfaces that to its own consumer unchanged.
	 */
	fetchUsageReports?: (signal?: AbortSignal) => Promise<UsageReport[] | null>;
};

// ─────────────────────────────────────────────────────────────────────────────
// Default Config Value Resolver
// ─────────────────────────────────────────────────────────────────────────────
