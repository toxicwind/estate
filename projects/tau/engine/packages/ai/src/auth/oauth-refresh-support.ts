/**
 * OAuth refresh support: bearer fingerprinting, refresh timeouts, OAuth access/identity and reset-credit types.
 *
 * Extracted verbatim from auth-storage.ts (surgical split 2026-09-14).
 * Re-exported through auth-storage.ts; import from there.
 */
import type { OAuthCredentials } from "../registry/oauth/types";
import type { CodexResetConsumeCode, CodexResetCredit } from "../usage/openai-codex-reset";
import type { OAuthCredential } from "./storage-contract";
import { createHash } from "node:crypto";

export const OAUTH_BEARER_FINGERPRINT_HISTORY_LIMIT = 8;

/** SHA-256 bearer fingerprint, so superseded OAuth token bytes never enter the identity cache. */
export function fingerprintOAuthBearer(bearer: string): string {
	return createHash("sha256").update(bearer).digest("base64url");
}
export const SESSION_STICKY_CACHE_PREFIX = "session:sticky:";
/**
 * Anthropic-only idle window after which a session's pinned credential no
 * longer suppresses usage-based re-ranking. Anthropic caps OAuth prompt-cache
 * retention at `ttl: "1h"` (ephemeral ~5min otherwise), so after this long
 * without an Anthropic resolve the conversation-prefix cache is no longer
 * guaranteed warm. Other providers retain indefinite stickiness until their
 * own cache lifetimes are verified.
 */
export const ANTHROPIC_SESSION_STICKY_CACHE_WARM_MS = 60 * 60_000;

export const DEFAULT_OAUTH_REFRESH_TIMEOUT_MS = 10_000;
export const OAUTH_REFRESH_FAILURE_BACKOFF_MS = 5 * 60 * 1000;
/**
 * Refresh OAuth access tokens this many ms before their stated expiry. The
 * skew exists so callers downstream of {@link AuthStorage} (stream providers,
 * usage probes, web_search) never observe a credential that is expired or
 * about to expire mid-request — there's a single rotation point and everyone
 * downstream trusts the token they receive.
 *
 * Set to 60s: comfortably absorbs request RTT + a clock-skew window without
 * triggering a refresh on every request. Provider token endpoints typically
 * mint access tokens with 30-60min lifetimes, so refreshing 60s early changes
 * the rotation cadence by <4%.
 */
export const OAUTH_REFRESH_SKEW_MS = 60_000;
export const OAUTH_REFRESH_LEASE_TTL_MS = 15_000;
export const OAUTH_REFRESH_LEASE_POLL_MS = 50;
export const OAUTH_REFRESH_LEASE_RENEW_MS = 5_000;
export const OAUTH_REFRESH_OPERATION_TIMEOUT_MS = 10_000;
/**
 * Cap on the buffered credential_disabled backlog held while no handler is attached.
 * In practice the backlog is 0–N where N ≈ active providers (≤ ~20). The cap exists so
 * pathological detach-without-reattach loops can't grow memory unboundedly.
 */
export const MAX_PENDING_DISABLED_EVENTS = 32;

export type AuthApiKeyOptions = {
	baseUrl?: string;
	modelId?: string;
	/**
	 * Caller's cancel signal. Threaded into any broker-bound OAuth refresh so
	 * `ESC` / request abort actually kills a hung broker fetch instead of
	 * stranding the caller for `timeoutMs * (maxRetries + 1)`.
	 */
	signal?: AbortSignal;
	/**
	 * Force a re-mint of the session-preferred OAuth credential's access token,
	 * bypassing the not-yet-expired short-circuit. Powers step (b) of the
	 * auth-retry policy ("refresh the SAME account") so a locally-cached token
	 * that a peer/broker rotated out from under us is replaced before retrying.
	 */
	forceRefresh?: boolean;
};
export type OAuthResolutionResult = {
	apiKey: string;
	credential: OAuthCredential;
	credentialId?: number;
};

/**
 * Refreshed OAuth access plus identity metadata returned by
 * {@link AuthStorage.getOAuthAccess}. Callers that authenticate via a bearer
 * AND need the credential's identity (Codex `chatgpt-account-id`, Google
 * `projectId`, GitHub `enterpriseUrl`) consume this shape directly; the
 * refresh slot is deliberately omitted because rotating refresh tokens never
 * leave {@link AuthStorage}.
 */
export interface OAuthAccess {
	accessToken: string;
	credentialId?: number;
	accountId?: string;
	email?: string;
	projectId?: string;
	enterpriseUrl?: string;
	apiEndpoint?: string;
	/** Organization/workspace the credential is scoped to (Anthropic/ChatGPT multi-subscription). */
	orgId?: string;
	orgName?: string;
}

/**
 * Identity slice of the credential a successful {@link AuthStorage.login}
 * stored — lets callers confirm WHICH account (and for Anthropic, which
 * organization/subscription) was added, without exposing tokens.
 */
export interface OAuthLoginIdentity {
	type: "oauth" | "api_key";
	email?: string;
	accountId?: string;
	orgId?: string;
	orgName?: string;
}

export interface OAuthAccessFailure {
	credentialId?: number;
	accountId?: string;
	email?: string;
	projectId?: string;
	enterpriseUrl?: string;
	apiEndpoint?: string;
	/** Organization/workspace the credential is scoped to (Anthropic/ChatGPT multi-subscription). */
	orgId?: string;
	orgName?: string;
	error: string;
}

/**
 * Identity of the OAuth credential a session is currently routed to. Read-only
 * display/metadata shape: `accountId` is the provider's account UUID, `email`
 * the user-facing login, `projectId` the GCP-style project for providers that
 * key usage on it (Gemini CLI / Antigravity).
 */
export interface OAuthAccountIdentity {
	accountId?: string;
	email?: string;
	projectId?: string;
	/** Organization/workspace the credential is scoped to (Anthropic/ChatGPT multi-subscription). */
	orgId?: string;
	orgName?: string;
}

export type OAuthAccessResolution = ({ ok: true } & OAuthAccess) | ({ ok: false } & OAuthAccessFailure);

/**
 * Read-only identity of one stored OAuth account, in stable storage order.
 * Returned by {@link AuthStorage.listOAuthAccounts}; `position` (0-based) is the
 * selector accepted by {@link AuthStorage.getOAuthAccessAt}.
 */
export interface OAuthAccountSummary {
	position: number;
	credentialId: number;
	accountId?: string;
	email?: string;
	projectId?: string;
	enterpriseUrl?: string;
	/** Organization/workspace the credential is scoped to (Anthropic/ChatGPT multi-subscription). */
	orgId?: string;
	orgName?: string;
	/** True when this account is the session-sticky OAuth credential requested by `listOAuthAccounts`. */
	active: boolean;
}
export interface InvalidateCredentialMatchingOptions {
	signal?: AbortSignal;
	sessionId?: string;
}

/** Options for refreshing one stored OAuth row through durable ownership. */
export interface StoredOAuthRefreshOptions<T extends OAuthCredential = OAuthCredential> {
	/** Stable row id when a provider has multiple OAuth credentials. */
	credentialId?: number;
	observedCredential?: T;
	credentialFromRow: (credential: OAuthCredential) => T | undefined;
	forceRefresh?: boolean;
	canRefresh?: (credential: T) => boolean;
	refreshSkewMs?: number;
	signal?: AbortSignal;
	keepCredentialOnRefreshFailure?: boolean | ((error: unknown) => boolean);
	onRefreshFailure?: (error: unknown) => void;
	refreshTimeoutMs?: number;
	refresh: (credential: T, signal?: AbortSignal) => Promise<OAuthCredentials>;
	mergeRefreshedCredential?: (credential: T, refreshed: OAuthCredentials) => T;
	isDefinitiveFailure?: (error: unknown) => boolean;
	disabledCause?: (error: unknown) => string;
}

/** Result of a stored OAuth refresh attempt. */
export interface StoredOAuthRefreshResult<T extends OAuthCredential = OAuthCredential> {
	credential: T | undefined;
	refreshed: boolean;
	removed: boolean;
}

/**
 * Identifies which stored account to redeem a saved rate-limit reset for.
 * Any one field is enough; `credentialId` is the most precise.
 */
export interface ResetCreditTarget {
	credentialId?: number;
	accountId?: string;
	email?: string;
}

/** Outcome of {@link AuthStorage.redeemResetCredit}. */
export interface ResetCreditRedeemOutcome {
	/** `true` only when a reset was actually applied (`code === "reset"`). */
	ok: boolean;
	/**
	 * Result code. Backend codes: `reset` (success), `already_redeemed`,
	 * `no_credit`, `nothing_to_reset`. Locally-synthesized: `no_account`
	 * (target not found), `account_unavailable` (token refresh failed),
	 * `credit_list_failed` (transport/auth failure while listing credits —
	 * retryable, unlike a genuine `no_credit`), `http_<status>` (unexpected
	 * HTTP).
	 */
	code: CodexResetConsumeCode;
	accountId?: string;
	email?: string;
	/** The credit that was spent (when one was). */
	creditId?: string;
}

/** One stored account's live saved-reset status, from {@link AuthStorage.listResetCredits}. */
export interface ResetCreditAccountStatus {
	credentialId?: number;
	accountId?: string;
	email?: string;
	/** Resets redeemable for this account right now (live, not cached). */
	availableCount: number;
	credits: CodexResetCredit[];
	/** Whether this is the given session's active account. */
	active: boolean;
	/** Set when the account's token refresh or list call failed. */
	error?: string;
}

export function isAbortSignalOption(
	value: InvalidateCredentialMatchingOptions | AbortSignal | undefined,
): value is AbortSignal {
	return typeof value === "object" && value !== null && "aborted" in value && "addEventListener" in value;
}
