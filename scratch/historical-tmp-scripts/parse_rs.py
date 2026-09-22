#!/usr/bin/env python3
"""Full recursive parser for Firefox Remote Settings IDB record blobs.
Format (reverse-engineered, verified against known recipes):
  blob = snappy_raw_compress( payload )
  payload = [u32 version=3][u32 magic=0xFFF10000][u32 0][u32 0xFFFF0008]
            { key value }* [u32 0][u32 0xFFFF0013]
  key    = [u32 0x80000000|len][u32 0xFFFF0004][bytes][0-pad to 8]
  string = same as key; if len word lacks 0x80000000 it is UTF-16LE
           with [u32 code_units][u32 0xFFFF0004][utf16le bytes][pad]
  int32  = [u32 val][u32 0xFFFF0003]
  bool   = [u32 0/1][u32 0xFFFF0002]
  null   = 00 00 00 00 00 00 ff ff   (also [u32 0][u32 0xFFFF0000])
  double = [u64 LE]  (tagless; only last_modified in practice)
  object = [u32 0][u32 0xFFFF0008] {key value}* [u32 0][u32 0xFFFF0013]
  array  = [u32 count][u32 0xFFFF0007] ([int idx][value])* [u32 0][u32 0xFFFF0013]
"""
import sqlite3, struct, json, sys, datetime

def snappy_raw(data):
    pos = 0; shift = 0; n = 0
    while True:
        b = data[pos]; pos += 1
        n |= (b & 0x7f) << shift
        if not (b & 0x80):
            break
        shift += 7
    out = bytearray(); mv = memoryview(data)
    while pos < len(data):
        tag = data[pos]; pos += 1; t = tag & 0x03
        if t == 0:
            ln = tag >> 2
            if ln < 60:
                ln += 1
            else:
                nb = ln - 59
                ln = int.from_bytes(mv[pos:pos+nb], "little") + 1
                pos += nb
            out += mv[pos:pos+ln]; pos += ln
        else:
            if t == 1:
                ln = ((tag >> 2) & 0x07) + 4
                off = ((tag >> 5) << 8) | data[pos]; pos += 1
            elif t == 2:
                ln = (tag >> 2) + 1
                off = int.from_bytes(mv[pos:pos+2], "little"); pos += 2
            else:
                ln = (tag >> 2) + 1
                off = int.from_bytes(mv[pos:pos+4], "little"); pos += 4
            st = len(out) - off
            for i in range(ln):
                out.append(out[st+i])
    assert len(out) == n, (len(out), n)
    return bytes(out)

def u32(b, p):
    return struct.unpack("<I", b[p:p+4])[0]

class P:
    def __init__(self, b):
        self.b = b

    def string(self, p):
        lw = u32(self.b, p)
        assert u32(self.b, p+4) == 0xFFFF0004, "strtag %08x @%x" % (u32(self.b, p+4), p)
        if lw & 0x80000000:
            # latin1/utf-8 bytes
            ln = lw & 0x7FFFFFFF
            s = self.b[p+8:p+8+ln].decode("utf-8", "replace")
            e = p + 8 + ln
        else:
            # utf-16le: lw = code unit count
            ln = lw
            s = self.b[p+8:p+8+ln*2].decode("utf-16-le", "replace")
            e = p + 8 + ln*2
        e += (-e) % 8
        return s, e

    def value(self, p, depth=0):
        b = self.b
        a = u32(b, p); c = u32(b, p+4)
        if c == 0xFFFF0004:
            return self.string(p)
        if a == 0 and c == 0xFFFF0008:
            p += 8; obj = {}
            while True:
                if u32(b, p) == 0 and u32(b, p+4) == 0xFFFF0013:
                    return obj, p+8
                k, p = self.string(p)
                v, p = self.value(p, depth+1)
                obj[k] = v
        if c == 0xFFFF0007:
            n = a; p += 8; arr = []
            for _ in range(n):
                idx, p = self.value(p, depth+1)   # index int
                v, p = self.value(p, depth+1)
                arr.append(v)
            if u32(b, p) == 0 and u32(b, p+4) == 0xFFFF0013:
                p += 8
            return arr, p
        if c == 0xFFFF0003:
            v = a if a < 0x80000000 else a - 0x100000000
            return v, p+8
        if c == 0xFFFF0002:
            return bool(a), p+8
        if b[p:p+8] == b"\x00\x00\x00\x00\x00\x00\xff\xff":
            return None, p+8
        if a == 0 and c == 0xFFFF0000:
            return None, p+8
        d = struct.unpack("<d", b[p:p+8])[0]
        return d, p+8

    def record(self, blob):
        raw = snappy_raw(blob)
        assert u32(raw, 0) == 3, "version"
        # header: [u32 3][u32 magic][u32 0][u32 objtag] then pairs
        assert u32(raw, 8) == 0 and u32(raw, 12) == 0xFFFF0008, "objhead"
        self.b = raw
        p = 16; obj = {}
        while True:
            if u32(raw, p) == 0 and u32(raw, p+4) == 0xFFFF0013:
                break
            k, p = self.string(p)
            v, p = self.value(p)
            obj[k] = v
        return obj

def dec_key(k):
    k = k[1:] if k[:1] == b"\x80" else k
    parts = k.split(b"\x00")
    f = lambda x: bytes((v-1) & 0xff for v in x).decode("utf-8", "replace")
    return f(parts[0]), f(parts[1]) if len(parts) > 1 else "?"

def main():
    dbpath = sys.argv[1]
    only = sys.argv[2] if len(sys.argv) > 2 else None
    db = sqlite3.connect("file:%s?mode=ro" % dbpath, uri=True)
    c = db.cursor()
    pr = P(b"")
    n_ok = n_fail = 0
    for (k, d) in c.execute("SELECT key,data FROM object_data WHERE object_store_id=1"):
        cid, rid = dec_key(k)
        if only and only not in cid and only not in rid:
            continue
        pr.b = b""
        try:
            rec = P(b"").record(d)
            n_ok += 1
        except Exception as e:
            n_fail += 1
            import traceback
            print("FAIL %s/%s: %s" % (cid, rid, e), file=sys.stderr)
            traceback.print_exc()
            continue
        if only:
            print(json.dumps(rec, indent=1, default=str))
    print("ok=%d fail=%d" % (n_ok, n_fail), file=sys.stderr)

if __name__ == "__main__":
    main()
