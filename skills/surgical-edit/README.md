![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/surgical-edit?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/surgical-edit?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/surgical-edit?style=for-the-badge)

# surgical-edit
Assertive surgical file editing: exact-text replacements with pre/post occurrence counts, every check before any write, abort on any mismatch

## What it does
Configuration surgery tool that enforces strict pre-write verification: counts exact-text block occurrences before any modification, performs literal string replacements (no regex/fuzzy matching), uses atomic write-to-then-rename operations, and handles byte-exact transit for remote files.

## Why it matters
Prevents catastrophic configuration errors by ensuring that any edit where a wrong change is worse than no change is verified before execution, eliminating silent corruption and partial writes.

## Who it's for
DevOps engineers, SREs, and developers managing hand-maintained router configs (herd.yaml, model_constraints.yaml) or any configuration where correctness is paramount and incorrect edits could cause system-wide outages.

## Features
- **Pre-Write Verification** - Counts every `old` block's occurrences first; aborts with zero bytes written if any count mismatches expectations
- **Exact Text Matching** - Literal string operations only — no regex, no "close enough" matching
- **Atomic Writes** - Write to temporary file + rename; no half-written configs ever
- **Byte-Exact Transit** - For yote/cell transfers: patches specs (not scripts) via base64 chunks per TOOLS.md "Bridge exec: no large heredocs"
- **Herd-Probe Integration** - Exact-token verification through herd router for model route validation
- **Config-Specific Safety** - Designed for herd.yaml, model_constraints.yaml, and other hand-maintained router configurations
- **Anti-Bulldozer Philosophy** - Explicitly not for bulk refactors or generated code; use `ast-migrate.ts` for AST-scale rewrites

## Quick Start
```bash
# Create JSON patch spec (example for herd.yaml)
cat > patch.json <<'EOF'
{
  "file": "/home/toxic/estate/config/herd.yaml",
  "edits": [
    {
      "old": "  # --- moonshot: Moonshot AI direct (PARKED 2026-09-20) ---",
      "new": "  # --- moonshot: Moonshot AI direct (RESTORED 2026-09-20) ---",
      "expected": 1
    }
  ]
}
EOF

# Verify only (dry run)
surgical-edit --check patch.json

# Apply the patch
surgical-edit patch.json

# Verify a model route actually serves
herd-probe moonshot/kimi-k2.6 "ABSTRACT-7X3Q"
# Returns: VERBATIM_EXACT / NONEXACT / HTTP <status> + error body
```

## Configuration
- **Main Tool**: `bin/surgical-edit` - Takes JSON patch spec with `file` and `edits` array
- **Edit Structure**: Each edit requires `"old"`, `"new"`, and `"expected"` (occurrence count) fields
- **Herd Probe**: `bin/herd-probe` - Exact-token probe through herd router: `herd-probe <model>/<version> "<token>"`
- **Bridge Transfer**: For yote/cell transfers, see `~/TOOLS.md` ("Bridge exec: no large heredocs")
- **Deep Links**:
  - Master README: `/home/toxic/estate/README.md`
  - Herd config docs: `/home/toxic/estate/config/` (herd.yaml, model_constraints.yaml)
  - Provenance: `projects/audits/moonshot-parked-audit-2026-09-20.md` §8

## Development
Modify the binaries in `/home/toxic/estate/skills/surgical-edit/bin/`:
- `surgical-edit` - Main editor tool
- `herd-probe` - Exact-token verification through herd router

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Zero Bytes on Mismatch** - Abort writes completely if pre-checks fail
- **No Silent Corruption** - Fail-fast on expectation mismatches instead of partial applies
- **Atomic Operations** - Temp-file + rename prevents half-written states
- **Transfer Safety** - Base64-chunked spec transfer avoids large heredoc issues on bridges
- **Verification Required** - Herd-probe provides verbatim response checking for model routes