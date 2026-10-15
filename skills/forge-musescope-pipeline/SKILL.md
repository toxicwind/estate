# forge-musescope-pipeline

Modular Bun framework for musescope JSON → parquet → ferret-den analysis pipeline.

## What it does

1. **Parse** musescope JSON (brand, join, hatch, crypto sections)
2. **Convert** each section to its own parquet table
3. **Analyze** via duckdb SQL queries
4. **Recon** via ferret-den tools (subfinder, dnsx, etc.)

## Usage

```bash
# Run full pipeline
bun run bin/forge-musescope.ts

# With custom input/output
bun run bin/forge-musescope.ts --input /path/to/musescope.json --output /path/to/output

# Skip analysis or ferret-den
bun run bin/forge-musescope.ts --skip-analysis --skip-ferret

# Only run ferret-den recon
bun run bin/forge-musescope.ts --ferret --domain example.com
```

## Config

Config persists at `~/.forgemscp/config.json`. Tampermonkey-style `GM_getValue`/`GM_setValue` API available:

```typescript
import { config, GM_getValue, GM_setValue } from './src/config.js';

config.setValue('reconDomain', 'example.com');
const domain = config.getValue('reconDomain', '');
```

## Module structure

```
bin/forge-musescope.ts   # CLI entry point
src/config.ts            # Tampermonkey-style GM config shim
src/index.ts             # Main pipeline orchestrator
src/stages/parse.ts      # Stage 1: JSON parsing
src/stages/convert.ts    # Stage 2: Parquet conversion
src/stages/analyze.ts    # Stage 3: SQL analysis via duckdb
src/stages/ferret.ts     # Stage 4: Ferret-den recon integration
```

## Pattern references

- dots_function_call pattern: vllm-project/vllm dots_tool_parser.py
- dots_function_call pattern: sgl-project/sglang dots_detector.py