#!/usr/bin/env bash
# yote_system_fix.sh — Generated directly from yote_audit_report.json (2026-10-20)
# Fixes:
# 1. Deduplicates table inet awrawr_filter in /etc/nftables.conf (adds idempotent
#    table create + flush table inet awrawr_filter without touching Docker/Tailscale tables).
# 2. Allows DHCPv6 client renewals (udp 547->546 from link-local router) and
#    Syncthing local discovery (udp 21027 on 10.0.0.0/24).
# 3. Silently drops noisy LAN multicast/broadcast chatter (mDNS 5353, SSDP 1900,
#    2021, LIFX 56700, pkttype broadcast/multicast) and stale 10.0.0.176:50005 UDP
#    before the log rule to eliminate the kernel printk/ksoftirqd log storm.
# 4. Removes the 0-byte orphaned /var/tmp/btdu-raw.log artifact.

set -euo pipefail

sudo cp /etc/nftables.conf /etc/nftables.conf.bak-20261020

cat << 'EOF' | sudo tee /etc/nftables.conf > /dev/null
#!/usr/sbin/nft -f
# awrawr-pc baseline firewall — network audit 2026-10-15 (updated 2026-10-20)
# NOTE: deliberately NO global `flush ruleset` — dockerd and tailscaled own their own
# tables (ip filter/nat with DOCKER-*/ts-* chains). Flushing globally would destroy
# docker-published ports and tailscale netfilter until restart.
# Flushing ONLY `table inet awrawr_filter` makes this file idempotent on reload.

table inet awrawr_filter
flush table inet awrawr_filter

table inet awrawr_filter {
	chain input {
		type filter hook input priority 0; policy drop;

		# Loopback + existing connections
		iifname "lo" accept
		ct state established,related accept
		ct state invalid drop

		# ICMP / ICMPv6 diagnostics (incl. IPv6 neighbor discovery) + DHCPv6 client
		ip protocol icmp accept
		ip6 nexthdr ipv6-icmp accept
		ip6 saddr fe80::/10 udp sport 547 udp dport 546 accept

		# Tailscale data plane: WireGuard UDP (any source, direct connect)
		udp dport 41641 accept

		# Full access from the tailnet (covers RustDesk 25220-25224, SSH, all 25xxx)
		iifname "tailscale0" accept
		iifname "tsd" accept

		# LAN: SSH, Caddy/UI ports, local DNS (dnsmasq on this host), syncthing (22000 + 21027 discovery)
		ip saddr 10.0.0.0/24 tcp dport { 22, 3000, 3001, 8503, 25100-25107, 25203 } accept
		ip saddr 10.0.0.0/24 udp dport { 53, 21027, 22000, 41641 } accept
		ip saddr 10.0.0.0/24 tcp dport { 53, 22000 } accept

		# Silently drop noisy LAN broadcast/multicast discovery & stale 10.0.0.176 UDP
		# so harmless LAN background chatter does not trigger a dmesg printk log storm
		ip saddr 10.0.0.176 udp sport 50005 drop
		udp dport { 1900, 2021, 5353, 21027, 56700 } drop
		meta pkttype { broadcast, multicast } drop

		# Everything else (unexpected unicast probes) logs rate-limited and drops
		log prefix "nft-drop: " limit rate 5/second burst 5 packets
		drop
	}

	chain forward {
		type filter hook forward priority 0; policy accept;
	}

	chain output {
		type filter hook output priority 0; policy accept;
	}
}
EOF

sudo nft -f /etc/nftables.conf
sudo rm -f /var/tmp/btdu-raw.log

echo "=== POST-FIX LOADAVG ==="
cat /proc/loadavg
echo "=== POST-FIX AWRAWR_FILTER TABLE ==="
sudo nft -a list table inet awrawr_filter
