#!/usr/bin/env python3
"""
yote_system_audit.py — Single-batch ground-truth system audit for yote (awrawr-pc).
Bypasses broken 'ps -L' shims by reading /proc directly, audits PSI, thread counts,
R/D states, VmSwap, context-switch leaders, and nft-drop / UDP 36575 / 50005 flood.
"""
import glob
import json
import os
import subprocess
import time
from collections import Counter, defaultdict

def sh(cmd, timeout=2.0):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"ERR: {e}"

def read_file(path):
    try:
        with open(path, "r", errors="replace") as f:
            return f.read().strip()
    except Exception:
        return ""

def audit():
    t0 = time.time()
    out = {}

    # 1. Loadavg & PSI (/proc/pressure/*) & Meminfo
    out["loadavg_t0"] = read_file("/proc/loadavg")
    out["psi"] = {
        "cpu": read_file("/proc/pressure/cpu"),
        "io": read_file("/proc/pressure/io"),
        "memory": read_file("/proc/pressure/memory"),
    }
    out["mem_free_h"] = sh("free -h", timeout=1.0)

    # 2. Exact Thread & Process Audit via /proc (no ps -L needed)
    state_counts = Counter()
    r_by_comm = Counter()
    d_by_comm = []
    threads_by_proc = []
    swap_by_proc = []
    zombies = []
    ctxt_by_proc = []

    for pdir in glob.glob("/proc/[0-9]*"):
        pid_str = os.path.basename(pdir)
        if not pid_str.isdigit():
            continue
        pid = int(pid_str)
        status_txt = read_file(f"{pdir}/status")
        if not status_txt:
            continue
        smap = {}
        for line in status_txt.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                smap[k.strip()] = v.strip()
        name = smap.get("Name", "?")
        ppid = int(smap.get("PPid", "0") or 0)
        pstate = smap.get("State", "?")[:1]
        nthreads = int(smap.get("Threads", "1") or 1)
        vmswap_kb = 0
        if "VmSwap" in smap:
            try:
                vmswap_kb = int(smap["VmSwap"].split()[0])
            except Exception:
                pass
        vol_ctxt = int(smap.get("voluntary_ctxt_switches", "0") or 0)
        nonvol_ctxt = int(smap.get("nonvoluntary_ctxt_switches", "0") or 0)
        cmdline = read_file(f"{pdir}/cmdline").replace("\x00", " ").strip()[:120] or name

        if nthreads >= 20:
            threads_by_proc.append({"pid": pid, "name": name, "threads": nthreads, "cmd": cmdline})
        if vmswap_kb >= 102400:  # >= 100 MB swap
            swap_by_proc.append({"pid": pid, "name": name, "swap_mb": round(vmswap_kb / 1024, 1), "cmd": cmdline})
        if pstate == "Z":
            zombies.append({"pid": pid, "name": name, "ppid": ppid})
        if vol_ctxt + nonvol_ctxt > 500000:
            ctxt_by_proc.append({"pid": pid, "name": name, "total_ctxt": vol_ctxt + nonvol_ctxt, "cmd": cmdline})

        # Scan all threads of this process
        for tstat_path in glob.glob(f"{pdir}/task/[0-9]*/stat"):
            raw = read_file(tstat_path)
            if not raw or ")" not in raw:
                continue
            try:
                tid = int(raw.split("(")[0].strip())
                tcomm = raw.split("(", 1)[1].rsplit(")", 1)[0]
                fields = raw.rsplit(")", 1)[1].split()
                st = fields[0]
                state_counts[st] += 1
                if st == "R":
                    r_by_comm[f"{name}/{tcomm} (pid {pid})"] += 1
                elif st == "D":
                    wchan = read_file(f"{pdir}/task/{tid}/wchan")
                    d_by_comm.append({"pid": pid, "tid": tid, "name": name, "tcomm": tcomm, "wchan": wchan, "cmd": cmdline})
            except Exception:
                pass

    threads_by_proc.sort(key=lambda x: x["threads"], reverse=True)
    swap_by_proc.sort(key=lambda x: x["swap_mb"], reverse=True)
    ctxt_by_proc.sort(key=lambda x: x["total_ctxt"], reverse=True)

    out["thread_state_totals"] = dict(state_counts)
    out["total_threads_counted"] = sum(state_counts.values())
    out["r_threads_by_comm"] = r_by_comm.most_common(20)
    out["d_threads_full"] = d_by_comm[:25]
    out["top_thread_owners"] = threads_by_proc[:15]
    out["top_swap_owners"] = swap_by_proc[:15]
    out["top_ctxt_switch_owners"] = ctxt_by_proc[:15]
    out["zombies"] = zombies

    # 3. Network, IP, ARP, Ports & nftables / dmesg nft-drop audit
    out["ip_br_addr"] = sh("ip -br addr | grep -v '^lo'", timeout=1.0)
    out["arp_neighbors"] = sh("ip neigh", timeout=1.0)
    out["udp_ports_of_interest"] = sh("sudo ss -ulnp 2>/dev/null | grep -E '36575|50005|56700|2021' || ss -ulnp | head -20", timeout=1.5)
    out["nft_ruleset"] = sh("sudo nft -a list ruleset 2>/dev/null", timeout=1.5)
    out["etc_nftables_conf"] = read_file("/etc/nftables.conf")
    out["dmesg_nft_drop_sample"] = sh("sudo dmesg --time-format iso 2>/dev/null | grep 'nft-drop' | tail -25", timeout=1.5)
    out["dmesg_non_nft_tail"] = sh("sudo dmesg --time-format iso 2>/dev/null | grep -v 'nft-drop' | tail -25", timeout=1.5)
    out["btdu_log_stat"] = sh("ls -la /var/tmp/btdu-raw.log 2>/dev/null || echo 'none'", timeout=0.5)
    out["loadavg_t1"] = read_file("/proc/loadavg")
    out["elapsed_ms"] = round((time.time() - t0) * 1000, 1)

    with open("/home/toxic/estate/config/tau/yote_audit_report.json", "w") as f:
        json.dump(out, f, indent=2)
    print("AUDIT_OK elapsed_ms=", out["elapsed_ms"], "total_threads=", out["total_threads_counted"], "states=", dict(state_counts))

if __name__ == "__main__":
    audit()
