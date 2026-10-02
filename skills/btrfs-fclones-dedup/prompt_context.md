BTRFS block-level extent dedup with fclones (znver4) on CachyOS / NVMe:
1. `fclones group -s 4KiB -t 16 <dirs>` → ${TMPDIR:-$HOME/.cache}/fclones-groups.txt (fast, ~3-4s for 475k files)
2. `fclones dedupe < groups.txt` → clones duplicate data blocks via FIDEDUPERANGE, reclaiming GB without breaking paths/symlinks
3. Always verify with `fclones --version` (znver4 build) and save groups file for audit
Use when jdupes is too slow or permission errors block full-scans.