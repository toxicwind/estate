// Helpers for Muse dynamic credential surrogates (Bun port of the Python helper).
//
// This bundled helper is imported by generated skill CLIs. It returns only
// `hsurr:*` surrogate values; Sentinel/authd replace those surrogates with real
// credentials on approved outbound requests.

import { connect } from "node:net";
import { readFileSync, statSync } from "node:fs";

export const AUTHD_SOCKET_DEFAULT = "/run/hatch/auth/authd.sock";

// Resolved per call, not at import: a process that starts before the broker
// socket is wired up must still pick up JARVIS_AUTHD_SOCK.
export function authdSocket() {
  return process.env.JARVIS_AUTHD_SOCK ?? AUTHD_SOCKET_DEFAULT;
}

// ---------------------------------------------------------------------------
// Local secret store fallback.
//
// authd's socket lives in the hatch cell and is absent here, so a
// credentialed skill would otherwise be dead in the water. secretsmith owns
// the local KEY=value store; this helper only asks it. Keeping the parsing
// here would fork the resolution rules and the 0600 permission check.
// ---------------------------------------------------------------------------

export const SECRETSMITH_DEFAULT =
  "/home/toxic/estate/projects/mesh/secretsmith/bin/secretsmith";

export function secretsmithBin() {
  return process.env.SECRETSMITH ?? SECRETSMITH_DEFAULT;
}

let localCache;

// Returns { entry, source } for a credential name, or null when neither the
// process env nor the store has it. The value is never logged or interpolated
// into an error message.
export function localCredentialEntry(credentialName) {
  if (localCache && localCache.has(credentialName)) {
    return localCache.get(credentialName);
  }
  let result = null;
  const bin = secretsmithBin();
  try {
    const proc = Bun.spawnSync({
      cmd: [bin, "--json", "env-get", credentialName],
      stdout: "pipe",
      stderr: "pipe",
    });
    if (proc.exitCode === 0) {
      const payload = JSON.parse(proc.stdout.toString());
      result = {
        entry: { surrogate: payload.value, placement: "bearer_header" },
        source: payload.key,
      };
    }
  } catch {
    result = null;
  }
  localCache ??= new Map();
  localCache.set(credentialName, result);
  return result;
}



export const SURROGATE_PATH = "/v1/credentials/surrogate";

export class DynamicCredentialError extends Error {
  constructor(message, opts) {
    super(message, opts);
    this.name = "DynamicCredentialError";
  }
}

const DEADLINE_MS = 2000;
const MAX_BODY_BYTES = 65536;

function postJsonUnix(socketPath, path, payload, timeoutMs = DEADLINE_MS) {
  const body = Buffer.from(JSON.stringify(payload), "utf8");
  const head = Buffer.from(
    `POST ${path} HTTP/1.1\r\n` +
      `Host: authd.local\r\n` +
      `Content-Type: application/json\r\n` +
      `Content-Length: ${body.length}\r\n` +
      `Connection: close\r\n` +
      `\r\n`,
    "ascii",
  );
  const request = Buffer.concat([head, body]);

  let st;
  try {
    st = statSync(socketPath);
  } catch (err) {
    throw new DynamicCredentialError(
      `unavailable: authd socket not found at ${socketPath}`,
      { cause: err },
    );
  }
  if (!st.isSocket()) {
    throw new DynamicCredentialError(
      `unavailable: ${socketPath} is not a unix socket`,
    );
  }

  return new Promise((resolve, reject) => {
    let settled = false;
    let response = Buffer.alloc(0);
    const finish = (fn, arg) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      socket.destroy();
      fn(arg);
    };
    const socket = connect(socketPath);
    const timer = setTimeout(
      () =>
        finish(
          reject,
          new DynamicCredentialError(
            `authd did not respond within ${timeoutMs}ms`,
          ),
        ),
      timeoutMs,
    );
    socket.on("connect", () => socket.write(request));
    socket.on("data", (chunk) => {
      response = Buffer.concat([response, chunk]);
      if (response.length > MAX_BODY_BYTES) {
        finish(reject, new DynamicCredentialError("authd response too large"));
      }
    });
    socket.on("error", (err) =>
      finish(
        reject,
        new DynamicCredentialError(`authd socket error: ${err.message}`, {
          cause: err,
        }),
      ),
    );
    socket.on("end", () => finish(resolve, response));
    socket.on("close", () => finish(resolve, response));
  });
}
// authd answers over a unix socket with an ordinary HTTP/1.1 response, which
// may be chunked. There is no HTTP client on a raw socket, so de-chunk here.
export function decodeBody(headers, raw) {
  if (!/^transfer-encoding:[^\r\n]*chunked/im.test(headers)) {
    return raw.toString("utf8");
  }
  const out = [];
  let i = 0;
  while (i < raw.length) {
    const nl = raw.indexOf("\r\n", i, "latin1");
    if (nl < 0) break;
    const size = parseInt(
      raw.subarray(i, nl).toString("latin1").split(";")[0],
      16,
    );
    if (!Number.isFinite(size) || size === 0) break;
    const start = nl + 2;
    out.push(raw.subarray(start, start + size));
    i = start + size + 2;
  }
  return Buffer.concat(out).toString("utf8");
}


export async function dynamicCredentialEntry(
  credentialName,
  entryName = "access_token",
  { socketPath = authdSocket(), timeoutMs = DEADLINE_MS } = {},
) {
  const raw = await postJsonUnix(
    socketPath,
    SURROGATE_PATH,
    { name: credentialName },
    timeoutMs,
  );
  const sep = raw.indexOf("\r\n\r\n");
  if (sep < 0) {
    throw new DynamicCredentialError(
      "authd returned a malformed HTTP response",
    );
  }
  const headers = raw.subarray(0, sep).toString("latin1");
  const statusLine = headers.split("\r\n")[0];
  const parts = statusLine.split(" ", 3);
  if (parts.length < 2 || !/^\d+$/.test(parts[1])) {
    throw new DynamicCredentialError(
      `authd returned malformed status: ${statusLine}`,
    );
  }
  const status = Number(parts[1]);
  const body = decodeBody(headers, raw.subarray(sep + 4));
  if (status !== 200) {
    throw new DynamicCredentialError(
      `authd ${SURROGATE_PATH} returned HTTP ${status}: ${body.trim()}`,
    );
  }

  let payload;
  try {
    payload = JSON.parse(body);
  } catch (err) {
    throw new DynamicCredentialError(
      "authd surrogate response was not JSON",
      { cause: err },
    );
  }

  for (const entry of payload.credentials ?? []) {
    if (entry.name !== entryName) continue;
    const surrogate = String(entry.surrogate ?? "").trim();
    if (!surrogate.startsWith("hsurr:")) {
      throw new DynamicCredentialError(
        `authd returned a non-surrogate value for ${credentialName}:${entryName}`,
      );
    }
    return entry;
  }
  throw new DynamicCredentialError(
    `missing ${entryName} surrogate for credential ${credentialName}`,
  );
}

export function ensureAllowedUrl(url, allowedHosts) {
  const host = new URL(url).hostname.toLowerCase();
  const allowed = new Set(
    [...allowedHosts].map((h) => h.trim().toLowerCase()).filter(Boolean),
  );
  if (!host || !allowed.has(host)) {
    const display = [...allowed].sort().join(", ") || "<none>";
    throw new DynamicCredentialError(
      `refusing authenticated request to ${host || "<missing host>"}; allowed hosts: ${display}`,
    );
  }
  return host;
}

// Returns the headers to merge into an outbound request.
export async function surrogateHeaders(
  url,
  credentialName,
  { entryName = "access_token", allowedHosts } = {},
) {
  ensureAllowedUrl(url, allowedHosts);
  let entry;
  try {
    entry = await dynamicCredentialEntry(credentialName, entryName);
  } catch (err) {
    // Only the broker being absent is recoverable. A broker that answers
    // with an error is a real failure and must surface, not be papered over
    // by silently swapping in a different credential source.
    if (!/^unavailable:/.test(err.message)) throw err;
    const local = localCredentialEntry(credentialName);
    if (!local) throw err;
    entry = local.entry;
  }
  const surrogate = String(entry.surrogate).trim();
  const placement = entry.placement;

  if (placement === "bearer_header") {
    return { Authorization: `Bearer ${surrogate}` };
  }
  if (placement && typeof placement === "object" && typeof placement.custom_header === "string") {
    return { [placement.custom_header]: surrogate };
  }
  if (placement && typeof placement === "object" && "url_path_segment" in placement) {
    throw new DynamicCredentialError(
      "url_path_segment credentials must be applied before the request is created",
    );
  }
  if (placement && typeof placement === "object" && "query_param" in placement) {
    throw new DynamicCredentialError(
      "query_param credentials must be applied to the URL before the request is created; use urlWithSurrogateQueryParam()",
    );
  }
  throw new DynamicCredentialError(
    `unsupported credential placement: ${JSON.stringify(placement)}`,
  );
}

export async function readJsonResponse(response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch (err) {
    throw new DynamicCredentialError(
      "provider response was not valid JSON",
      { cause: err },
    );
  }
}

export async function urlWithSurrogatePathSegment(
  urlTemplate,
  credentialName,
  { entryName = "access_token", allowedHosts } = {},
) {
  ensureAllowedUrl(urlTemplate, allowedHosts);
  const parsed = new URL(urlTemplate);
  if (!parsed.pathname.includes("{}")) {
    throw new DynamicCredentialError(
      "url template path must contain {} placeholder",
    );
  }
  const entry = await dynamicCredentialEntry(credentialName, entryName);
  const placement = entry.placement;
  if (!(placement && typeof placement === "object" && "url_path_segment" in placement)) {
    throw new DynamicCredentialError(
      `credential is not url_path_segment: ${JSON.stringify(placement)}`,
    );
  }
  const surrogate = encodeURIComponent(String(entry.surrogate).trim());
  return urlTemplate.replace("{}", surrogate);
}

export async function urlWithSurrogateQueryParam(
  url,
  credentialName,
  { entryName = "access_token", allowedHosts } = {},
) {
  ensureAllowedUrl(url, allowedHosts);
  const entry = await dynamicCredentialEntry(credentialName, entryName);
  const placement = entry.placement;
  if (
    !(placement &&
      typeof placement === "object" &&
      typeof placement.query_param === "string")
  ) {
    throw new DynamicCredentialError(
      `credential is not query_param: ${JSON.stringify(placement)}`,
    );
  }
  const parsed = new URL(url);
  parsed.searchParams.append(placement.query_param, String(entry.surrogate).trim());
  return parsed.toString();
}

export async function exists(path) {
  try {
    await fs.access(path);
    return true;
  } catch {
    return false;
  }
}
