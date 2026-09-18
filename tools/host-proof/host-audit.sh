#!/usr/bin/env bash
# ============================================================================
# awrawr-pc host-bridge audit -- READ-ONLY debug audit
# Generalized as host-proof/host-audit.sh: universal, identifies whatever box
# it runs on. The entity-hunt target defaults to the box's own hostname and
# can be overridden:  TARGET=mybox ./host-audit.sh   or   ./host-audit.sh mybox
# ----------------------------------------------------------------------------
# Contract: strictly read-only. No mutations, no restarts, no writes to disk.
# Output goes to stdout only. Every check degrades gracefully: if a command
# is missing or a data source is unreadable, the script prints
# CHECK-UNAVAILABLE with the reason and moves on. Exit status is always 0;
# this is an audit, not a test.
#
# Run:  bash awrawr-pc-host-bridge-audit.sh
#       (or paste the whole file into a shell on the host)
#
# The script discovers the environment at runtime. It names no service
# manager, container runtime, hypervisor, or network stack up front; each
# subsystem is probed for presence before it is queried.
# ============================================================================
set -u
set -o pipefail  # pipeline failures must reach the || CHECK-UNAVAILABLE branches

say()     { printf '\n===== %s =====\n' "$1"; }
have()    { command -v "$1" >/dev/null 2>&1; }
unavail() { printf 'CHECK-UNAVAILABLE: %s -- %s\n' "$1" "$2"; }
oklabel() { printf '[ok] %s\n' "$1"; }

# Entity-hunt target: the box's own identity by default. Never hardcoded.
# Override:  TARGET=mybox ./host-audit.sh   or   ./host-audit.sh mybox
TARGET="${1:-${TARGET:-$(hostname 2>/dev/null || echo host)}}"
[ -n "$TARGET" ] || TARGET="host"
# pgrep self-exclusion: bracket the first character so pgrep doesn't match itself
PGREP_PAT="[${TARGET:0:1}]${TARGET:1}"
printf '\n===== TARGET =====\nentity-hunt target: %s\n' "$TARGET"

# ---------------------------------------------------------------- A. HOST IDENTITY
# Proves: what this machine claims to be (kernel, distro, hostname), how long
# it has been up, what PID 1 is (reveals the init/service-manager family
# without assuming one), and whether it is bare metal, a VM, or a container
# (determines which bridge technologies are even possible here).
say "A. HOST IDENTITY"
uname -a 2>/dev/null || unavail "uname" "command not found"
if [ -r /etc/os-release ]; then
    # head only: os-release is structural, no secrets
    head -6 /etc/os-release
else
    unavail "/etc/os-release" "not readable"
fi
hostname 2>/dev/null || unavail "hostname" "command not found"
uptime 2>/dev/null || unavail "uptime" "command not found"
if [ -r /proc/1/comm ]; then printf 'pid1: '; cat /proc/1/comm; else unavail "/proc/1/comm" "not readable"; fi
if have systemd-detect-virt; then
    printf 'virt: '; systemd-detect-virt 2>/dev/null || echo "detection-failed"
elif [ -r /sys/class/dmi/id/product_name ]; then
    printf 'dmi-product: '; cat /sys/class/dmi/id/product_name
elif [ -f /.dockerenv ]; then
    echo "virt: container (/.dockerenv present)"
else
    unavail "virtualization detection" "no detector available"
fi

# ------------------------------------------------- B. ENTITY HUNT
# Proves: which concrete form the target endpoint takes on THIS host --
# a process, a managed service, a container, a VM, a mount, a socket, or
# nothing visible from here. Each form is probed independently so an absent
# subsystem yields CHECK-UNAVAILABLE instead of a false negative.
say "B. ENTITY HUNT for '$TARGET' (process / service / container / VM / mount / socket)"
# B1: processes -- read-only scan of /proc, no signals sent
if have pgrep; then
    pgrep -af "$PGREP_PAT" 2>/dev/null | head -20 || true
    [ "$(pgrep -af "$PGREP_PAT" 2>/dev/null | wc -l)" -eq 0 ] && echo "[ok] no '$TARGET' process matched"
else
    # fallback: pure /proc read, still read-only
    found=0
    for d in /proc/[0-9]*; do
        if tr '\0' ' ' < "$d/cmdline" 2>/dev/null | grep -qiE "$TARGET"; then
            printf 'pid %s: ' "${d#/proc/}"; tr '\0' ' ' < "$d/cmdline" 2>/dev/null | head -c 200; echo; found=1
        fi
    done
    [ "$found" -eq 0 ] && echo "[ok] no '$TARGET' process matched (/proc scan)"
fi
# B2: service managers -- only ones actually present are queried
if have systemctl; then
    systemctl list-units --all --no-pager 2>/dev/null | grep -i "$TARGET" | head -10 || echo "[ok] no '$TARGET' systemd unit matched"
else
    unavail "systemd unit query" "systemctl not present"
fi
if have pitchfork; then
    pitchfork list 2>/dev/null | grep -i "$TARGET" | head -10 || echo "[ok] no '$TARGET' pitchfork entry matched"
else
    unavail "pitchfork query" "pitchfork not present"
fi
# B3: containers / VMs -- each runtime probed only if its CLI exists
if have docker; then
    docker ps --format '{{.Names}} {{.Image}} {{.Status}}' 2>/dev/null | grep -i "$TARGET" | head -10 || echo "[ok] no '$TARGET' docker container matched"
else
    unavail "docker query" "docker not present"
fi
if have podman; then
    podman ps --format '{{.Names}} {{.Image}} {{.Status}}' 2>/dev/null | grep -i "$TARGET" | head -10 || echo "[ok] no '$TARGET' podman container matched"
else
    unavail "podman query" "podman not present"
fi
if have virsh; then
    virsh list --all 2>/dev/null | grep -i "$TARGET" | head -10 || echo "[ok] no '$TARGET' libvirt domain matched"
else
    unavail "libvirt query" "virsh not present"
fi
# B4: mounts -- read-only read of /proc/mounts
if [ -r /proc/mounts ]; then
    grep -i "$TARGET" /proc/mounts | head -10 || echo "[ok] no '$TARGET' mount matched"
else
    unavail "/proc/mounts" "not readable"
fi
# B5: sockets -- listening endpoints only, no connections made
if have ss; then
    ss -tulnp 2>/dev/null | grep -iE "$TARGET" | head -10 || echo "[ok] no '$TARGET' socket matched (ss)"
elif have netstat; then
    netstat -tulnp 2>/dev/null | grep -iE "$TARGET" | head -10 || echo "[ok] no '$TARGET' socket matched (netstat)"
else
    unavail "socket listing" "neither ss nor netstat present"
fi

# ---------------------------------------------------------- C. BRIDGE DISCOVERY
# Proves: which bridge technology actually exists on this host. Linux bridge,
# Open vSwitch, libvirt networks, and Docker networks are each probed for
# presence; only present ones are reported as candidates. Absent ones are
# CHECK-UNAVAILABLE, never assumed.
say "C. BRIDGE DISCOVERY"
BRIDGES_FOUND=0
# C1: Linux bridge via iproute2 or sysfs (both read-only)
if have ip; then
    ip -o link show type bridge 2>/dev/null | head -10 || true
    [ "$(ip -o link show type bridge 2>/dev/null | wc -l)" -gt 0 ] && BRIDGES_FOUND=1
elif [ -d /sys/class/net ]; then
    for n in /sys/class/net/*; do [ -d "$n/bridge" ] && { echo "bridge: ${n##*/} (via sysfs)"; BRIDGES_FOUND=1; }; done
else
    unavail "linux bridge probe" "neither ip nor /sys/class/net available"
fi
if have brctl; then
    brctl show 2>/dev/null | head -20 || unavail "brctl show" "command failed"
else
    unavail "brctl" "not present (ip/sysfs probe above is authoritative)"
fi
# C2: Open vSwitch
if have ovs-vsctl; then
    ovs-vsctl show 2>/dev/null | head -40 || unavail "ovs-vsctl show" "command failed"
    BRIDGES_FOUND=1
else
    unavail "openvswitch probe" "ovs-vsctl not present"
fi
# C3: libvirt networks
if have virsh; then
    virsh net-list --all 2>/dev/null | head -15 || unavail "virsh net-list" "command failed"
else
    unavail "libvirt network probe" "virsh not present"
fi
# C4: Docker networks
if have docker; then
    docker network ls 2>/dev/null | head -15 || unavail "docker network ls" "command failed (daemon may be down; still read-only)"
else
    unavail "docker network probe" "docker not present"
fi
[ "$BRIDGES_FOUND" -eq 0 ] && echo "[note] no linux-bridge/OVS device positively identified above; see per-subsystem results"

# ------------------------------------------- D. BRIDGE MEMBERSHIP AND L2 STATE
# Proves: exactly which interfaces are enslaved to each discovered bridge,
# their link state, STP state, and forwarding-database entries -- i.e. who is
# actually ON the bridge right now. All sources are read-only (ip, sysfs,
# bridge fdb show).
say "D. BRIDGE MEMBERSHIP AND L2 STATE"
if [ -d /sys/class/net ]; then
    for n in /sys/class/net/*; do
        [ -d "$n/bridge" ] || continue
        br="${n##*/}"
        printf -- '--- bridge %s ---\n' "$br"
        printf 'member ports (sysfs brif): '
        ls "$n/brif" 2>/dev/null | tr '\n' ' ' || echo -n "(unreadable)"
        echo
        [ -r "$n/bridge/stp_state" ] && printf 'stp_state: %s\n' "$(cat "$n/bridge/stp_state")"
        [ -r "$n/operstate" ] && printf 'operstate: %s\n' "$(cat "$n/operstate")"
        if have bridge; then
            bridge fdb show br "$br" 2>/dev/null | head -15 || unavail "bridge fdb show $br" "command failed"
        else
            unavail "forwarding database" "bridge(8) not present"
        fi
        if have ip; then
            for p in "$n"/brif/*; do
                [ -e "$p" ] || continue
                ip -o link show dev "${p##*/}" 2>/dev/null | head -2
            done
        fi
    done
else
    unavail "bridge membership" "/sys/class/net not available"
fi
if have ovs-vsctl; then
    say "D2. OVS PORT DETAIL"
    for b in $(ovs-vsctl list-br 2>/dev/null); do
        printf -- '--- ovs bridge %s ---\n' "$b"
        ovs-vsctl list-ports "$b" 2>/dev/null | head -20 || unavail "ovs-vsctl list-ports $b" "command failed"
    done
fi

# ----------------------------------------------------------------- E. ROUTES
# Proves: the host's L3 path selection -- which routes leave via bridge
# member interfaces vs the physical uplink. A bridge with no route pointing
# at it is L2-only by configuration.
say "E. ROUTES"
if have ip; then
    ip route show 2>/dev/null | head -25 || unavail "ip route show" "command failed"
    echo "--- ipv6 ---"
    ip -6 route show 2>/dev/null | head -15 || unavail "ip -6 route show" "command failed"
else
    unavail "routing table" "ip not present"
fi

# --------------------------------------------------------------- F. FIREWALL
# Proves: the packet policy that could permit or drop bridged traffic, and
# whether the host forwards at L3 at all (ip_forward). Rules are only
# LISTED, never changed. Listing may need privilege; denial is reported, not
# worked around.
say "F. FIREWALL RULES AND FORWARDING"
if have iptables; then
    iptables -L -n -v --line-numbers 2>/dev/null | head -40 || unavail "iptables -L" "command failed (likely needs privilege)"
else
    unavail "iptables" "not present"
fi
if have nft; then
    nft list ruleset 2>/dev/null | head -40 || unavail "nft list ruleset" "command failed (likely needs privilege)"
else
    unavail "nft" "not present"
fi
if [ -r /proc/sys/net/ipv4/ip_forward ]; then
    printf 'ipv4 ip_forward: %s\n' "$(cat /proc/sys/net/ipv4/ip_forward)"
else
    unavail "ip_forward" "/proc/sys/net/ipv4/ip_forward not readable"
fi

# ------------------------------------------------------- G. ACTIVE CONNECTIONS
# Proves: live L4 flows on the host at audit time -- what is actually
# talking, over which local interface. Snapshot only; nothing is traced or
# intercepted.
say "G. ACTIVE CONNECTIONS (established, snapshot)"
if have ss; then
    ss -tun state established 2>/dev/null | head -30 || unavail "ss" "command failed"
elif have netstat; then
    netstat -tun 2>/dev/null | head -30 || unavail "netstat" "command failed"
else
    unavail "connection listing" "neither ss nor netstat present"
fi

# --------------------------------------------- H. LOGS AND ENVIRONMENT (SANITIZED)
# Proves: recent kernel link/bridge events (up/down, STP, new ports) without
# dumping whole logs. Environment is reported as VARIABLE NAMES ONLY --
# values are never printed, so secrets cannot leak through stdout.
say "H. LOGS (bridge/link events, recent)"
if have dmesg; then
    dmesg 2>/dev/null | grep -iE 'bridge|br[0-9]|virbr|docker0|link (up|down)|stp' | tail -20 || echo "[ok] no bridge/link events in dmesg"
else
    unavail "dmesg" "not present"
fi
if have journalctl; then
    journalctl -k -n 40 --no-pager 2>/dev/null | grep -iE 'bridge|br[0-9]|virbr|docker0|link (up|down)|stp' | tail -20 \
        || echo "[ok] no bridge/link events in kernel journal (or journal unreadable)"
else
    unavail "journalctl" "not present"
fi
say "H2. ENVIRONMENT (names only -- values never printed)"
if [ -r /proc/1/environ ]; then
    tr '\0' '\n' < /proc/1/environ 2>/dev/null | cut -d= -f1 | sort | head -40 || unavail "/proc/1/environ" "unreadable"
else
    # fall back to own environment names only
    env 2>/dev/null | cut -d= -f1 | sort | head -40 || unavail "env" "command failed"
fi
echo "[note] secret-shaped names (KEY/TOKEN/SECRET/PASS/CREDENTIAL) are listed by name only; no value is ever printed by this audit"

# ------------------------------------------------------------- I. COUNTERS
# Proves: per-interface traffic and error counters -- corroborates membership
# claims (a member port with zero packets is suspicious) from a read-only
# procfs source.
say "I. INTERFACE COUNTERS (/proc/net/dev, read-only)"
if [ -r /proc/net/dev ]; then
    head -2 /proc/net/dev
    tail -n +3 /proc/net/dev | head -25
else
    unavail "/proc/net/dev" "not readable"
fi

say "END OF AUDIT -- no state was modified; output is stdout only"
exit 0
