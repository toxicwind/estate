# pd-mcp

Star-grade ProjectDiscovery MCP server (Bun/TypeScript). Wraps the estate's
PD Go binaries as MCP tools over stdio JSON-RPC with `Content-Length` framing —
same protocol conventions as `tools/tmux-mcp/server.ts`
(`initialize` → `tools/list` → `tools/call`).

Runs **on yote**, where the binaries live. It never runs on the cell.

## Tools

| Tool | Binary | What it does | Heavy? |
|------|--------|--------------|--------|
| `pd_httpx` | `/home/toxic/.pdtm/go/bin/httpx` | HTTP probing: status, title, tech detect | — |
| `pd_dnsx` | `/home/toxic/.pdtm/go/bin/dnsx` | DNS recon: A/AAAA/CNAME/TXT/MX/NS/SRV/PTR/SOA/CAA | — |
| `pd_shuffledns` | `/home/toxic/go/bin/shuffledns` | Mass subdomain bruteforce (needs wordlist + resolvers file; bruteforce mode needs `massdns` on PATH) | ⚠︎ |
| `pd_subfinder` | `/home/toxic/.pdtm/go/bin/subfinder` | Passive subdomain enumeration | — |
| `pd_naabu` | `/home/toxic/.pdtm/go/bin/naabu` | Port scan (unprivileged connect scan; `-scan-type c`) | ⚠︎ |
| `pd_nuclei` | `/home/toxic/.pdtm/go/bin/nuclei` | Vulnerability scan — **DESTRUCTIVE-GATED: requires `confirm: true`** | ⚠︎ |
| `pd_katana` | `/home/toxic/.pdtm/go/bin/katana` | Web crawler (needs `http(s)://` seed URL) | — |
| `pd_tlsx` | `/home/toxic/.pdtm/go/bin/tlsx` | TLS recon: cert, cipher, expiry for `host[:port]` | — |

Heavy tools (⚠︎: `pd_naabu`, `pd_nuclei`, `pd_shuffledns`) share a **max-2
concurrent** gate. Extra heavy calls queue until a slot frees.

## Parameters

Every tool accepts `timeout_sec` (sane per-tool defaults: httpx/dnsx/tlsx 60,
subfinder 120, naabu 180, katana/shuffledns 300, nuclei 600; hard max 3600).

- `pd_httpx`: `target` (URL or host/IP), `include_title` (default true),
  `tech_detect` (default true).
- `pd_dnsx`: `target` (domain), `types` (default `[A,AAAA,CNAME,TXT,MX]`),
  `resolver` (optional IPv4).
- `pd_shuffledns`: `domain`, `wordlist` (existing file), `resolvers`
  (existing file, one IP/line), `mode` = `bruteforce` (default) | `resolve`.
- `pd_subfinder`: `domain`.
- `pd_naabu`: `target`, `ports` (default top 100; e.g. `"80,443"` or `"1-1000"`).
- `pd_nuclei`: `target`, `confirm: true` (**required**), `templates` (optional
  `-t` path), `severity` (default `"critical,high"`), `rate_limit` (default 150).
- `pd_katana`: `target` (http(s) URL), `depth` (1–10, default 3).
- `pd_tlsx`: `target` (`host` or `host:port`).

## Hardening

- **No shell, ever.** Binaries are spawned via argv arrays — no shell string
  interpolation, no injection surface.
- **Input validation** on every tool: empty targets rejected; domains/hosts/IPs
  checked against regex; URLs must be `http(s)://`; port specs, severity
  strings, depth, and resolver IPs are format-checked.
- **Timeouts** on every invocation; timed-out processes are SIGKILLed and
  reported as `-32603`.
- **Structured errors**: `-32601` unknown tool/method, `-32602` invalid params
  (including missing `confirm:true` on `pd_nuclei`), `-32603` execution failure
  with an stderr excerpt.
- **Startup check**: every binary is probed for execute permission at launch;
  the server exits 1 with a clear message naming the missing binary instead of
  failing mid-call.
- **Logging**: all diagnostics go to stderr with a `[pd-mcp]` prefix. stdout
  carries only framed RPC replies (a stray byte on stdout breaks the framing).
- Large outputs are capped at 120k chars with a truncation note.

## Run it

```sh
cd /home/toxic/estate/tools/pd-mcp
bun run server.ts
```

Minimal stdio probe (bash):

```sh
req() { local m="$1"; local n=$(( ${#m} )); printf 'Content-Length: %d\r\n\r\n%s' "$n" "$m"; }
{
  req '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
  req '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
  req '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"pd_tlsx","arguments":{"target":"pollinations.ai"}}}'
} | bun run server.ts | tr '\r' '\n' | grep -v '^$'
```

## MCP client config

```json
{
  "mcpServers": {
    "pd": {
      "command": "bun",
      "args": ["run", "/home/toxic/estate/tools/pd-mcp/server.ts"]
    }
  }
}
```

## Examples

Probe a host over HTTPS:

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call",
 "params":{"name":"pd_httpx",
  "arguments":{"target":"https://gen.pollinations.ai","tech_detect":true}}}
```

A-record lookup:

```json
{"jsonrpc":"2.0","id":4,"method":"tools/call",
 "params":{"name":"pd_dnsx",
  "arguments":{"target":"pollinations.ai","types":["A","MX","TXT"]}}}
```

Gated nuclei scan (refused without `confirm:true`):

```json
{"jsonrpc":"2.0","id":5,"method":"tools/call",
 "params":{"name":"pd_nuclei",
  "arguments":{"target":"https://example.com","confirm":true,"severity":"critical,high"}}}
```
