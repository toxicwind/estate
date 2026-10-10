---
name: tau-extension-location
description: Remember where tau extensions like tau-flocksync actually live vs where their configs are stored
---

When looking for tau extension code, check ~/.tau/extensions/ for the actual implementation (extension.ts, provider.ts, etc.), while extension configuration lives in ~/.tau/agent/extensions/<extension-name>/settings.json. This split location is non-standard but consistent across tau extensions like tau-flocksync.
