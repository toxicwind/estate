{
  "exploration_summary": {
    "repository_structure": "Monorepo with packages/, projects/, src/, skills/, tools/, and various configuration files. Notable directories: packages/coding-agent (main CLI), src/ (services like yote, openfang), projects/ (various subprojects).",
    "documentation": "README.md provides comprehensive overview of omp as a coding agent with IDE wired in. CONTRIBUTING.md outlines contribution process (PRs open to everyone on trial basis). DEVELOPMENT.md in coding-agent package details local development workflow.",
    "source_directories": [
      "packages/coding-agent/src",
      "src/services",
      "src/clients",
      "src/maximal-sovereign-agentic-audit",
      "packages/metaharness/src",
      "packages/typescript-edit-benchmark/src"
    ],
    "todo_fixme_findings": [
      "Found TODO/FIXME comments primarily in skill definitions and external dependencies. Minimal actual TODO/FIXME in core source code. One TODO in src/services/yote.ts regarding proxy pure LLM path for debugging.",
      "Files with TODO/FIXME: src/services/yote.ts (1), src/clients/nim-client/src/client.ts (1), src/kataware-doki/cdp-node.ts (1), packages/metaharness/src/server.ts (1)"
    ],
    "test_suite": {
      "status": "Present but some tests failing",
      "details": "Test suite exists for coding-agent package (bun test). Ran tests showed 2 failing tests in advisor-toggle.test.ts related to cost calculations and 1 failing test in acp-initialize-conformance.test.ts related to version mismatch. Build system verification: build succeeded via bun run build in coding-agent package.",
      "frameworks": [
        "Bun test runner",
        "TypeScript"
      ]
    },
    "build_system": {
      "status": "Functional",
      "details": "Build script: bun run build in packages/coding-agent. Successfully built Tailwind CSS, React app, generated client bundle, tool views, and embedded native dependencies. No errors encountered."
    },
    "configuration_dependencies": {
      "package_json_dependencies": [
        "sherpa-onnx",
        "sherpa-onnx-darwin-arm64",
        "sherpa-onnx-node"
      ],
      "dev_dependencies": [
        "@types/bun",
        "@typescript/native-preview",
        "lint-staged",
        "oxfmt",
        "oxlint",
        "prettier",
        "ts-morph",
        "typescript",
        "bun-types",
        "turbo"
      ],
      "cargo_workspace": [
        "crates/pi-ast",
        "crates/pi-builtins",
        "crates/pi-diff",
        "crates/pi-edit",
        "crates/pi-iso",
        "crates/pi-natives",
        "crates/pi-shell",
        "crates/pi-vcs",
        "crates/pi-voice",
        "crates/pi-walker",
        "crates/vendor/brush-core",
        "crates/vendor/cfg_aliases"
      ],
      "lockfiles": [
        "Cargo.lock",
        "bun.lock",
        "package-lock.json in various skill directories"
      ]
    },
    "immediate_tasks_contribution": {
      "contribution_guidelines": "PRs open to everyone on trial basis (previously required vouch). Must include human-written explanation in PR body, verify changes work as intended, keep PRs to one logical change. AI agents welcome as tools but must be constrained to agreed scope.",
      "development_process": "Local development: bun run check for typecheck, bun run gen:tool-views after changing React tool renderers. See DEVELOPMENT.md for detailed subsystem references.",
      "identified_todos": [
        "Version mismatch in test/acp-initialize-conformance.test.ts (expected tau/main-18.3.0-sovereign-tau-d83c686 vs received 18.3.0)",
        "Advisor cost calculation issues in test/advisor-toggle.test.ts"
      ]
    }
  }
}