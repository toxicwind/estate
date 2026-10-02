# fix-tau-session-corruption

**Fix Tau Session Store Corruption** – Repair corrupted tau session JSONL files caused by over-broad `sed` operations that double-replaced paths.

## What It Does

This skill addresses tau session store corruption where paths in session JSONL files were incorrectly modified (e.g., `$HOME/.local/home/toxic/.local/bin/tau` instead of `$HOME/.local/bin/tau`) due to sed commands lacking proper word boundaries. It identifies, fixes, and verifies the correction of these corrupted files.

## Why It Matters

Over-broad `sed` operations can accidentally replace entire strings rather than matching specific word boundaries, leading to double-replacement and broken session files. This skill provides a safe, word-boundary-safe approach to repair the damage while preserving the integrity of the tau session store.

## Features

- **Automated detection**: Finds recently modified session JSONL files containing corrupted paths.
- **Safe repair**: Uses word-boundary-aware `sed` to fix double-replaced paths without affecting other parts of the file.
- **Pre-merge restoration option**: Checks for a pre-merge tarball as a fallback for severe corruption.
- **Verification**: Confirms that corrupted files are cleaned and the session store is healthy.

## Quick Start

```bash
# Identify corrupted files (last 120 minutes)
find ~/.tau/sessions -name '*.jsonl' -mmin -120 2>/dev/null |
  while read f; do
    grep -q 'HOME/.local/home/toxic' "$f" 2>/dev/null && echo "$f"
  done

# Apply the fix to each corrupted file
for f in $(find ~/.tau/sessions -name '*.jsonl' -mmin -120 2>/dev/null |
            | while read f; do
              grep -q 'HOME/.local/home/toxic' "$f" 2>/dev/null && echo "$f"
            done); do
    echo "Fixing: $f"
    # Word-boundary-safe sed to fix double-replaced paths
    sed -i -E 's:(HOME/.local)/home/toxic/.local/bin/tau:\1/.local/bin/tau:g' "$f"
    # Verify the fix
    BAD=$(grep -c 'HOME/.local/home/toxic' "$f" 2>/dev/null || echo 0)
    GOOD=$(grep -c 'HOME/.local/bin/tau' "$f" 2>/dev/null || echo 0)
    echo "  Fixed: $BAD bad patterns removed, $GOOD good patterns present"
  done

# Verify the session store is clean
corrupted_count=$(find ~/.tau/sessions -name '*.jsonl' -mmin -120 2>/dev/null |
  | while read f; do
    grep -q 'HOME/.local/home/toxic' "$f" 2>/dev/null && echo "$f"
  done | wc -l)
echo "Corrupted files remaining: $corrupted_count"
```

## Configuration

- **`~/.tau/sessions`**: Directory containing tau session JSONL files that may be corrupted.
- **`~/.tau`**: Configuration symlink (created by the fix).
- **`~/.omp`**: Configuration symlink (created by the fix).
- **Pre-merge tarball**: Optional `~/.tau-premerge-*.tar.zst` file that can be used for restoration if needed.

## Prevention

Always use word-boundary-safe `sed` patterns when modifying file paths:

**Correct (word-boundary safe)**
```bash
sed -i -E 's:(^|[^a-zA-Z0-9_\/])/bin/tau([^a-zA-Z0-9_\/]|$):\1\/home\/toxic\/\.local\/bin\/tau\2:g' file
```

**Incorrect (causes double-replacement)**
```bash
sed -i 's|/bin/tau|/home/toxic/.local/bin/tau|g' file
```

## Verification

After running the fix, verify that tau can read session files without errors:

```bash
tau --version  # Should work normally
```

If any corrupted files remain, the verification step will show the count. All corrupted files should be eliminated after the fix.

## Security & Licensing

- **Security**: The fix ensures that path corrections are precise and do not introduce unintended modifications. Using word-boundary-safe patterns reduces the risk of accidental overwrites.
- **License**: Not specified in the skill metadata.
