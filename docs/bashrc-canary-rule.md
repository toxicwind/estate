# ~/.bashrc canary rule — FP-CANARY-REWRITE-PROOF

**Rule (User, 2026-10-28):** any new config/export in `~/.bashrc` MUST be
inserted **before** the S13 canary block, never after. The canary
(`# FP-CANARY-REWRITE-PROOF-20260929`) is only a valid rewrite detector while
it is the **physical last line** of the file — a sentinel that isn't the
terminal line is worthless.

## Why it keeps regressing

Installers and sessions append to the end of `.bashrc`:

- 2026-10-28: `RIPGREP_CONFIG_PATH` export appended after the canary — fixed by
  moving it into the section above and renumbering.
- 2026-10-30: `export KAPPA_ALLOW_HOME_INDEXING=1` (kappa installer) found
  appended after the canary — moved into S0 (universal env tier) with a
  comment; canary restored as the physical last line.

After ANY kappa install/update or any session edit to `~/.bashrc`: verify the
last line is `# if this line is gone, an autonomous process rewrote $HOME/.bashrc`.
