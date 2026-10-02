#!/usr/bin/env python3
"""zipfs-vault: an obfuscated zipfs repo backed by a Google Drive folder.

Adapted from encrypted-github-fs. One zip is the repo: inside it, every
entry is a blob with a random name (obfuscated), plus a manifest.json that
maps human aliases -> blob names. The zip itself is synced to a Google
Drive folder (default "zipfs"); Drive authentication is the access
boundary, random blob names are the obfuscation.

This is NOT encryption: anyone with read access to the Drive folder (or
the local zip) can unzip it. Use it for content that is fine living in
Chris's Drive but must never be served from a public endpoint — e.g. the
Squawk fleet-chat feed (replaces the held fat long-poll design).

Layout inside the zip:
    blobs/<16 hex chars>   raw bytes of one entry
    manifest.json           {alias: {blob, size, sha256, added_at}}

Sync model: single writer (awrawr-pc relay side) does put+sync; readers
(my cell hook) do pull+get. Last-writer-wins on conflict — do not have two
writers put+sync concurrently without pulling first.
"""

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
import zipfile

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(SKILL_DIR, ".env"))
except ImportError:
    pass

GWS = os.getenv("ZIPFS_GWS") or "/opt/hatch/bin/hatch_gws_cli"
RCLONE = os.getenv("ZIPFS_RCLONE") or "rclone"
RCLONE_DEST = os.getenv("ZIPFS_RCLONE_DEST") or "gdrive:/zipfs/vault.zip"
VIA_DEFAULT = os.getenv("ZIPFS_VIA") or "gws"
STORE_DIR = os.path.join(SKILL_DIR, "store")
ZIP_PATH = os.path.join(STORE_DIR, "vault.zip")
DRIVE_INDEX = os.path.join(STORE_DIR, "drive.json")
FOLDER_NAME = os.getenv("ZIPFS_DRIVE_FOLDER") or "zipfs"
REMOTE_NAME = os.getenv("ZIPFS_REMOTE_NAME") or "vault.zip"


def _gws(*args, check=True):
    r = subprocess.run([GWS, "drive", *args], capture_output=True,
                       text=True, timeout=180)
    if check and r.returncode != 0:
        raise RuntimeError(f"gws drive {' '.join(args[:3])} failed: "
                           f"{r.stderr.strip()[:300]}")
    out = r.stdout.strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"raw": out}


def _load_index():
    if os.path.exists(DRIVE_INDEX):
        with open(DRIVE_INDEX) as f:
            return json.load(f)
    return {}


def _save_index(idx):
    os.makedirs(STORE_DIR, exist_ok=True)
    with open(DRIVE_INDEX, "w") as f:
        json.dump(idx, f, indent=2)


def folder_id():
    idx = _load_index()
    if idx.get("folder_id"):
        return idx["folder_id"], idx
    res = _gws("files", "list", "--params", json.dumps({
        "q": f"name = '{FOLDER_NAME}' and "
             "mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        "fields": "files(id,name)"}))
    files = res.get("files", [])
    if not files:
        res = _gws("files", "create", "--json", json.dumps({
            "name": FOLDER_NAME,
            "mimeType": "application/vnd.google-apps.folder"}),
            "--params", json.dumps({"fields": "id,name"}))
        fid = res.get("id")
        if not fid:
            raise RuntimeError(f"could not create Drive folder '{FOLDER_NAME}': {res}")
        print(f"created Drive folder '{FOLDER_NAME}'")
    else:
        fid = files[0]["id"]
    idx["folder_id"] = fid
    _save_index(idx)
    return fid, idx


def remote_file_id(fid, idx):
    if idx.get("file_id"):
        return idx["file_id"]
    res = _gws("files", "list", "--params", json.dumps({
        "q": f"name = '{REMOTE_NAME}' and '{fid}' in parents and trashed = false",
        "fields": "files(id,name)"}))
    files = res.get("files", [])
    if files:
        idx["file_id"] = files[0]["id"]
        _save_index(idx)
        return files[0]["id"]
    return None


def _read_manifest():
    if not os.path.exists(ZIP_PATH):
        return {}
    with zipfile.ZipFile(ZIP_PATH) as zf:
        try:
            return json.loads(zf.read("manifest.json").decode())
        except KeyError:
            return {}


def _write_manifest(manifest):
    # rewrite the zip with the updated manifest (zipfile has no in-place edit)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip", dir=STORE_DIR).name
    os.makedirs(STORE_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zin, \
            zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for item in zin.infolist():
            if item.filename == "manifest.json":
                continue
            zout.writestr(item, zin.read(item.filename))
        zout.writestr("manifest.json", json.dumps(manifest, indent=2))
    os.replace(tmp, ZIP_PATH)


def _ensure_zip():
    if not os.path.exists(ZIP_PATH):
        os.makedirs(STORE_DIR, exist_ok=True)
        with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", "{}")


def sha256_of(data):
    return hashlib.sha256(data).hexdigest()


def cmd_init(args):
    _ensure_zip()
    fid, _ = folder_id()
    print(f"local: {ZIP_PATH}")
    print(f"drive folder '{FOLDER_NAME}': {fid}")


def cmd_put(args):
    _ensure_zip()
    if args.text is not None:
        data = args.text.encode()
        alias = args.alias
    else:
        with open(args.src, "rb") as f:
            data = f.read()
        alias = args.alias or os.path.basename(args.src)
    if not alias:
        raise RuntimeError("need an alias: -a <alias> or --text with -a")
    blob = secrets.token_hex(8)
    manifest = _read_manifest()
    with zipfile.ZipFile(ZIP_PATH, "a", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr(f"blobs/{blob}", data)
    manifest[alias] = {"blob": blob, "size": len(data),
                       "sha256": sha256_of(data),
                       "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    _write_manifest(manifest)
    print(f"put {alias} ({len(data)} bytes) -> blobs/{blob}")


def cmd_get(args):
    manifest = _read_manifest()
    if args.alias not in manifest:
        raise RuntimeError(f"unknown alias: {args.alias}")
    blob = manifest[args.alias]["blob"]
    with zipfile.ZipFile(ZIP_PATH) as zf:
        data = zf.read(f"blobs/{blob}")
    if args.out:
        with open(args.out, "wb") as f:
            f.write(data)
        print(f"wrote {args.out} ({len(data)} bytes)")
    else:
        sys.stdout.buffer.write(data)


def cmd_list(args):
    manifest = _read_manifest()
    if args.json:
        print(json.dumps(manifest, indent=2))
        return
    print(f"vault: {ZIP_PATH} ({len(manifest)} entries)")
    for alias in sorted(manifest):
        m = manifest[alias]
        print(f"  {alias}  {m['size']} bytes  blobs/{m['blob']}  {m['added_at']}")


def cmd_rm(args):
    manifest = _read_manifest()
    if args.alias not in manifest:
        raise RuntimeError(f"unknown alias: {args.alias}")
    blob = manifest.pop(args.alias)["blob"]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip", dir=STORE_DIR).name
    os.makedirs(STORE_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zin, \
            zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for item in zin.infolist():
            if item.filename in (f"blobs/{blob}", "manifest.json"):
                continue
            zout.writestr(item, zin.read(item.filename))
        zout.writestr("manifest.json", json.dumps(manifest, indent=2))
    os.replace(tmp, ZIP_PATH)
    print(f"rm {args.alias}")


def _rclone(*args):
    r = subprocess.run([RCLONE, *args], capture_output=True,
                       text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"rclone {' '.join(args[:3])} failed: "
                           f"{r.stderr.strip()[:300]}")
    return r.stdout.strip()


def cmd_sync(args):
    """Upload the local zip to the Drive folder (create or update in place)."""
    _ensure_zip()
    via = args.via or VIA_DEFAULT
    size = os.path.getsize(ZIP_PATH)
    if via == "rclone":
        _rclone("copyto", ZIP_PATH, RCLONE_DEST)
        print(f"rclone copyto -> {RCLONE_DEST} ({size} bytes)")
        return
    fid, idx = folder_id()
    rid = remote_file_id(fid, idx)
    if rid:
        _gws("files", "update", "--params", json.dumps({"fileId": rid}),
             "--upload", ZIP_PATH,
             "--upload-content-type", "application/zip")
        print(f"updated Drive '{REMOTE_NAME}' ({size} bytes)")
    else:
        res = _gws("files", "create",
                   "--json", json.dumps({"name": REMOTE_NAME,
                                         "parents": [fid],
                                         "mimeType": "application/zip"}),
                   "--upload", ZIP_PATH,
                   "--upload-content-type", "application/zip",
                   "--params", json.dumps({"fields": "id,name"}))
        rid = res.get("id")
        if not rid:
            raise RuntimeError(f"upload did not return a file id: {res}")
        idx["file_id"] = rid
        _save_index(idx)
        print(f"uploaded Drive '{REMOTE_NAME}' ({size} bytes): {rid}")


def cmd_pull(args):
    """Download the Drive zip over the local copy. Returns 0/1: changed?"""
    via = args.via or VIA_DEFAULT
    if via == "rclone":
        return _pull_rclone(args)
    fid, idx = folder_id()
    rid = remote_file_id(fid, idx)
    if not rid:
        raise RuntimeError("no remote vault.zip in Drive folder yet (sync first)")
    meta = _gws("files", "get", "--params",
                json.dumps({"fileId": rid,
                            "fields": "id,modifiedTime,md5Checksum,size"}))
    local_md5 = idx.get("md5")
    if local_md5 and meta.get("md5Checksum") == local_md5 and not args.force:
        print("unchanged (md5 match)")
        return 0
    os.makedirs(STORE_DIR, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip", dir=STORE_DIR).name
    os.makedirs(STORE_DIR, exist_ok=True)
    # NOTE: `files download` only returns a downloadUri operation; the bytes
    # come from `files get` with alt=media.
    _gws("files", "get", "--params",
         json.dumps({"fileId": rid, "alt": "media"}), "-o", tmp)
    os.replace(tmp, ZIP_PATH)
    idx["md5"] = meta.get("md5Checksum")
    _save_index(idx)
    print(f"pulled Drive '{REMOTE_NAME}' ({meta.get('size')} bytes, "
          f"modified {meta.get('modifiedTime')})")
    return 0


def _pull_rclone(args):
    os.makedirs(STORE_DIR, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip",
                                      dir=STORE_DIR).name
    os.makedirs(STORE_DIR, exist_ok=True)
    _rclone("copyto", RCLONE_DEST, tmp)
    if not args.force and os.path.exists(ZIP_PATH):
        if sha256_of_file(ZIP_PATH) == sha256_of_file(tmp):
            os.unlink(tmp)
            print("unchanged (sha256 match)")
            return 0
    os.replace(tmp, ZIP_PATH)
    print(f"pulled {RCLONE_DEST} ({os.path.getsize(ZIP_PATH)} bytes)")
    return 0


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description="obfuscated zipfs repo on Google Drive")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("init", help="create local zip + Drive folder, print ids")

    pu = sub.add_parser("put", help="add a file/text to the vault")
    pu.add_argument("src", nargs="?", help="file to store")
    pu.add_argument("-a", "--alias", help="alias (default: basename)")
    pu.add_argument("--text", help="store inline text instead of a file")

    g = sub.add_parser("get", help="fetch an entry (stdout or -o)")
    g.add_argument("alias")
    g.add_argument("-o", "--out")

    li = sub.add_parser("list", help="list aliases")
    li.add_argument("--json", action="store_true")

    r = sub.add_parser("rm", help="delete an entry")
    r.add_argument("alias")

    sy = sub.add_parser("sync", help="upload local zip -> Drive folder")
    sy.add_argument("--via", choices=["gws", "rclone"],
                    help="transport (default: $ZIPFS_VIA or gws)")

    pl = sub.add_parser("pull", help="download Drive zip -> local (skips if unchanged)")
    pl.add_argument("--force", action="store_true")
    pl.add_argument("--via", choices=["gws", "rclone"],
                    help="transport (default: $ZIPFS_VIA or gws)")

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return 2
    try:
        rc = {"init": cmd_init, "put": cmd_put, "get": cmd_get,
              "list": cmd_list, "rm": cmd_rm, "sync": cmd_sync,
              "pull": cmd_pull}[args.cmd](args)
    except Exception as e:  # noqa: BLE001 - CLI surface
        print(f"error: {e}", file=sys.stderr)
        return 1
    return rc if isinstance(rc, int) else 0


if __name__ == "__main__":
    sys.exit(main())
