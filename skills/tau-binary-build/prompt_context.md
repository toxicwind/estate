To build and deploy the tau binary:
1. Navigate to `packages/coding-agent`.
2. Run the compilation script or inline compilation via Bun:
   ```bash
   bun -e 'import { compileCodingAgent } from "./scripts/compile-binary"; import * as path from "node:path"; const packageDir = import.meta.dir; const repoRoot = path.join(packageDir, "..", ".."); await compileCodingAgent({ repoRoot, entrypoint: path.join(packageDir, "src", "cli.ts"), outfile: path.join(packageDir, "dist", "tau"), transformersVersion: "3.0.0" });'
   ```
3. Update the launcher script to point to `dist/tau` correctly using `exec "$scripts_dir/../dist/tau" "$@"`.