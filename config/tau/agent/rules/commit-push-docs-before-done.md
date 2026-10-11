---
name: commit-push-docs-before-done
description: "Always update documentation and commit and push before declaring work complete"
condition: "(?i)\\b(verification complete|task (is )?complete|all (services|tasks|fixes) (have been )?(verified|complete)|finished all)\\b"
question: "Does the response declare completion or wrap up the work without having committed, pushed, and updated relevant READMEs or documentation?"
scope: "text"
---

Do not declare completion or yield without updating relevant documentation (READMEs/changelogs) and ensuring all changes are staged, committed, and pushed. Complete the full delivery cycle before wrapping up.