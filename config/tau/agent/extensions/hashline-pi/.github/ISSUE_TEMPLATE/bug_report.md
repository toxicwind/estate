---
name: Bug report
about: A hashline patch didn't do what the docs say it should
title: '[bug] '
labels: bug
---

## What happened

A short description of what you expected the patch to do and what it
actually did.

## Minimal reproducing patch

Paste the smallest hashline patch that reproduces the failure, redacted
of any private paths. Include the file content it was authored against
(or the exact `read` output the tag was minted from).

```
[example/path.ts#XXXX]
SWAP 1.=1:
+…
```

## Exact error / output

Copy the error message or wrong output verbatim from the Pi agent's
console.

## Environment

- `bun --version`:
- `hashline-pi` commit SHA:
- `@earendil-works/pi-coding-agent` version:
- OS + arch (`uname -a` or Windows build):

## Notes

Anything else that seems relevant — extension config, workspace layout,
symlinks, unusual filesystem, etc.
