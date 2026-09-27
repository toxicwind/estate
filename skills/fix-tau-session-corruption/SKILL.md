---
name: fix-tau-session-corruption
description: Fix tau session store corruption caused by over-broad sed operations that double-replace paths
---

# Fix Tau Session Store Corruption

## When to Use This Skill
When tau session JSONL files contain corrupted paths like `$HOME/.local/home/toxic/.local/bin/tau` instead of `$HOME/.local/bin/tau` due to over-broad sed operations that didn't use word boundaries.

## Procedure

1. **Identify corrupted files**
   ```bash
   find ~/.tau/sessions -name '*.jsonl' -mmin -120 2>/dev/null \
     | while read f; do
         grep -q 'HOME/.local/home/toxic' "$f" 2>/dev/null && echo "$f"
       done
   ```

2. **Check for pre-merge tarball (optional restoration)**
   ```bash
   TARBALL=$(ls -t ~/.tau-premerge-*.tar.zst 2>/dev/null | head -1)
   if [ -n "$TARBALL" ]; then
     # Attempt tarball restoration first if it contains the needed files
     # (Note: tarball must be newer than the corruption)
   fi
   ```

3. **Fix corrupted files with word-boundary-safe sed**
   ```bash
   for f in $(find ~/.tau/sessions -name '*.jsonl' -mmin -120 2>/dev/null \
               | while read f; do
                     grep -q 'HOME/.local/home/toxic' "$f" 2>/dev/null && echo "$f"
                   done); do
     
     echo "Fixing: $f"
     
     # Fix the double-replaced path using word boundaries to prevent re-corruption
     sed -i -E 's:(HOME/\.local)/home/toxic/\.local/bin/tau:\1/.local/bin/tau:g' "$f"
     
     # Verify fix
     BAD=$(grep -c 'HOME/.local/home/toxic' "$f" 2>/dev/null || echo 0)
     GOOD=$(grep -c 'HOME/.local/bin/tau' "$f" 2>/dev/null || echo 0)
     echo "  Fixed: $BAD bad patterns removed, $GOOD good patterns present"
   done
   ```

4. **Verify session store is clean**
   ```bash
   corrupted_count=$(find ~/.tau/sessions -name '*.jsonl' -mmin -120 2>/dev/null \
     | while read f; do
         grep -q 'HOME/.local/home/toxic' "$f" 2>/dev/null && echo "$f"
       done | wc -l)
   echo "Corrupted files remaining: $corrupted_count"
   ```

## Prevention
Always use word-boundary-safe sed when replacing paths:
```bash
# CORRECT (word-boundary safe)
sed -i -E 's:(^|[^a-zA-Z0-9_\/])/bin/tau([^a-zA-Z0-9_\/]|$):\1\/home\/toxic\/.local\/bin\/tau\2:g' file

# INCORRECT (causes double-replacement)
sed -i 's|/bin/tau|/home/toxic/.local/bin/tau|g' file
```

## Verification
After fixing, tau should be able to read session files without errors:
```bash
tau --version  # Should work normally
```
