# Refusal-classifier hunt — evidence log

Perpetual task (Chris, 2026-09-15): track down the "sorry classifier" behind the
canned refusals and the bugged "completed" spawn status. MITM/unshare/pcap.

## 2026-09-15 22:00 MDT — first capture: classifier is REMOTE, not local

**Hypothesis:** a hidden local interceptor in the cell substitutes refusals.

**Result: DISPROVEN for the cell.** The refusal is generated serving-side.

### unshare audit (cell, as root)
- `lsns`: only the container's own net/mnt/pid/uts/ipc/user/cgroup namespaces,
  plus normal per-hook private mount namespaces (squawk-push, poller, exec hooks).
  No hidden network namespaces.
- `ps`: only expected processes — systemd, hatch daemon, hatch-execd,
  squawk hooks, service-health-poller. No interceptor, no proxy process.
- `iptables`: all chains ACCEPT, no REDIRECT/DNAT rules.
- Egress path is clean: cell -> host0 -> hatch-egress-proxy:3128 -> backend.

### pcap experiment (spawn-refusal-20260915.pcap)
- Static tcpdump 4.99.6 (jpiersol/StaLiBs v3, staticaly linked) captured host0
  during a trivial `subagent.spawn` ("reply pong").
- The spawn was refused (~1s, canned refusal as final_response, status completed).
- During the refusal window (t+5-6s) TWO fresh TCP connections were opened
  through the egress proxy carrying ~2.6KB up / ~3.5KB down.
- Verdict: the refusal involved a full REMOTE round trip. Nothing local
  generated it — radio silence would have proven local generation, and we got
  the opposite.

### What this means
- There is no local "sorry classifier" in the cell to find or fix. unshare
  cannot reach it because it lives in Hatch serving infrastructure.
- The bugged "completed" status is also platform-side (runtime writes the
  ledger). Local workaround: AGENTS.md rule — never trust spawn status,
  always inspect final_response for the refusal signature.
- "Fixing" the classifier itself is not possible from here; the perpetual
  task is detection + evidence + escalation material.

## Perpetual watch protocol
1. Canary spawn probes (trivial task) whenever active; log refused vs ran.
2. Fleet-ledger audit via muse.db: count refused-completed rows per 24h.
3. On refusal storms: capture host0 with /home/toxic/refusal-hunt/tcpdump-static
   (re-download: https://github.com/jpiersol/StaLiBs/releases/download/v3/stalibs-linux-x86_64.zip).
4. Evidence lands here, newest capture + notes appended.

## Files
- spawn-refusal-20260915.pcap — refused spawn, remote round trip proven

## 2026-09-15 22:02 MDT — deeper: eBPF out, ledger signature in

**eBPF: BLOCKED.** bpf() syscall returns EPERM from the cell
(unprivileged_bpf_disabled=2, no tracefs, no bpftool/bpftrace/bcc).
No eBPF tracing possible here; pcap + ledger remain the instruments.

**Refusal signature extracted (no string quoting needed):** all 30 refused
spawns in 24h share byte-identical final_response md5
b4aefd29108f232f9c0d5a4b030215c1 (384 chars, status completed, 0-4s).
5 genuine spawns have unique bodies and 60s+ runtimes. The md5 is now the
mechanical refused-vs-ran detector — see pong-canary.md (the constant retest).
