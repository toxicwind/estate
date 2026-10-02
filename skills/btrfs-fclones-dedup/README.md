# btrfs-fclones-dedup

[![for-the-badge](https://img.shields.io/badge/BTRFS-0D7377?style=for-the-badge)](https://btrfs.readthedocs.io) [![for-the-badge](https://img.shields.io/badge/fclones-FF6F61?style=for-the-badge)](https://github.com/cyfde/fclones) [![for-the-badge](https://img.shields.io/badge/znver4-Optimized-FFD700?style=for-the-badge)](https://cachyos.org)

## btrfs-fclones-dedup

BTRFS block-level extent dedup with fclones (znver4) on CachyOS / NVMe. Use when jdupes is too slow or permission errors block full-scans.

### Procedures

1. **Group**: `fclones group -s 4KiB -t 16 <dirs>` → `/tmp/fclones-groups.txt` (fast, ~3-4s for 475k files)
2. **Dedupe**: `fclones dedupe < groups.txt` → clones duplicate data blocks via FIDEDUPERANGE, reclaiming GB without breaking paths/symlinks
3. **Verify**: Always verify with `fclones --version` (znver4 build) and save groups file for audit

### Quick start (3 commands max)

```bash
# Step 1: Group duplicate extents
fclones group -s 4KiB -t 16 /path/to/dirs

# Step 2: Dedupe using the groups file
fclones dedupe /tmp/fclones-groups.txt

# Step 3: Verify the results
fclones --version
```

### Architecture

BTRFS block-level dedup operates at the extent level, not the file level. fclones identifies duplicate blocks and clones them via FIDEDUPERANGE, sharing the same physical extent while maintaining independent logical paths/symlinks. The znver4 optimization targets CachyOS CPUs for fastest group+dedupe cycles. Always save the groups file for auditability — it records which blocks were deemed duplicates.

### Config / optional services

- `-s <size>` — extent size granularity (default 4KiB)
- `-t <threads>` — number of threads for grouping (default 16)
- `--version` — verify znver4 build
- Groups file path (default: `/tmp/fclones-groups.txt`)
- Target directories — required argument

### Dev / contributing

- Test on CachyOS / znver4; results: 3-4s for 475k files
- Always save the groups file before dedupe for audit
- Verify paths/symlinks remain intact after dedupe
- Compare against jdupes for correctness when switching tools
- Contributions should preserve the block-level semantics and FIDEDUPERANGE usage

### License

Open Claw — see `skill.toml` for details.

### Security

- Always verify with `fclones --version` (znver4 build) and save groups file for audit
- Never breaks paths/symlinks during dedupe (FIDEDUPERANGE preserves them)
- Save groups file before dedupe for reproducibility and audit