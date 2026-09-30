/**
 * Code generation: the package is the single source of truth; non-TS
 * consumers get GENERATED artifacts, never hand-maintained copies.
 *
 * - generated/providers.json — canonical data artifact (Python scripts, docs).
 * - generated/providers.go  — drop-in data file for herd (Go cannot import TS).
 *
 * Both are checked in. `bun run build` regenerates them; the sync test
 * regenerates into a temp dir and diffs byte-for-byte, so a stale artifact
 * fails the build. The generated files carry a DO-NOT-EDIT header.
 */
import type { ModelAlias, ProviderDef } from "./types.ts";

export interface CodegenInput {
  defs: ProviderDef[];
  aliases: Record<string, ModelAlias>;
  deadIds: string[];
  /** Free-form provenance, e.g. git sha of the source. */
  provenance?: string;
}

function jsonEscaped(s: string): string {
  return JSON.stringify(s);
}

function goStringSlice(ids: string[], elementIndent = "\t\t", closeIndent = "\t"): string {
  if (ids.length === 0) return "[]string{}";
  return `[]string{\n${ids.map((id) => `${elementIndent}${jsonEscaped(id)},`).join("\n")}\n${closeIndent}}`;
}

function goStringMap(m: Record<string, string>): string {
  const keys = Object.keys(m).sort();
  if (keys.length === 0) return "map[string]string{}";
  return `map[string]string{\n${keys.map((k) => `\t\t${jsonEscaped(k)}: ${jsonEscaped(m[k])},`).join("\n")}\n\t}`;
}

function goAliasMap(m: Record<string, ModelAlias>): string {
  const keys = Object.keys(m).sort();
  if (keys.length === 0) return "map[string][2]string{}";
  // gofmt aligns map values: colon directly after the key, padding after the
  // colon. Emit gofmt-clean so the artifact needs no post-processing.
  const width = Math.max(...keys.map((k) => jsonEscaped(k).length));
  return `map[string][2]string{\n${keys
    .map(
      (k) =>
        `\t${jsonEscaped(k)}:${" ".repeat(width - jsonEscaped(k).length + 1)}{${jsonEscaped(m[k][0])}, ${jsonEscaped(m[k][1])}},`,
    )
    .join("\n")}\n}`;
}

/** Canonical JSON artifact for non-TS consumers (Python research scripts). */
export function buildProvidersJson(input: CodegenInput): string {
  const doc = {
    $schema: "sovereign-providers/v1",
    generatedAt: new Date().toISOString(),
    generator: "@sovereign/providers codegen — DO NOT EDIT BY HAND",
    ...(input.provenance ? { provenance: input.provenance } : {}),
    adapters: ["openai", "google-v1beta", "mistral", "static", "none"],
    providers: input.defs.map((d) => ({
      name: d.name,
      ...(d.displayName ? { displayName: d.displayName } : {}),
      baseUrl: d.baseUrl,
      keyEnv: d.keyEnv,
      ...(d.keyEnvAlt ? { keyEnvAlt: d.keyEnvAlt } : {}),
      adapter: d.adapter,
      ...(d.modelsPath ? { modelsPath: d.modelsPath } : {}),
      ...(d.auth ? { auth: d.auth } : {}),
      ...(d.headerName ? { headerName: d.headerName } : {}),
      ...(d.queryParam ? { queryParam: d.queryParam } : {}),
      ...(d.extraHeaders ? { extraHeaders: d.extraHeaders } : {}),
      ...(d.staticModels ? { staticModels: d.staticModels } : {}),
      ...(d.noModelsReason ? { noModelsReason: d.noModelsReason } : {}),
      ...(d.enabled === false ? { enabled: false } : {}),
      ...(d.routerLocal ? { routerLocal: true } : {}),
    })),
    // Seeds are cold-start data only; the JSON documents that contract.
    seeds: Object.fromEntries(input.defs.map((d) => [d.name, d.seeds])),
    seedsContract:
      "Cold-start only: served while a provider has never had a successful discovery; inert afterwards. Never hand-edit model membership here — discovery owns it.",
    aliases: input.aliases,
    deadIds: [...input.deadIds].sort(),
    deadIdsContract:
      "Permanent hand-managed tier (EOL notices). Never served, never re-admitted by discovery.",
  };
  return JSON.stringify(doc, null, 2) + "\n";
}

/**
 * Generated Go data file for herd. Package name and exported symbols are
 * chosen to be a drop-in data replacement for herd's hardcoded tables; herd's
 * own merge/selection LOGIC stays hand-written and reads these tables.
 *
 * The type is CatalogProviderDef (not ProviderDef) — herd's registry.go
 * already declares ProviderDef for the extended 9Router registry.
 */
export function buildProvidersGo(input: CodegenInput): string {
  const generatedAt = new Date().toISOString();
  const defStructs = input.defs
    .map((d) => {
      const fields = [
        `\t\tName:           ${jsonEscaped(d.name)},`,
        `\t\tBaseURL:        ${jsonEscaped(d.baseUrl)},`,
        `\t\tKeyEnv:         ${jsonEscaped(d.keyEnv)},`,
        `\t\tKeyEnvAlt:      ${jsonEscaped(d.keyEnvAlt ?? "")},`,
        `\t\tAdapter:        ${jsonEscaped(d.adapter)},`,
        `\t\tAuth:           ${jsonEscaped(d.auth ?? "")},`,
        `\t\tHeaderName:     ${jsonEscaped(d.headerName ?? "")},`,
        `\t\tQueryParam:     ${jsonEscaped(d.queryParam ?? "")},`,
        `\t\tModelsPath:     ${jsonEscaped(d.modelsPath ?? "")},`,
        `\t\tNoModelsReason: ${jsonEscaped(d.noModelsReason ?? "")},`,
        `\t\tNoAuth:         ${d.auth === "none" ? "true" : "false"},`,
        `\t\tRouterLocal:    ${d.routerLocal ? "true" : "false"},`,
        `\t\tEnabled:        ${d.enabled === false ? "false" : "true"},`,
      ];
      return `\t{\n${fields.join("\n")}\n\t},`;
    })
    .join("\n");

  // gofmt does not column-align map entries whose values are composite
  // literals (seeds/static): emit keys unpadded.
  const seedsGo = input.defs
    .map((d) => `\t${jsonEscaped(d.name)}: ${goStringSlice(d.seeds)},`)
    .join("\n");

  const staticGo = input.defs
    .filter((d) => d.adapter === "static")
    .map((d) => `\t${jsonEscaped(d.name)}: ${goStringSlice(d.staticModels ?? [])},`)
    .join("\n");

  const provenance = input.provenance ? input.provenance : "unknown";

  return `// Code generated by @sovereign/providers — DO NOT EDIT BY HAND.
// Regenerate with: bun run build  (in packages/providers)
// Source of truth: packages/providers/src/data.ts
// Generated at: ${generatedAt}

package astmatrix

// CatalogProvenance identifies the package revision this file was generated
// from (litellm-style provenance carried into the artifact).
const CatalogProvenance = ${jsonEscaped(provenance)}

// CatalogProviderDef mirrors the catalog's provider definition (data only).
// Named to avoid colliding with registry.go's ProviderDef (extended registry).
type CatalogProviderDef struct {
	Name           string
	BaseURL        string
	KeyEnv         string
	KeyEnvAlt      string
	Adapter        string // openai | google-v1beta | mistral | static | none
	Auth           string // bearer | x-api-key | query-key | none
	HeaderName     string // auth === "x-api-key"
	QueryParam     string // auth === "query-key"
	ModelsPath     string
	NoModelsReason string
	NoAuth         bool // auth === "none": no API key needed
	RouterLocal    bool // TS-router-local concept; herd skips these
	Enabled        bool
}

// ProviderCatalogDefs is the canonical provider table.
var ProviderCatalogDefs = []CatalogProviderDef{
${defStructs}
}

// ProviderCatalogSeeds: cold-start seeds ONLY. Served while a provider has
// never had a successful discovery; inert afterwards. Discovery owns
// membership — never add live models here. Seeds may name dead IDs; the
// catalog filters deadIds everywhere (cold start included).
var ProviderCatalogSeeds = map[string][]string{
${seedsGo}
}

// ProviderCatalogStaticModels: adapter "static" providers carry their list
// in the definition (no /models endpoint to discover).
var ProviderCatalogStaticModels = map[string][]string{
${staticGo}
}

// ProviderCatalogAliases: friendly alias -> [provider, model] (UX layer).
var ProviderCatalogAliases = ${goAliasMap(input.aliases)}

// ProviderCatalogDeadIDs: permanent hand-managed tier (EOL notices).
// Never served, never re-admitted by discovery.
var ProviderCatalogDeadIDs = ${goStringSlice([...input.deadIds].sort(), "\t", "")}
`;
}

/** Emit both artifacts into outDir. Returns the written paths. */
export async function emitAll(
  outDir: string,
  input: CodegenInput,
): Promise<{ jsonPath: string; goPath: string }> {
  const { promises: fs } = await import("node:fs");
  const { join } = await import("node:path");
  await fs.mkdir(outDir, { recursive: true });
  const jsonPath = join(outDir, "providers.json");
  const goPath = join(outDir, "providers.go");
  await fs.writeFile(jsonPath, buildProvidersJson(input), "utf8");
  await fs.writeFile(goPath, buildProvidersGo(input), "utf8");
  return { jsonPath, goPath };
}
