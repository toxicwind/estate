#!/usr/bin/env python3
"""wsframe.py — shared stdlib-only websocket framing for the awrawr bridge.

No third-party deps and no credential imports, so it is importable both
from the cell (ws_daemon.py, xfer.py) and from awrawr-pc's interactive
shell (xfer.py --via direct).
"""
import secrets

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


async def read_frame(reader):
    hdr = await reader.readexactly(2)
    fin = bool(hdr[0] & 0x80)
    opcode = hdr[0] & 0x0F
    masked = bool(hdr[1] & 0x80)
    length = hdr[1] & 0x7F
    if length == 126:
        length = int.from_bytes(await reader.readexactly(2), "big")
    elif length == 127:
        length = int.from_bytes(await reader.readexactly(8), "big")
    mask = await reader.readexactly(4) if masked else None
    payload = await reader.readexactly(length) if length else b""
    if mask:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return fin, opcode, payload


async def send_frame(writer, opcode, payload=b"", mask=True):
    """Send one frame. Clients MUST mask (mask=True); servers must not."""
    hdr = bytes([0x80 | opcode])
    n = len(payload)
    if n < 126:
        hdr += bytes([(0x80 if mask else 0) | n])
    elif n < 65536:
        hdr += bytes([(0x80 if mask else 0) | 126]) + n.to_bytes(2, "big")
    else:
        hdr += bytes([(0x80 if mask else 0) | 127]) + n.to_bytes(8, "big")
    if mask:
        m = secrets.token_bytes(4)
        payload = bytes(b ^ m[i % 4] for i, b in enumerate(payload))
        hdr += m
    writer.write(hdr + payload)
    await writer.drain()


async def read_message(reader):
    """One complete message -> (is_text, bytes). Raises on close."""
    buf = bytearray()
    is_text = True
    while True:
        fin, opcode, payload = await read_frame(reader)
        if opcode == 0x8:
            raise ConnectionError("websocket closed by peer")
        if opcode == 0x9:  # ping; caller should pong, we surface it
            return ("ping", bytes(payload))
        if opcode in (0x1, 0x2):
            is_text = (opcode == 0x1)
            buf = bytearray(payload)
        elif opcode == 0x0:
            buf += payload
        else:
            continue
        if fin:
            return (is_text, bytes(buf))
