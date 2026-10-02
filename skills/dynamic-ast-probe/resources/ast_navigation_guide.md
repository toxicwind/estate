# Dynamic AST Navigation Guide for Gemma 4 SWE Agents

## 1. When to Use Dynamic AST Navigation
The competition's static precomputed graph (`get_code_neighbors`, `search_similar_code`) has verified blind spots:
- Asynchronous function declarations (`async def`) are completely omitted from the graph node registry in major libraries (e.g., FastAPI, HTTPX).
- Direct call-edges for async dependencies fail to return.

## 2. Using `.dynamic_symbols.json`
When `search_similar_code` or `get_code_neighbors` fails:
1. Run `python3 skills/dynamic_ast_probe/scripts/ast_indexer.py`.
2. Inspect the resulting `.dynamic_symbols.json` via:
   `run_command("python3 -c 'import json; d=json.load(open(\".dynamic_symbols.json\")); print(d[\"symbols\"].get(\"<symbol_name>\", []))'")`
3. Retrieve exact line bounds (`line_start`, `line_end`) and call `read_file(filepath, line_start, line_end)` for surgical inspection.

## 3. Preservation Invariants
- When modifying code via `edit_file`, preserve existing decorators (`@app.get`, `@router.post`, etc.).
- Never convert `async def` to `def` or remove `await` expressions unless explicitly mandated by the issue description.
