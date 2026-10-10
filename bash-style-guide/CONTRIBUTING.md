# Contributing

Rules are flat-numbered. New rules take the next free number in their
area. Renumbering is forbidden -- downstream commits cite rule ids.

## Before you open a PR

1. Run ShellCheck at warning level and above. Fix every finding or add an
   inline disable with a comment explaining the false positive.
2. Run `shfmt -i 2 -ci -sr -w .`.
3. Run the ASCII gate: `LC_ALL=C grep -PlI "[^\x00-\x7F]" .`
   Any output blocks the push.
4. Cite the rule your change enforces in the commit body. Example:
   "Enforce R-901 in _evalcache."

## Adding a rule

- Cite the upstream you derive it from, or mark `estate-original`.
- Include a Correct / Avoid pair.
- Include a Why paragraph that names the failure mode the rule prevents.
- Add the rule to `CHANGELOG.md` under `[Unreleased]`.
