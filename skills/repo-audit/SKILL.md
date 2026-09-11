# Repo Audit Skill

Analyze repository visibility and identify anomalies.

## Usage

Run this skill to audit all repositories under a GitHub user/org and identify which should be public vs private based on naming conventions.

## Steps

1. Fetch all repositories
2. Analyze visibility
3. Flag anomalies (e.g., repos with "private" in name that are public, or lacking CI that should be public)
4. Output recommendations

## Implementation

This skill uses Python with pandas for data analysis.

## Example

```bash
# Run the skill audit
python repo_audit.py --user toxicwind
```