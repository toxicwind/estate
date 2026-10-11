---
name: use-ffs-grep-not-bare-grep
description: "Use ffs grep --root instead of bare grep in bash commands"
condition: "\\b(grep|egrep|fgrep)\\s+"
scope: "tool:bash"
---

Never use bare `grep`, `egrep`, or `fgrep` in bash commands. Use `ffs grep --root <dir> <needle>` instead for all code and file content searches.