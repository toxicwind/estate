# flicker — Local Build Daemon

`flicker` is the local-only, pitchfork-supervised build daemon listening on `127.0.0.1:25148`. It executes jobs directly via the local backend (no containers, no remote forges) with content-hash caching for identical job deduplication.

## Why flicker Matters

1. **Local-Only Execution**:
   - Jobs run directly on the host via bash login shells (mise toolchains resolve).
   - No Docker, no Kubernetes, no remote forge dependencies.
2. **Content-Hash Caching**:
   - Identical job specs (command, env, workdir, etc.) return CACHED on resubmit.
   - Eliminates redundant executions across agent turns.
3. **Direct Job API**:
   - Simple HTTP API: POST /api/jobs, GET /api/jobs/:id, GET /api/jobs/:id/logs.
   - No authentication (single-tenant daemon).

## Health Check & Status

```bash
# Basic health check via HTTP
curl -fsS http://127.0.0.1:25148/api/health

# Response format:
# {"ok":true,"service":"flicker","running":0,"cache":{"entries":N},"time":"..."}
```

## API Usage

### 1. Submit a Job (POST /api/jobs)

```bash
curl -s -X POST http://127.0.0.1:25148/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-job",
    "command": "echo hello",
    "workdir": "/tmp",
    "env": {"FOO": "bar"},
    "timeout": 300
  }'
# Returns: {"id":1,"number":1,"name":"my-job","status":"pending","hash":"...","created":...}
```

Job spec fields:
- `name` (string): job name
- `command` (string): shell command to run (required, or use `script`)
- `script` (string): multi-line script (alternative to command)
- `workdir` (string): working directory
- `env` (object): environment variables
- `timeout` (int): timeout in seconds (0 = no timeout)
- `cache_key` (string): additional cache key component
- `artifacts` (array): artifact paths to collect

### 2. Get Job Status (GET /api/jobs/:id)

```bash
curl -s http://127.0.0.1:25148/api/jobs/1
# Returns: {"id":1,"status":"success","hash":"...","started":...,"finished":...,"duration_ms":...}
```

Status values: `pending`, `running`, `success`, `failure`, `canceled`, `error`.

### 3. Get Job Logs (GET /api/jobs/:id/logs)

```bash
curl -s http://127.0.0.1:25148/api/jobs/1/logs
# Returns: plain text logs
```

### 4. List Jobs (GET /api/jobs)

```bash
curl -s http://127.0.0.1:25148/api/jobs
# Returns: array of job objects
```

## Cache Behavior

If an identical job (same content hash) was previously successful, POST /api/jobs returns immediately with:
```json
{"id":1,"status":"success","cached":true,"message":"CACHED","hash":"..."}
```

The hash covers: command/script, workdir, env (sorted), cache_key, artifacts (sorted).

## Migration from buildsrv/brand

Flicker replaces the Python buildsrv/brand daemon. Key differences:
- **Port**: Same (25148) — drop-in replacement.
- **API**: `/api/jobs` instead of buildsrv's endpoints. Simpler, no auth.
- **Execution**: Direct local bash (not Python subprocess with custom caching).
- **State**: Migrated from `/home/toxic/brand/` to `/home/toxic/flicker/migrated-brand/`.

## Daemons

Pitchfork supervises:
- `sovereign/flicker` — the server (port 25148, gRPC 25240)
- `sovereign/flicker-agent` — the local execution agent

## CLI

The `flicker` CLI (at `/home/toxic/estate/projects/range/ranch/flicker/bin/flicker`) provides:
- `flicker submit` — submit a job
- `flicker status` — check job status
- `flicker logs` — fetch logs
- `flicker list` — list jobs
- `flicker health` — health check