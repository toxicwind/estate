# Strict Bash Guard Extension (`strict-bash-guard`)

In-process safety guard for Tau that blocks shell commands duplicating built-in agent capabilities (`find`, `fd`, `cat`) to enforce AST tool usage and prevent context flooding.

## Testing
```bash
bun test /home/toxic/estate/config/tau/extensions/strict-bash-guard/index.test.ts
```
