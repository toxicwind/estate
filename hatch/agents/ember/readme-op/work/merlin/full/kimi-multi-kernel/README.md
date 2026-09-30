# KIMI Multi-Kernel Mesh 🖥️

![forensics](https://img.shields.io/badge/type-forensic_lab_notebook-6b21a8)
![auto-hook](https://img.shields.io/badge/ingest-auto--hook_daemon-f59e0b)
![status](https://img.shields.io/badge/status-append--only_dump-inactive)

A forensic lab notebook from the Kimi sandbox lane: **multi-python kernel
mesh + headscale + CVE-2026 research** artifacts, committed by an auto-hook
daemon. Treat this repo as an append-only evidence locker, not a library —
there is no public API and no supported install path.

> ## What this repo actually is
>
> An auto-hook system (`auto_hook.py`, `autohook_v7.py`) watched
> `/mnt/agents/output` on a sandbox host and pushed tool outputs,
> environment snapshots, and service dumps here as they landed. Commits are
> machine-generated (`auto: …`, `hook: …`). Files are evidence, curated
> only by capture time.

## What's in the locker

| Area | Files | What it is |
|---|---|---|
| **Auto-hook daemons** | `auto_hook.py`, `autohook_v7.py`, `auto_loader.py` | Persistent sandbox monitors — capture tool outputs, chunked payloads (`.moonbox_chunks`), push snapshots to this repo via the GitHub API |
| **Kernel mesh** | `activate_all_v1.py`, `deploy_shim_v1.py`, `envd_shim_v4.py`, `drive9_client_v1.py` | Multi-python kernel bring-up, shims, and client wiring |
| **s6 supervision** | `s6_status_*`, `s6_env_*`, `s6_run_*`, `s6_services*.json` | Supervised service snapshots: `kernel-server`, `kasmvnc`, `browser-guard`, `sshd`, `socat`, `s6rc-fdholder`, `oneshot-runner` |
| **Env snapshots** | `env_*.json`, `env_*.sh`, `state.json` | Frozen environment captures (dev, kimi, s6, net, vnc, cdp) |
| **Browser/Chrome forensics** | `chrome_cookies.txt`, `chrome_history.txt`, `chrome_logins.txt`, `chrome_data_files.txt`, `cdp_snapshot.json`, `cdp_targets.json`, `strings_*.txt` | Chrome profile dumps and CDP target snapshots |
| **Capabilities** | `capabilities.txt` | Capability/setuid audit of the sandbox (`uid=999(kimi)`, bounding-set dump) |
| **SynthID research** | `synthid_analysis/` | SynthID watermarking research — Master Index, Mathematical Autopsy, Regulatory Capture, Surveillance Architecture, Technical Obfuscations |
| **Transaction research** | `transaction_analysis.md`, `transaction_analysis_full.png` | CVE-2026-adjacent transaction forensics artifacts |

## Auto-hook mechanics (for the curious)

`autohook_v7.py` runs a threaded capture loop: tool outputs land in
`/mnt/agents/output`, get logged to `.bg_logs/ah7.log` (plus a JSONL tool
stream), chunked under `.moonbox_chunks`, and state-tracked in
`.bg_state/ah7_state.json`. `auto_hook.py` additionally pushes artifacts
straight to `toxicwind/kimi-multi-kernel` via the GitHub Contents API.

## Provenance

- Machine-generated commits; human-authored files are the exception.
- Snapshot dates are in file contents, not this README — check the file
  before quoting a finding.
- Some dumps contain environment-specific paths and identifiers from the
  sandbox; treat as internal.

---

Part of the Kimi infrastructure-research lane. See also
[toxicwind/infra-recon](https://github.com/toxicwind/infra-recon) for the
companion reconnaissance toolkit.
