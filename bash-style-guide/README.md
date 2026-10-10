<div align="center">

# estate - bash-style-guide

**A style guide for writing safe, predictable, portable Bash in the estate.**

[![Forked from bahamas10](https://img.shields.io/badge/forked%20from-bahamas10-blue?style=for-the-badge)](https://github.com/bahamas10/bash-style-guide)
[![Forked from asc4asc](https://img.shields.io/badge/forked%20from-asc4asc-blue?style=for-the-badge)](https://github.com/asc4asc/bash-style-guide)
[![Forked from guitarrapc](https://img.shields.io/badge/forked%20from-guitarrapc-blue?style=for-the-badge)](https://github.com/guitarrapc/bash-styleguide)
[![Forked from easybash](https://img.shields.io/badge/forked%20from-easybash-blue?style=for-the-badge)](https://github.com/easybash/bash-coding-style-guide)
[![Forked from org-ai-assisted](https://img.shields.io/badge/forked%20from-org--ai--assisted-blue?style=for-the-badge)](https://github.com/org-ai-assisted/developer-meta-files)

*Synthesised for the assisted-by-AI era. Rules carry flat R-NNN ids so they can be cited in code review, commit messages, and PR replies.*

<p align="center">
  <a href="#contents">Contents</a>  ·
  <a href="docs/forked-from/">Forked from</a>  ·
  <a href="CHANGELOG.md">Changelog</a>  ·
  <a href="CONTRIBUTING.md">Contributing</a>  ·
  <a href="LICENSE">License</a>
</p>

</div>

---

## Contents

1. [Shebang](#1-shebang)
2. [Indentation](#2-indentation)
3. [Line length](#3-line-length)
4. [Section dividers](#4-section-dividers)
5. [Conditionals](#5-conditionals)
6. [Variables](#6-variables)
7. [Loops](#7-loops)
8. [Functions](#8-functions)
9. [Arithmetic](#9-arithmetic)
10. [Comments](#10-comments)
11. [File headers](#11-file-headers)
12. [Error handling](#12-error-handling)
13. [ASCII only](#13-ascii-only)
14. [Naming](#14-naming)
15. [Tooling](#15-tooling)
16. [Forks and provenance](#16-forks-and-provenance)

---

## 1. Shebang

Use `#!/usr/bin/env bash`. Never `#!/bin/bash`, never `#!/bin/sh`.

```bash
#!/usr/bin/env bash
```

**Why.** `env` resolves `bash` through `PATH`, so the interpreter is swappable without editing every file. The absolute path `/bin/bash` breaks on NixOS, macOS Homebrew, and any host where bash is installed elsewhere. `sh` is not bash; the whole guide assumes bash semantics.

**R-101.** Every executable shell file begins with the env shebang.

---

## 2. Indentation

**2 spaces. No tabs.**

**Why.** bahamas10 uses tabs. asc4asc changed to 2 spaces because "spaces (2) because I often change the editor and the system". The estate follows asc4asc. Tabs render at different widths across tools, which breaks diff review and LLM token alignment.

**R-201.** Two spaces per level. No tabs.

**R-202.** Continuation lines indent one additional level.

```bash
some_command \
    --flag-a \
    --flag-b
```

---

## 3. Line length

**Columns do not exceed 80.**

**Why.** Both bahamas10 and the Google Shell Style Guide mandate this. 80 columns fits two panes side-by-side on any laptop, survives terminal resizes, and keeps rendered code blocks from horizontal-scrolling. Long URLs in comments are the only exception.

**R-301.** 80 columns maximum. URL-in-comment is the sole exception.

---

## 4. Section dividers

**Use `# --- NN - name ---`. One line. No stacking.**

**Why.** ShellCheck [SC2273](https://www.shellcheck.net/wiki/SC2273) flags a bare `=====` as a possible merge conflict. Box-drawing characters are non-ASCII and violate R-1301.

**Correct.**

```bash
# --- 05 - _evalcache ---
```

**Avoid.**

```bash
# ===================
```

**R-401.** Section headers use `# --- NN - name ---`. One line, ASCII, numbered.

**R-402.** Never a bare `=====` without a `#` prefix.

**R-403.** Never box-drawing characters in source files.

---

## 5. Conditionals

**Use `[[ ... ]]`. Never `[ ... ]` or `test`.**

**Why.** `[[ ]]` is a bash keyword: it does not word-split, does not glob-expand, supports `&&`/`||`, and supports `==` pattern matching. `[ ]` is an external command on some systems and a builtin on others, with subtly different behaviour.

**R-501.** `[[ ... ]]` for all conditionals. `[ ... ]` is forbidden in new code.

**R-502.** Semicolons are permitted only in control statements.

---

## 6. Variables

**Quote every expansion.**

```bash
"$var"          not   $var
"${arr[@]}"     not   ${arr[@]}
"${PROMPT_COMMAND:-}"   not   "$PROMPT_COMMAND"
```

**Why.** Unquoted expansions word-split on `IFS` and glob-expand. `"$var"` is the only form that survives paths with spaces, empty values, and filenames containing `*`.

**R-601.** Quote every expansion.

**R-602.** `${var:-}` when the variable may be unset.

**R-603.** `local` for every variable inside a function.

---

## 7. Loops

**Use `{1..5}` or C-style `for ((...))`. Never `$(seq ...)`.**

**Why.** `seq` is an external binary. Brace expansion and C-style `for` are bash builtins.

**R-701.** `{1..N}` or C-style `for`. Never `$(seq ...)`.

---

## 8. Functions

**No `function` keyword. Use `foo() { ... }`.**

**R-801.** `foo() { ... }` only.

**R-802.** Internal helpers use a leading underscore: `_helper()`.

---

## 9. Arithmetic

**Use `((...))` and `$((...))`. Never `let`. Never bare `(( expr ))` under errexit.**

```bash
count=$((count + 1))     # correct: assignment rc is 0
(( count += 1 ))         # WRONG under set -e when result is 0
```

**Why.** R-012 from org-ai-assisted/developer-meta-files: under `set -e`, an arithmetic expression that evaluates to zero returns rc=1 and exits the shell. The assignment form `var=$((expr))` has rc=0 regardless of the expression value.

**R-901.** `var=$((expr))`, never `(( expr ))` as a standalone statement.

**R-902.** Never `let`.

---

## 10. Comments

**State why, not what. A comment that narrates the line below it is deleted, not edited.**

**Why.** [sarev/scale](https://github.com/sarev/scale) runs a restatement filter: "A comment that just narrates the line below it (increment the counter) is rejected." The estate adopts this standard.

**Correct.**

```bash
# Retry because the vendor API is flaky under load.
curl --retry 3 "$url"
```

**Avoid.**

```bash
# Retry the curl command three times.
curl --retry 3 "$url"
```

**R-1001.** Comments explain why. Restatement comments are removed.

**R-1002.** Preserve hand-written rationale verbatim when editing a file.

**R-1003.** Cite rules when a block enforces one: `# See R-901.`

---

## 11. File headers

Every executable shell file carries a header. Every AI-touched file additionally carries `## AI-Assisted`.

```bash
#!/usr/bin/env bash
# ---
# <one-line purpose>
#
# <optional context, escape hatches, related files>
# ---
```

**R-1101.** File header is mandatory.

**R-1102.** AI-touched files carry `## AI-Assisted` on its own line.

---

## 12. Error handling

**Standalone scripts use strict mode:**

```bash
set -o errexit
set -o nounset
set -o pipefail
set -o errtrace
shopt -s inherit_errexit
shopt -s shift_verbose
```

**Dotfiles are exempt.** An interactive shell cannot tolerate errexit; every sourced snippet would be a landmine. Never toggle errexit on and off mid-file.

**R-1201.** Standalone scripts: strict mode block at the top.

**R-1202.** Dotfiles: no strict mode, ever.

**R-1203.** Never `set +e` mid-script. Wrap failing commands: `cmd || true`.

---

## 13. ASCII only

**No smart quotes, em dashes, arrows, zero-width spaces, emoji.**

**Why.** R-001 from org-ai-assisted/developer-meta-files: "AI tools reflexively render text with cosmetic unicode (U+2014 em dash, U+2192 right-arrow); strip them." ASCII-only files make the pre-push gate possible:

```bash
LC_ALL=C grep -PlI "[^\x00-\x7F]" .
```

**R-1301.** Source files contain only ASCII bytes.

**R-1302.** Commit messages are ASCII only.

**R-1303.** Pre-push gate runs the grep above and blocks on any output.

---

## 14. Naming

| Kind | Convention | Example |
|---|---|---|
| Variables | lowercase_with_underscores | `request_count` |
| Constants | UPPERCASE, readonly | `readonly MAX_RETRIES=3` |
| Environment vars | UPPERCASE | `PI_DISABLE_UUTILS_BUILTINS` |
| Internal functions | `_leading_underscore` | `_evalcache` |
| Public functions | lowercase | `readme-check` |

**R-1401.** Follow the table.

---

## 15. Tooling

**ShellCheck runs on every PR.** Warning severity and above blocks merge. Inline `# shellcheck disable=SCXXXX` directives require a comment explaining the specific false positive.

**shfmt formats the tree:**

```bash
shfmt -i 2 -ci -sr -w .
```

- `-i 2` two-space indent (R-201)
- `-ci`  switch-case body indented
- `-sr`  redirect operators followed by a space

**EditorConfig** (`.editorconfig`) enforces indent style at the editor layer.

**R-1501.** ShellCheck on every PR; warning+ blocks merge.

**R-1502.** shfmt invocation is `-i 2 -ci -sr`.

**R-1503.** `.editorconfig` sets `indent_style = space`, `indent_size = 2`.

---

## 16. Forks and provenance

This guide is a fork and synthesis. The sources are documented under [`docs/forked-from/`](docs/forked-from/). Rules that derive from a specific upstream are cited inline.

| Upstream | Repo | Contributes |
|---|---|---|
| bahamas10 | [github.com/bahamas10/bash-style-guide](https://github.com/bahamas10/bash-style-guide) | Shebang, bashisms, `[[ ]]`, functions |
| asc4asc | [github.com/asc4asc/bash-style-guide](https://github.com/asc4asc/bash-style-guide) | 2-space indent (fork of bahamas10) |
| guitarrapc | [github.com/guitarrapc/bash-styleguide](https://github.com/guitarrapc/bash-styleguide) | File header, consistency rule, Google Shell Style alignment |
| easybash | [github.com/easybash/bash-coding-style-guide](https://github.com/easybash/bash-coding-style-guide) | `source` over `.`, array patterns |
| org-ai-assisted | [github.com/org-ai-assisted/developer-meta-files](https://github.com/org-ai-assisted/developer-meta-files) | R-001, R-010, R-011, R-012 |
| sarev/scale | [github.com/sarev/scale](https://github.com/sarev/scale) | Why-not-what comment filter |
| ShellCheck | [shellcheck.net/wiki/SC2273](https://www.shellcheck.net/wiki/SC2273) | Separator rule |
| Google | [google.github.io/styleguide/shell.xml](https://google.github.io/styleguide/shell.xml) | 80-col, function names |

**R-1601.** New rules must cite the upstream they derive from or be marked `estate-original`.

---

<div align="center">

**Forked with intent. Broken deliberately where the upstream disagreed.**

</div>
