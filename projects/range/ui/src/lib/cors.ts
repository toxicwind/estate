// CORS policy builder + live preflight probe for the herd dashboard.
//
// herd exposes no config API, so this panel cannot read or write the active
// security.cors block directly. Instead it does two things:
//   1. Probes the effective policy: a same-origin OPTIONS request carries the
//      page's Origin automatically, and herd's CORS middleware answers with
//      the Access-Control-* headers it would send a browser. That is the
//      policy as the browser sees it.
//   2. Builds the security.cors YAML snippet to paste into herd.yaml, with
//      the same validation rules herd applies at load time (mirrored from
//      internal/config/security.go).

export interface CorsConfig {
  allowedOrigins: string[];
  allowCredentials: boolean;
  allowPrivateNetwork: boolean;
  allowedMethods: string[];
  allowedHeaders: string[];
  exposedHeaders: string[];
  // null/0 = server default (86400s)
  maxAge: number | null;
}

export function defaultCorsConfig(): CorsConfig {
  return {
    allowedOrigins: [],
    allowCredentials: false,
    allowPrivateNetwork: false,
    allowedMethods: [],
    allowedHeaders: [],
    exposedHeaders: [],
    maxAge: null,
  };
}

// Server defaults mirrored from herd's internal/config/security.go. The YAML
// builder omits fields left at these defaults so the snippet stays minimal.
export const DEFAULT_CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"];
export const DEFAULT_CORS_HEADERS = ["Content-Type", "Authorization", "Accept", "X-Requested-With"];
export const DEFAULT_CORS_MAX_AGE = 86400;

// Common method set offered by the builder UI.
export const KNOWN_HTTP_METHODS = [
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
  "OPTIONS",
  "HEAD",
];

const HTTP_TOKEN_RE = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;

// isHttpToken mirrors herd's config.IsHTTPToken (RFC 9110 token), the
// grammar both method names and header names follow.
export function isHttpToken(s: string): boolean {
  return HTTP_TOKEN_RE.test(s);
}

// isValidCorsOrigin mirrors herd's validateCORSOrigin: a bare
// scheme://host[:port], the only form a browser ever sends in an Origin
// header. "*" is the explicit allow-any marker. A trailing slash, path,
// query, fragment or userinfo would silently never match an Origin header,
// so each is rejected like the server rejects it. The check is structural
// on the raw string (rather than the URL-normalized form) so explicit
// default ports and mixed-case hosts are accepted exactly as the server
// accepts them.
export function isValidCorsOrigin(origin: string): boolean {
  if (origin === "*") return true;
  const trimmed = origin.trim();
  if (trimmed === "" || trimmed !== origin) return false;
  let url: URL;
  try {
    url = new URL(trimmed);
  } catch {
    return false;
  }
  if (url.protocol === "" || !url.host) return false;
  const afterScheme = trimmed.slice(`${url.protocol}//`.length);
  return afterScheme !== "" && !/[/?#@]/.test(afterScheme);
}

// validateCorsConfig mirrors herd's CORSConfig.Validate. Returns human
// readable problems; empty means herd would accept the block.
export function validateCorsConfig(cfg: CorsConfig): string[] {
  const problems: string[] = [];
  const origins = cfg.allowedOrigins.map((o) => o.trim()).filter((o) => o !== "");
  const hasNonOriginSettings =
    cfg.allowCredentials ||
    cfg.allowPrivateNetwork ||
    cfg.allowedMethods.length > 0 ||
    cfg.allowedHeaders.length > 0 ||
    cfg.exposedHeaders.length > 0 ||
    (cfg.maxAge !== null && cfg.maxAge !== 0);

  if (origins.length === 0) {
    if (hasNonOriginSettings) {
      problems.push(
        "allowedOrigins is required when any other CORS setting is present — " +
          "remove the whole security.cors block to keep the permissive default.",
      );
    }
  } else {
    const wildcard = origins.includes("*");
    if (wildcard && cfg.allowCredentials) {
      problems.push(
        'allowedOrigins may not contain "*" when allowCredentials is true — list the origins explicitly.',
      );
    }
    if (wildcard && cfg.allowPrivateNetwork) {
      problems.push(
        'allowedOrigins may not contain "*" when allowPrivateNetwork is true — list the origins explicitly.',
      );
    }
    for (const origin of origins) {
      if (origin !== "*" && !isValidCorsOrigin(origin)) {
        problems.push(
          `allowedOrigins: ${JSON.stringify(origin)} must be a scheme://host[:port] origin, e.g. https://dashboard.example.com`,
        );
      }
    }
  }

  for (const method of cfg.allowedMethods) {
    if (!isHttpToken(method)) {
      problems.push(`allowedMethods: ${JSON.stringify(method)} is not a valid HTTP method`);
    }
  }
  for (const header of cfg.allowedHeaders) {
    if (!isHttpToken(header)) {
      problems.push(`allowedHeaders: ${JSON.stringify(header)} is not a valid HTTP header name`);
    }
  }
  for (const header of cfg.exposedHeaders) {
    if (!isHttpToken(header)) {
      problems.push(`exposedHeaders: ${JSON.stringify(header)} is not a valid HTTP header name`);
    }
  }

  if (cfg.maxAge !== null && (!Number.isInteger(cfg.maxAge) || cfg.maxAge < 0)) {
    problems.push("maxAge must be an integer >= 0");
  }

  return problems;
}

// yamlScalar renders one scalar for the snippet. "*" must be quoted: a bare
// * starts a YAML alias.
function yamlScalar(value: string): string {
  return /^[A-Za-z0-9_][A-Za-z0-9_.:/-]*$/.test(value) ? value : JSON.stringify(value);
}

function yamlStringList(values: string[]): string[] {
  return values.map((v) => `      - ${yamlScalar(v)}`);
}

// corsConfigToYaml renders the security.cors block to paste into herd.yaml.
// Fields left empty take herd's defaults, so they are omitted — except
// allowedOrigins, which selects the mode (absent = legacy permissive).
// An entirely empty config renders just the commented header.
export function corsConfigToYaml(cfg: CorsConfig): string {
  const lines = ["security:", "  cors:"];
  const origins = cfg.allowedOrigins.map((o) => o.trim()).filter((o) => o !== "");
  const methods = cfg.allowedMethods.map((m) => m.trim()).filter((m) => m !== "");
  const allowedHeaders = cfg.allowedHeaders.map((h) => h.trim()).filter((h) => h !== "");
  const exposedHeaders = cfg.exposedHeaders.map((h) => h.trim()).filter((h) => h !== "");

  if (origins.length > 0) {
    lines.push("    allowedOrigins:");
    lines.push(...yamlStringList(origins));
  }
  if (cfg.allowCredentials) lines.push("    allowCredentials: true");
  if (cfg.allowPrivateNetwork) lines.push("    allowPrivateNetwork: true");
  if (methods.length > 0) {
    lines.push("    allowedMethods:");
    lines.push(...yamlStringList(methods));
  }
  if (allowedHeaders.length > 0) {
    lines.push("    allowedHeaders:");
    lines.push(...yamlStringList(allowedHeaders));
  }
  if (exposedHeaders.length > 0) {
    lines.push("    exposedHeaders:");
    lines.push(...yamlStringList(exposedHeaders));
  }
  if (cfg.maxAge !== null && cfg.maxAge !== 0 && cfg.maxAge !== DEFAULT_CORS_MAX_AGE) {
    lines.push(`    maxAge: ${cfg.maxAge}`);
  }

  if (lines.length === 2) {
    lines.push("    # (empty — herd keeps the legacy permissive policy)");
  }
  return lines.join("\n") + "\n";
}

export interface CorsProbeResult {
  ok: boolean;
  status: number;
  // The origin the probe ran as. Browsers forbid scripts from setting the
  // Origin header, so the probe always runs as the page's own origin.
  probedOrigin: string;
  allowOrigin: string | null;
  allowCredentials: string | null;
  allowMethods: string | null;
  allowHeaders: string | null;
  exposeHeaders: string | null;
  maxAge: string | null;
  allowPrivateNetwork: string | null;
  error?: string;
}

function emptyProbeResult(probedOrigin: string, error: string): CorsProbeResult {
  return {
    ok: false,
    status: 0,
    probedOrigin,
    allowOrigin: null,
    allowCredentials: null,
    allowMethods: null,
    allowHeaders: null,
    exposeHeaders: null,
    maxAge: null,
    allowPrivateNetwork: null,
    error,
  };
}

// probeCorsPolicy asks herd for its effective CORS policy. The request is
// same-origin so no preflight-of-the-preflight happens; the browser attaches
// the page's Origin automatically (OPTIONS is not GET/HEAD) and herd's CORS
// middleware answers 204 with the Access-Control-* headers it would send a
// browser carrying that Origin.
export async function probeCorsPolicy(
  fetchFn: typeof fetch = fetch,
  getOrigin: () => string = () =>
    typeof window !== "undefined" ? window.location.origin : "",
): Promise<CorsProbeResult> {
  const probedOrigin = getOrigin();
  try {
    const res = await fetchFn("/v1/models", {
      method: "OPTIONS",
      headers: {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization",
      },
    });
    const header = (name: string): string | null => res.headers.get(name);
    return {
      ok: res.ok,
      status: res.status,
      probedOrigin,
      allowOrigin: header("access-control-allow-origin"),
      allowCredentials: header("access-control-allow-credentials"),
      allowMethods: header("access-control-allow-methods"),
      allowHeaders: header("access-control-allow-headers"),
      exposeHeaders: header("access-control-expose-headers"),
      maxAge: header("access-control-max-age"),
      allowPrivateNetwork: header("access-control-allow-private-network"),
    };
  } catch (err) {
    return emptyProbeResult(probedOrigin, err instanceof Error ? err.message : String(err));
  }
}

// describeEffectivePolicy turns a probe result into one plain-English line
// for the Settings panel header.
export function describeEffectivePolicy(probe: CorsProbeResult): string {
  if (!probe.ok) return probe.error ? `probe failed: ${probe.error}` : `probe failed (HTTP ${probe.status})`;
  if (probe.allowOrigin === null) return "no CORS headers — origin not allowed by policy";
  if (probe.allowOrigin === "*") return "permissive — any origin allowed";
  return `restricted — allows ${probe.allowOrigin}`;
}
