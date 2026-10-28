---
description: Estate env doctor — layer conflict audit
---
Run `bun run /home/toxic/estate/ranch/estate-shell/src/doctor.ts` and report conflicts between /etc/environment, /etc/environment.d, ~/.config/environment.d, and the estate env SSOT. Fix by regenerating environment.d via `bun run /home/toxic/estate/ranch/estate-shell/src/env.ts` when the estate layer is the source of truth.
