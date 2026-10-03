# OpenRouter Catalog Intelligence

## Reconnaissance (2026-10-02)

### Subdomain Discovery
Extensive footprint mapped via `pd:subfinder` & `pd:httpx`. Key subdomains:
- `mcp.openrouter.ai` (404, Cloudflare) - Potential future native MCP integration plane.
- `tool-playground.openrouter.ai` (200, Cloudflare) - Tool testing SPA.
- `eu.openrouter.ai` (200, Cloudflare) - European regional endpoint.
- `tool-calling.openrouter.ai` (200, Vercel) - Tool calling demo environment.
- `status.openrouter.ai` (307 redirect to statuspage) - Infrastructure status.

### EU Regional Endpoint Analysis (`eu.openrouter.ai/api/v1/models`)
- **Total Models**: 69
- **Zero-Cost Models**: 0 (none available via EU region API)
- **Key Providers**: Anthropic (`claude-opus-5.5`, etc.), Google (`gemini-3.5-flash-lite`, etc.), Mistral (`devstral-2512`, `mistral-large-2512`), Moonshot (`kimi-k2.7-code`), OpenAI (`gpt-6-luna`, `gpt-oss-120b`).
- Indicates stricter regulatory segmentation or separate commercial agreements for the EU operating zone. 

### Infrastructure & Telemetry
- Active protection via Cloudflare Bot Management on primary API and media endpoints.
- Widespread use of Vercel for frontend surfaces (`tool-calling`, `preview`).
- Internal endpoints tracked but restricted (`argocd.internal`, `grafana.internal`).

### Next.js API Surface Extraction
Crawl via `pd:katana` over `tool-calling.openrouter.ai` returned heavy chunked delivery mechanisms. Tooling indicates client-side orchestration relying on cross-origin requests back to primary `.ai` APIs.
