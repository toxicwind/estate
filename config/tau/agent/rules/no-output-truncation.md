---
name: no-output-truncation
description: "Never truncate command output with head/tail/cut/grep-limit — persist full output to a file and read it back"
condition: "\\b(head|tail|cut)\\s+[-\\-a-zA-Z0-9]*\\s*\\S|\\|\\s*(head|tail)\\b|\\bcut\\s+-c\\d|\\bsed -n\\s+['\\\"]?[0-9]"
scope: "tool"
---

Truncated output is not a result.

**Never** pipe through `head`, `tail`, `cut -c`, `grep ... | head`, or `sed -n '1,Np'`. Switching from `head -20` to `cut -c1-220` is the same defect wearing a hat — both silently discard data, and the user cannot tell how much was dropped.

**Do this instead:**

1. Write the full output to a file: `cmd > /tmp/out.txt 2>&1`
2. Report the size: `wc -l /tmp/out.txt`
3. Read the file with the `read` tool using explicit line ranges — `:1-200`, `:200-400`, paging as needed.

```bash
# WRONG — you have now lost everything past line 20
jscpd ... | head -25

# RIGHT — nothing lost, read it back in ranges
jscpd ... > /tmp/jscpd.txt 2>&1; wc -l /tmp/jscpd.txt
```

Same rule for `tee` redirection and for any `-m`/`-n` limit flags on tools that take them (`grep -m1`, `gh --limit N`). Those are truncation too.

If output is genuinely huge, say so with the real line count and let the user decide what to page through. An honest "12,000 lines, here are the 200 that matter" beats a silent 20-line window that implies it is everything.