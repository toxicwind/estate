#!/usr/bin/env python3
"""Local TCP forward: 127.0.0.1:3129 -> egress proxy (IPv6).

Raw Chromium in this sandbox cannot speak IPv6 to the egress proxy, so it
gets ERR_EMPTY_RESPONSE on every navigation. This forwarder bridges
IPv4 loopback to the proxy's IPv6 endpoint. The proxy itself allows
unauthenticated CONNECT from this VM (verified with curl).

Usage: proxy_fwd.py [listen_port]   # default 3129; runs forever
"""
import socket
import threading
import sys

PROXY_HOST = "hatch-egress-proxy"
PROXY_PORT = 3128

# HFT: resolve the upstream once, not per connection — the address is
# stable for the life of the process. Re-resolved only when a connect
# fails (fail-fast, then one fresh attempt).
_UPSTREAM_ADDR = None
_UPSTREAM_LOCK = threading.Lock()


def _resolve_upstream():
    global _UPSTREAM_ADDR
    with _UPSTREAM_LOCK:
        if _UPSTREAM_ADDR is None:
            infos = socket.getaddrinfo(PROXY_HOST, PROXY_PORT,
                                       type=socket.SOCK_STREAM)
            fam, typ, proto, _, addr = infos[0]
            _UPSTREAM_ADDR = (fam, typ, proto, addr)
        return _UPSTREAM_ADDR


def _invalidate_upstream():
    global _UPSTREAM_ADDR
    with _UPSTREAM_LOCK:
        _UPSTREAM_ADDR = None


def _nodelay(sock):
    """Disable Nagle on a relay socket.

    HFT: the relay forwards small TLS handshake records; with Nagle
    enabled each small write can stall ~200ms waiting for an ACK. This
    was measured adding ~100ms per proxied HTTPS request.
    """
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError:
        pass


def pipe(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        for s in (src, dst):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            s.close()


def handle(client):
    _nodelay(client)
    upstream = None
    for attempt in (0, 1):
        try:
            fam, typ, proto, addr = _resolve_upstream()
            upstream = socket.socket(fam, typ, proto)
            _nodelay(upstream)
            upstream.connect(addr)
            break
        except OSError:
            _invalidate_upstream()
            upstream = None
            if attempt:
                client.close()
                return
    threading.Thread(target=pipe, args=(client, upstream), daemon=True).start()
    threading.Thread(target=pipe, args=(upstream, client), daemon=True).start()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3129
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(100)
    print(f"forwarding 127.0.0.1:{port} -> {PROXY_HOST}:{PROXY_PORT}", flush=True)
    while True:
        client, _ = srv.accept()
        threading.Thread(target=handle, args=(client,), daemon=True).start()


if __name__ == "__main__":
    main()
