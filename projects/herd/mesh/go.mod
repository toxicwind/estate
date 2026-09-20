module github.com/mostlygeek/herd-mesh

go 1.26.1

// Quarantine boundary (2026-09-20, herd audit): mesh/ is mid-migration code
// merged 2026-09-17 with foreign import paths
// (github.com/smart-mcp-proxy/mcpproxy-go/...) whose internal packages are
// not vendored in-tree, so it cannot build as part of the herd module.
// This nested module boundary keeps the parent  green;
// nothing in the herd daemon binary depends on mesh/ (verified via
// ). Reversible: delete this file to re-merge.
