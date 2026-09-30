import os, sys, stat
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

scan_roots = [
    os.path.expanduser("~/.local/bin"),
    os.path.expanduser("~/bin"),
    os.path.expanduser("~/sovereign/bin"),
    os.path.expanduser("~/.cargo/bin"),
    os.path.expanduser("~/.bun/bin"),
    os.path.expanduser("~/sovereign/projects/tau/launcher"),
    os.path.expanduser("~/sovereign/projects/mesh/bin"),
    os.path.expanduser("~/sovereign"),
    os.path.expanduser("~")
]

records = []

for root_dir in scan_roots:
    if not os.path.exists(root_dir):
        continue
    max_d = 1 if root_dir == os.path.expanduser("~") else 3
    base_depth = root_dir.rstrip("/").count("/")
    
    for root, dirs, files in os.walk(root_dir):
        depth = root.count("/") - base_depth
        if depth > max_d:
            dirs.clear()
            continue
        if any(skip in root for skip in [".git", "node_modules", "target", "dotfiles_pull", ".cache", "cache", "gist-archive"]):
            dirs.clear()
            continue
            
        for name in files + dirs:
            p = os.path.join(root, name)
            is_link = os.path.islink(p)
            link_target = ""
            is_broken = False
            if is_link:
                try:
                    link_target = os.readlink(p)
                    is_broken = not os.path.exists(p)
                except Exception:
                    is_broken = True
            
            is_dir = os.path.isdir(p) and not is_link
            is_file = os.path.isfile(p) or (is_link and not is_dir)
            is_exec = os.access(p, os.X_OK) if os.path.exists(p) else False
            
            bizarre_reasons = []
            if ":" in name:
                bizarre_reasons.append("colon_in_name")
            if name.startswith("100644") or name.startswith("100755"):
                bizarre_reasons.append("git_mode_in_name")
            if name.startswith(" ") or name.endswith(" "):
                bizarre_reasons.append("whitespace_padding")
            if "\\" in name:
                bizarre_reasons.append("backslash_in_name")
            if is_broken and ("bin" in root or root == os.path.expanduser("~")):
                bizarre_reasons.append("broken_symlink_in_bin")
            if (name.endswith(".bak") or ".bak-" in name) and "bin" in root:
                bizarre_reasons.append("backup_pile_in_bin")
                
            records.append({
                "dir": root,
                "name": name,
                "full_path": p,
                "is_link": is_link,
                "is_broken_link": is_broken,
                "link_target": link_target,
                "is_file": is_file,
                "is_dir": is_dir,
                "is_exec": is_exec,
                "is_bizarre": len(bizarre_reasons) > 0,
                "bizarre_reasons": ",".join(bizarre_reasons),
                "size_bytes": os.path.getsize(p) if os.path.exists(p) and not is_dir else 0
            })

df = pd.DataFrame(records)
table = pa.Table.from_pandas(df)
pq.write_table(table, "/tmp/bin_audit.parquet")

print(f"Total scanned paths: {len(df)}")
print(f"Total bizarre/anomalous entries: {len(df[df['is_bizarre']])}")

bizarre_df = df[df["is_bizarre"]][["name", "full_path", "bizarre_reasons", "link_target"]]
for reason, group in bizarre_df.groupby("bizarre_reasons"):
    print(f"\n[Reason: {reason}] (Count: {len(group)})")
    for idx, row in group.iterrows():
        n = row["name"]
        fp = row["full_path"]
        tgt = row["link_target"] if row["link_target"] else "none"
        print(f"  - {n} ({fp}) -> {tgt}")
