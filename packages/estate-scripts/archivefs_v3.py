#!/usr/bin/env python3
"""ArchiveFS v3 - Mount-like binary archive with 90MB chunking."""
import struct, os, json, hashlib, sys
from pathlib import Path

MAGIC = b"ARFS\x03\x00"
VERSION = 3
CHUNK_MAX = 90 * 1024 * 1024

class Entry:
    __slots__ = ["path", "data", "size", "mode", "flags", "checksum"]
    def __init__(self, path, data, mode=0o644, flags=0):
        self.path = path
        self.data = data
        self.size = len(data)
        self.mode = mode
        self.flags = flags
        self.checksum = hashlib.sha256(data).hexdigest()[:16]

class ArchiveFS:
    def __init__(self):
        self.entries = {}

    def add_file(self, path, data, mode=0o644, flags=0):
        self.entries[path] = Entry(path, data, mode, flags)

    def add_from_disk(self, filepath, arcpath=None):
        arcpath = arcpath or str(filepath)
        data = filepath.read_bytes()
        mode = filepath.stat().st_mode
        flags = 0x01 if os.access(filepath, os.X_OK) else 0x00
        self.add_file(arcpath, data, mode, flags)

    def write(self, output):
        index_bytes = b""
        data_bytes = b""
        offset = 0
        for e in self.entries.values():
            path_b = e.path.encode("utf-8")
            nchunks = (e.size + CHUNK_MAX - 1) // CHUNK_MAX
            index_bytes += struct.pack("<H", len(path_b)) + path_b
            index_bytes += struct.pack("<I", nchunks)
            pos = 0
            for _ in range(nchunks):
                chunk = e.data[pos:pos+CHUNK_MAX]
                index_bytes += struct.pack("<Q", offset) + struct.pack("<Q", len(chunk))
                data_bytes += chunk
                offset += len(chunk)
                pos += len(chunk)
            index_bytes += struct.pack("<I", e.mode) + struct.pack("<Q", int(e.checksum, 16)) + struct.pack("<B", e.flags)
        header = MAGIC + struct.pack("<H", VERSION) + struct.pack("<I", len(self.entries))
        header += struct.pack("<Q", 256) + struct.pack("<Q", 256 + len(index_bytes)) + struct.pack("<B", 0)
        header += b"\x00" * (256 - len(header))
        with open(output, "wb") as f:
            f.write(header + index_bytes + data_bytes)
        return output.stat().st_size

    @classmethod
    def read(cls, input_path):
        ar = cls()
        with open(input_path, "rb") as f:
            hdr = f.read(256)
            if hdr[:6] != MAGIC: raise ValueError("Invalid magic")
            count = struct.unpack("<I", hdr[8:12])[0]
            data_off = struct.unpack("<Q", hdr[20:28])[0]
            f.seek(256)
            for _ in range(count):
                pl = struct.unpack("<H", f.read(2))[0]
                path = f.read(pl).decode("utf-8")
                nchunks = struct.unpack("<I", f.read(4))[0]
                data = b""
                for __ in range(nchunks):
                    coff = struct.unpack("<Q", f.read(8))[0]
                    csz = struct.unpack("<Q", f.read(8))[0]
                    pos = f.tell()
                    f.seek(data_off + coff)
                    data += f.read(csz)
                    f.seek(pos)
                mode = struct.unpack("<I", f.read(4))[0]
                f.read(8); f.read(1)
                ar.entries[path] = Entry(path, data, mode)
        return ar

    def cat(self, path):
        e = self.entries.get(path)
        if not e: raise FileNotFoundError(path)
        sys.stdout.buffer.write(e.data)

    def ls(self, prefix=""):
        return [p for p in self.entries if p.startswith(prefix)]

    def extract(self, output_dir):
        for e in self.entries.values():
            out = Path(output_dir) / e.path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(e.data)
            os.chmod(out, e.mode)
        return len(self.entries)

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["create", "cat", "ls", "extract", "test"])
    p.add_argument("-i", "--input")
    p.add_argument("-o", "--output")
    p.add_argument("-f", "--files", nargs="+")
    p.add_argument("-p", "--path", default="")
    args = p.parse_args()
    if args.cmd == "create":
        ar = ArchiveFS()
        for f in args.files or []:
            fp = Path(f)
            if fp.exists(): ar.add_from_disk(fp)
        sz = ar.write(Path(args.output))
        print(f"Created: {args.output} ({sz} bytes, {len(ar.entries)} entries)")
    elif args.cmd == "cat":
        ar = ArchiveFS.read(Path(args.input))
        ar.cat(args.path)
    elif args.cmd == "ls":
        ar = ArchiveFS.read(Path(args.input))
        for p in ar.ls(args.path): print(p)
    elif args.cmd == "extract":
        ar = ArchiveFS.read(Path(args.input))
        n = ar.extract(Path(args.output))
        print(f"Extracted {n} files")
    elif args.cmd == "test":
        ar = ArchiveFS()
        ar.add_file("test.txt", b"Hello v3")
        big = b"X" * (CHUNK_MAX + 1000)
        ar.add_file("big.bin", big, 0o755, 0x01)
        ar.write(Path("/tmp/test_v3.arfs"))
        ar2 = ArchiveFS.read(Path("/tmp/test_v3.arfs"))
        assert ar2.entries["test.txt"].data == b"Hello v3"
        assert len(ar2.entries["big.bin"].data) == len(big)
        print("v3 self-test PASSED")

if __name__ == "__main__":
    main()
