#!/bin/sh
# pcap-install.sh — reproduce the cell packet-capture toolchain from the net.
# Chris's directive: missing binaries are fetched, never a blocker.
# Fetches tcpdump + libpcap + libnl3 + libibverbs debs from the Ubuntu archive
# (DNS via 1.1.1.1 DoH, per directive) and extracts them into a pcaproot dir.
#
# Usage: pcap-install.sh [prefix]
#   prefix defaults to ~/workspace/bin ; produces $prefix/pcaproot
#   and expects the caller to use $prefix/tcpdump (wrapper, committed alongside).
set -eu

PREFIX="${1:-$HOME/workspace/bin}"
ROOT="$PREFIX/pcaproot"
DEBS="$(mktemp -d)"
trap 'rm -rf "$DEBS"' EXIT

doh() {
  # DNS-over-HTTPS via 1.1.1.1 ; prints first A record for $1
  curl -s --max-time 15 'https://1.1.1.1/dns-query?name='"$1"'&type=A' \
    -H 'accept: application/dns-json' | python3 -c \
    'import json,sys; d=json.load(sys.stdin); print(d["Answer"][0]["data"])'
}

ARCH_HOST="archive.ubuntu.com"
ARCH_IP="$(doh "$ARCH_HOST")"
echo "[pcap-install] $ARCH_HOST -> $ARCH_IP (via DoH 1.1.1.1)"

fetch_deb() { # $1 = pool path fragment, $2 = grep pattern
  page="$(curl -s --max-time 20 --resolve "$ARCH_HOST:80:$ARCH_IP" \
    "http://$ARCH_HOST/ubuntu/$1/")"
  deb="$(printf '%s' "$page" | grep -oE "href=\"$2\"" | sort -u | tail -1 \
    | sed 's/href="//;s/"//')"
  [ -n "$deb" ] || { echo "[pcap-install] FATAL: no deb matched $2 in $1" >&2; exit 1; }
  echo "[pcap-install] fetching $deb"
  curl -s --max-time 60 --resolve "$ARCH_HOST:80:$ARCH_IP" \
    -o "$DEBS/$(basename "$deb")" "http://$ARCH_HOST/ubuntu/$1/$deb"
}

mkdir -p "$ROOT"
fetch_deb "pool/main/t/tcpdump" 'tcpdump_[^"]*_amd64\.deb'
fetch_deb "pool/main/libp/libpcap" 'libpcap0\.8t64_[^"]*_amd64\.deb'
fetch_deb "pool/main/libn/libnl3" 'libnl-3-200t64_[^"]*_amd64\.deb'
fetch_deb "pool/main/libn/libnl3" 'libnl-route-3-200t64_[^"]*_amd64\.deb'
fetch_deb "pool/main/r/rdma-core" 'libibverbs1_[^"]*_amd64\.deb'

for d in "$DEBS"/*.deb; do
  echo "[pcap-install] extracting $(basename "$d")"
  dpkg-deb -x "$d" "$ROOT"
done

export LD_LIBRARY_PATH="$ROOT/usr/lib/x86_64-linux-gnu"
"$ROOT/usr/bin/tcpdump" --version 2>&1 | grep -v 'no version information' | head -2
echo "[pcap-install] done -> $ROOT"
echo "[pcap-install] use: $PREFIX/tcpdump -i <iface> ..."
