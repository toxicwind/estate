# Output Contract

Use these sections in order.

## 1) Repository Status

Include:
- Date/time snapshot
- Current branch and working tree state
- Build/lint/test status
- Architecture summary
- Active risks

## 2) Prioritized Enhancements

Use a table with columns:
- ID
- Enhancement
- Impact (`high|medium|low`)
- Effort (`high|medium|low`)
- Risk if ignored
- Recommended (`yes|no`)

## 3) Designer Input (when UI/UX scope exists)

Include:
- Designer findings summary
- Top design recommendation IDs (`DES-<n>`)
- Mapping from design IDs to enhancement IDs
## 4) Selection Request

Ask the user to choose enhancement IDs to convert into tasks.

## 5) Task Plan (only after selection)

Use a table with columns:
- Task ID
- Enhancement ID
- Designer Source IDs (optional)
- Description
- Assignee
- Feature Branch
- Status
- Acceptance Criteria
- Validation

## 6) Review Feedback (for completed tasks)

Use this shape:
- Task ID
- Review Outcome (`pass|changes_required`)
- Functional Test Outcome (`pass|fail`)
- Acceptance Criteria Coverage (`complete|partial|missing`)
- Findings
- Required Fixes
- Next Step
