#!/usr/bin/env python3
"""arfs-cat.py: cat/ls files from ArchiveFS without extraction."""
import struct, sys, os
from pathlib import Path

MAGIC = b"ARFS\x03\x00"

def read_entry(f, data_off):
    pl = struct.unpack("<H", f.read(2))[0]
    path = f.read(pl).decode("utf-8")
    nchunks = struct.unpack("<I", f.read(4))[0]
    data = b""
    for _ in range(nchunks):
        coff = struct.unpack("<Q", f.read(8))[0]
        csz = struct.unpack("<Q", f.read(8))[0]
        pos = f.tell()
        f.seek(data_off + coff)
        data += f.read(csz)
        f.seek(pos)
    mode = struct.unpack("<I", f.read(4))[0]
    f.read(8); f.read(1)  # skip checksum, flags
    return path, data, mode

def cat(arfs_path, file_path):
    with open(arfs_path, "rb") as f:
        hdr = f.read(256)
        if hdr[:6] != MAGIC:
            print("Invalid archive", file=sys.stderr)
            sys.exit(1)
        count = struct.unpack("<I", hdr[8:12])[0]
        data_off = struct.unpack("<Q", hdr[20:28])[0]
        f.seek(256)
        for _ in range(count):
            path, data, mode = read_entry(f, data_off)
            if path == file_path:
                sys.stdout.buffer.write(data)
                return
        print(f"{file_path}: not found", file=sys.stderr)
        sys.exit(1)

def ls(arfs_path, prefix=""):
    with open(arfs_path, "rb") as f:
        hdr = f.read(256)
        if hdr[:6] != MAGIC:
            print("Invalid archive", file=sys.stderr)
            sys.exit(1)
        count = struct.unpack("<I", hdr[8:12])[0]
        data_off = struct.unpack("<Q", hdr[20:28])[0]
        f.seek(256)
        for _ in range(count):
            path, data, mode = read_entry(f, data_off)
            if path.startswith(prefix):
                print(path)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["cat", "ls"])
    p.add_argument("archive")
    p.add_argument("-p", "--path", default="")
    args = p.parse_args()
    if args.cmd == "cat":
        cat(args.archive, args.path)
    elif args.cmd == "ls":
        ls(args.archive, args.path)
