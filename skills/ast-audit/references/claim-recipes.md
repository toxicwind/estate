# Claim recipes — natural-language claim -> ast-grep pattern

Conventions: `$X` = one AST node, `$$$` = zero or more nodes. Always
single-quote patterns in shell. `--lang` per file type: `py ts tsx js go rs`.

## 1. "X listens on / serves port N"

The claim is structural only if the port literal (or a named constant resolving
to it) appears in a listen/serve call. Two-step: find bind sites, then check
the captured port.

```bash
# TypeScript / Bun
ast-grep run -p 'app.listen($PORT, $$$)' --lang ts --json=compact <root>
ast-grep run -p 'Bun.serve({ $$$ })' --lang ts --json=compact <root>   # then read port: $X inside
ast-grep run -p 'server.listen($PORT, $$$)' --lang ts --json=compact <root>

# Python
ast-grep run -p 'app.listen($PORT)' --lang py --json=compact <root>
ast-grep run -p 'uvicorn.run($$$, port=$PORT, $$$)' --lang py --json=compact <root>
ast-grep run -p 'serve_forever($$$)' --lang py --json=compact <root>

# Go
ast-grep run -p 'http.ListenAndServe($ADDR, $$$)' --lang go --json=compact <root>
ast-grep run -p 'log.Fatal(http.ListenAndServe($ADDR, $$$))' --lang go --json=compact <root>

# Rust
ast-grep run -p 'axum::Server::bind($ADDR)' --lang rs --json=compact <root>
```

Verdict rule: VERIFIED iff a hit's `$PORT`/`$ADDR` meta-variable text contains
the claimed port number (or a constant whose definition — checked separately —
equals it). A bare `rg 25104` hit in a comment is NOT a verification.

## 2. "function X calls Y"

Relational claim: needs `inside`/`has`, and `stopBy: end` so the search walks
the whole function body (amp-contrib's hard-won rule).

```yaml
# calls.yml — does X call Y? fill in X and Y
id: x-calls-y
language: TypeScript
rule:
  all:
    - pattern: $Y($$$)          # the call site
    - inside:
        kind: function_declaration
        has: { pattern: 'function $X($$$)' }
        stopBy: end
```

```bash
ast-grep scan --inline-rules "
id: x-calls-y
language: Python
rule:
  all:
    - pattern: \$Y(\$\$\$)
    - inside:
        kind: function_definition
        has: { pattern: 'def $X($$$)' }
        stopBy: end" <root>
```

Simpler two-pass alternative (no YAML): find X's definition lines, then run a
call pattern limited to that file and check the hit's line range falls inside
X's body. `forge audit` does this automatically.

## 3. "module A imports B"

```bash
# ES imports — capture the specifier, filter substring in code
ast-grep run -p 'import $$$ from $SPEC' --lang ts --json=compact <root>
ast-grep run -p 'import $SPEC' --lang ts --json=compact <root>
# Python
ast-grep run -p 'from $MOD import $$$' --lang py --json=compact <root>
ast-grep run -p 'import $MOD' --lang py --json=compact <root>
# Go
ast-grep run -p 'import ( $$$ $SPEC $$$ )' --lang go --json=compact <root>
# dynamic require
ast-grep run -p 'require($SPEC)' --lang ts --json=compact <root>
```

**String literals match exactly** — `import $$$ from 'router_config'` will NOT
match `from "./router_config.ts"`. Always capture the specifier (`$SPEC`,
`$MOD`) and substring-filter the captured text. `forge audit` does this
automatically.

## 4. "class X defines method Y" / "X has field F"

```bash
ast-grep scan --inline-rules "
id: x-defines-y
language: TypeScript
rule:
  kind: class_declaration
  has:
    pattern: '$Y($$$) { $$$ }'
    stopBy: end" <root>
# then check the enclosing class name == X from the matched text
```

## 5. "config key K = V" — NOT structural, use rg

ast-grep parses code, not YAML/TOML/INI. For config values:

```bash
rg -n "^\s*K\s*[:=]" <root> --glob '*.yml' --glob '*.yaml' --glob '*.toml'
```

Quote the rg line as supporting evidence only. If the value feeds code
(e.g. `PORT = config.port`), verify the *code side* structurally (recipe 1)
and cite the config line as the value's source.

## 6. Debugging a pattern that returns 0 matches

In order (from the registry skill's field guide):

1. `ast-grep run -p '<pattern>' --lang <l> --debug-query=pattern --stdin <<< ''`
   — if the pattern AST shows ERROR nodes, the pattern is malformed.
2. `ast-grep run -p '$_' --lang <l> --debug-query=cst <file> | head -40`
   — find the real `kind` name for what you're matching.
3. Check `--lang` matches the file (`tsx` needs `--lang tsx`, not `ts`).
4. For `inside`/`has`: add `stopBy: end`.
