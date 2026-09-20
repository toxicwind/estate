"""swarm/nvidia_swarm_archivefs.py — ArchiveFS: chunked binary archive for swarm payloads.

Ported from the Drive maximal monolith (nvidia_lens_swarm_maximal.py §7),
which was the only source with this capability. Hardened during the merge:

- pack(): skips symlinks (original followed them, leaking files outside src).
- unpack(): rejects absolute paths and ".." traversal (original wrote
  anywhere the index said), verifies each resolved path stays inside dest,
  caps the index length against the actual payload size.

Format: 256-byte header ("ARFS\\x01\\x02", version u16, entry count u32,
index length u64) + JSON index + concatenated file bytes. SHA-256 (16 hex
chars) per entry. Payloads over chunk_limit (default 85MB) split into
.partNNN files for transport-friendly chunks.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import struct
from pathlib import Path
from typing import List

MAGIC = b"ARFS\x01\x02"
VERSION = 1
HEADER_SIZE = 256
DEFAULT_CHUNK_BYTES = 85 * 1024 * 1024
MAX_INDEX_BYTES = 512 * 1024 * 1024  # sanity cap on the JSON index


class ArchiveFSEntry:
    def __init__(self, path: str, data: bytes, mode: int = 0o644, flags: int = 0):
        self.path = path
        self.data = data
        self.size = len(data)
        self.mode = mode
        self.flags = flags
        self.checksum = hashlib.sha256(data).hexdigest()[:16]

    def to_header_dict(self) -> dict:
        return {
            "path": self.path,
            "size": self.size,
            "mode": self.mode,
            "flags": self.flags,
            "checksum": self.checksum,
        }


def _safe_join(dest: Path, rel: str) -> Path:
    """Resolve rel inside dest; raise on absolute paths or traversal."""
    if os.path.isabs(rel):
        raise ValueError(f"ArchiveFS: absolute path rejected: {rel!r}")
    target = (dest / rel).resolve()
    dest_resolved = dest.resolve()
    if target != dest_resolved and dest_resolved not in target.parents:
        raise ValueError(f"ArchiveFS: path traversal rejected: {rel!r}")
    return target


class ArchiveFS:
    @staticmethod
    def pack(src_dir: Path, output_file: Path,
             chunk_limit: int = DEFAULT_CHUNK_BYTES) -> List[Path]:
        entries: List[ArchiveFSEntry] = []
        src_path = Path(src_dir)
        for p in src_path.rglob("*"):
            if p.is_symlink() or not p.is_file():
                continue  # never follow symlinks out of src
            rel_path = str(p.relative_to(src_path))
            raw_bytes = p.read_bytes()
            st = p.stat()
            mode = st.st_mode & 0o777
            is_exec = 1 if (mode & 0o111) else 0
            is_bin = 1 if b"\x00" in raw_bytes[:1024] else 0
            flags = (is_bin & 1) | ((is_exec & 1) << 1)
            entries.append(ArchiveFSEntry(rel_path, raw_bytes, mode=mode, flags=flags))
        index_json = json.dumps([e.to_header_dict() for e in entries]).encode("utf-8")
        index_len = len(index_json)
        buf = io.BytesIO()
        header = struct.pack("<6sH I Q 236s", MAGIC, VERSION, len(entries), index_len, b"\x00" * 236)
        buf.write(header)
        buf.write(index_json)
        for e in entries:
            buf.write(e.data)
        full_payload = buf.getvalue()
        total_size = len(full_payload)
        produced_files = []
        if total_size <= chunk_limit:
            output_file.write_bytes(full_payload)
            produced_files.append(output_file)
        else:
            total_chunks = (total_size + chunk_limit - 1) // chunk_limit
            for i in range(total_chunks):
                chunk_path = output_file.with_name(
                    f"{output_file.stem}.part{i+1:03d}{output_file.suffix}")
                start_byte = i * chunk_limit
                end_byte = min(start_byte + chunk_limit, total_size)
                chunk_path.write_bytes(full_payload[start_byte:end_byte])
                produced_files.append(chunk_path)
        return produced_files

    @staticmethod
    def unpack(archive_files: List[Path], dest_dir: Path) -> int:
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)
        sorted_files = sorted(archive_files)
        full_buf = io.BytesIO()
        for f in sorted_files:
            full_buf.write(Path(f).read_bytes())
        full_payload = full_buf.getvalue()
        if len(full_payload) < HEADER_SIZE:
            raise ValueError("ArchiveFS: truncated archive (short header)")
        magic, version, count, index_len, _ = struct.unpack(
            "<6sH I Q 236s", full_payload[:HEADER_SIZE])
        if magic != MAGIC:
            raise ValueError(f"ArchiveFS: invalid magic: {magic!r}")
        if version != VERSION:
            raise ValueError(f"ArchiveFS: unsupported version {version}")
        if index_len > MAX_INDEX_BYTES or HEADER_SIZE + index_len > len(full_payload):
            raise ValueError("ArchiveFS: corrupt index length")
        index_bytes = full_payload[HEADER_SIZE:HEADER_SIZE + index_len]
        index_table = json.loads(index_bytes.decode("utf-8"))
        if len(index_table) != count:
            raise ValueError("ArchiveFS: index count mismatch")
        data_offset = HEADER_SIZE + index_len
        extracted_count = 0
        for item in index_table:
            size = item["size"]
            if size < 0 or data_offset + size > len(full_payload):
                raise ValueError(f"ArchiveFS: truncated data for {item['path']!r}")
            file_data = full_payload[data_offset:data_offset + size]
            data_offset += size
            chk = hashlib.sha256(file_data).hexdigest()[:16]
            if chk != item["checksum"]:
                raise ValueError(f"ArchiveFS: checksum mismatch for {item['path']!r}")
            out_file = _safe_join(dest_path, item["path"])
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(file_data)
            os.chmod(out_file, item["mode"])
            extracted_count += 1
        return extracted_count
