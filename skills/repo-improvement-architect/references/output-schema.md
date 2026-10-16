# Output schema, Repo Improvement Architect

The skill returns this object first, then a short prose summary. It is validated
by `validateRepoPlan` in `@premium-agent-skills/core`.

```json
{
  "summary": "string, one or two sentences naming the top improvement",
  "evidence": [
    {
      "path": "string, repo-relative file path the finding is grounded in",
      "finding": "string, the concrete observation at that path",
      "confidence": "high | medium | low"
    }
  ],
  "recommended_next_change": {
    "scope": "string, the single bounded change to make next",
    "files": ["string, files the change touches"],
    "risk": "low | medium | high"
  },
  "verification": {
    "commands": ["string, exact shell commands that prove the change"],
    "manual_checks": ["string, human checks that cannot be automated"]
  },
  "optional_followups": ["string, deferred, lower-priority items"]
}
```

## Field rules

- **summary**, required, non-empty. Lead with the outcome, not the mechanism.
- **evidence**, every entry must cite a real `path`. No path, no finding.
  `confidence` reflects how directly the evidence supports the claim.
- **recommended_next_change**, exactly one change. If the work needs several,
  pick the first and list the rest under `optional_followups`.
- **risk**, `low` = isolated, reversible; `medium` = touches shared code;
  `high` = behavior or interface change. Anything `high` should usually be split.
- **verification.commands**, exact and runnable. Empty array is allowed only
  when paired with a `manual_checks` entry explaining why.
- **optional_followups**, defaults to `[]`. Never smuggle a second "next
  change" in here; these are explicitly deferred.

## Worked example

```json
{
  "summary": "Normalize the CI install/test sequence to remove flaky failures.",
  "evidence": [
    {
      "path": ".github/workflows/test.yml",
      "finding": "Job 'unit' runs `npm install` while job 'e2e' runs `npm ci`, producing divergent trees.",
      "confidence": "high"
    }
  ],
  "recommended_next_change": {
    "scope": "Use `npm ci` in every job and cache ~/.npm by lockfile hash",
    "files": [".github/workflows/test.yml"],
    "risk": "low"
  },
  "verification": {
    "commands": ["npm ci", "npm test"],
    "manual_checks": ["Re-run the workflow twice; both runs go green"]
  },
  "optional_followups": [
    "Pin third-party actions to full commit SHAs"
  ]
}
```
