#!/usr/bin/env python3
"""openfang-mcp-shim: NDJSON <-> Content-Length MCP stdio bridge.

The openfang Rust binary's `mcp` server speaks LSP-style Content-Length
framing on stdio, while mcpproxy/shep (and most MCP clients) speak
newline-delimited JSON. This shim translates both directions so the
openfang agent tools can live behind the mesh gateway.

    stdin (NDJSON) -> [shim] -> Content-Length frames -> `openfang mcp`
    `openfang mcp` -> Content-Length frames -> [shim] -> stdout (NDJSON)

Stderr from the child is forwarded to our stderr (gateway server logs).
No secrets are handled here; the child inherits the gateway environment.
"""
import json
import os
import select
import subprocess
import sys
import time

BIN = os.environ.get("OPENFANG_BIN", "/home/toxic/.local/bin/openfang")
DRAIN_GRACE_S = 10.0


def read_frame(stream, buf, timeout=30.0):
    """Read one Content-Length framed message from child's stdout."""
    deadline = time.time() + timeout
    while b"\r\n\r\n" not in buf:
        if time.time() > deadline:
            return None, buf
        r, _, _ = select.select([stream], [], [], 0.5)
        if not r:
            continue
        chunk = os.read(stream.fileno(), 65536)
        if not chunk:
            return None, buf
        buf += chunk
    head, rest = buf.split(b"\r\n\r\n", 1)
    length = 0
    for line in head.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            length = int(line.split(b":", 1)[1].strip())
            break
    while len(rest) < length:
        if time.time() > deadline:
            break
        r, _, _ = select.select([stream], [], [], 0.5)
        if not r:
            continue
        chunk = os.read(stream.fileno(), 65536)
        if not chunk:
            break
        rest += chunk
    if len(rest) < length:
        return None, buf
    return rest[:length], rest[length:]


def main():
    child = subprocess.Popen(
        [BIN, "mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,  # forward child logs straight through
    )
    child_buf = b""
    stdin_fd = sys.stdin.fileno()
    stdin_open = True
    drain_deadline = None
    try:
        while True:
            if child.poll() is not None:
                # child exited: flush whatever is left, then stop
                while True:
                    msg, child_buf = read_frame(child.stdout, child_buf, timeout=1.0)
                    if msg is None:
                        break
                    sys.stdout.buffer.write(msg + b"\n")
                sys.stdout.buffer.flush()
                break
            watch = [child.stdout]
            if stdin_open:
                watch.append(stdin_fd)
            r, _, _ = select.select(watch, [], [], 1.0)
            if stdin_fd in r:
                data = os.read(stdin_fd, 65536)
                if not data:
                    stdin_open = False
                    drain_deadline = time.time() + DRAIN_GRACE_S
                    try:
                        child.stdin.close()
                    except Exception:
                        pass
                else:
                    for piece in data.split(b"\n"):
                        piece = piece.strip()
                        if not piece:
                            continue
                        try:
                            json.loads(piece)
                        except Exception:
                            continue
                        frame = b"Content-Length: %d\r\n\r\n" % len(piece) + piece
                        try:
                            child.stdin.write(frame)
                            child.stdin.flush()
                        except BrokenPipeError:
                            stdin_open = False
                            break
            if child.stdout in r:
                msg, child_buf = read_frame(child.stdout, child_buf)
                if msg is None:
                    break
                sys.stdout.buffer.write(msg + b"\n")
                sys.stdout.buffer.flush()
                drain_deadline = None  # progress resets the drain clock
            if not stdin_open and drain_deadline and time.time() > drain_deadline:
                break
    finally:
        try:
            child.stdin.close()
        except Exception:
            pass
        try:
            child.wait(timeout=5)
        except Exception:
            child.kill()


if __name__ == "__main__":
    main()
