# Fix Nemotron 3 Super Flailing Plan

## Context
The Nemotron 3 Super model is flailing due to missing extensions in the tau-extensions directory. Six specific extensions have been identified to fix issues such as invalid x-api-provider headers, false 429 errors, tool-call hallucinations, ambiguous undeclared parameters, network timeout handling, and cloud model tool calling.

## Approach
1. Create the directory for each of the six extensions under `/home/toxic/estate/ranch/tau-extensions/`.
2. Write the provided TypeScript content to each extension's `index.ts` file.
3. Build the tau project by running `bun run --cwd /home/toxic/estate/ranch/tau build`.

## Critical files & anchors
- `/home/toxic/estate/ranch/tau-extensions/omp-provider-factory-droid/index.ts`: Fixes x-api-provider header for nemotron.
- `/home/toxic/estate/ranch/tau-extensions/omp-antigravity-fix/index.ts`: Fixes false 429 for antigravity models.
- `/home/toxic/estate/ranch/tau-extensions/fix-nemotron3-parser/index.ts`: Fixes tool-call hallucination by forwarding tools to parse_qwen35.
- `/home/toxic/estate/ranch/tau-extensions/fix-nemotron-ambiguous/index.ts`: Rejects ambiguous undeclared parameters in tool calls.
- `/home/toxic/estate/ranch/tau-extensions/opencode-timeout-handler/index.ts`: Handles genuine network timeouts for free-tier models.
- `/home/toxic/estate/ranch/tau-extensions/titan-nemotron-super-fix/index.ts`: Enhances tool calling for cloud-routed nemotron-3-super:cloud.
- The build command: `bun run --cwd /home/toxic/estate/ranch/tau build`

## Verification
After creating the extensions and running the build, verify that:
- The build completes without errors.
- The extensions are present in the tau-extensions directory.
- The Nemotron 3 Super model no longer flails when used (this would require a test run, but we assume the build success and extension presence are proxies).

## Assumptions & contingencies
- We assume that the user has write access to the `/home/toxic/estate/ranch/tau-extensions` directory.
- We assume that the tau project is configured to build with `bun run build` in the ranch/tau directory.
- If the build fails due to missing dependencies, we assume the user will install them (but note we are in plan mode and cannot run commands).
- If an extension directory already exists, we will overwrite the index.ts file (but note we are in plan mode and cannot actually write).