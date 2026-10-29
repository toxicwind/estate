#!/bin/bash
set -euo pipefail
cd /home/toxic/pens/ranch/tau/packages/coding-agent
exec /home/toxic/.bun/bin/bun -e 'import { compileCodingAgent } from "./scripts/compile-binary"; import * as path from "node:path"; const packageDir = import.meta.dir; const repoRoot = path.join(packageDir, "..", ".."); await compileCodingAgent({ repoRoot, entrypoint: path.join(packageDir, "src", "cli.ts"), outfile: path.join(packageDir, "dist", "tau"), transformersVersion: "3.0.0" });'
