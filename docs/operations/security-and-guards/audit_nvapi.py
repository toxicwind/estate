import os
import re
import json
import urllib.request
import urllib.error

OUT_FILE = "/home/toxic/nvapi_audit_results.json"

results = {
    "scanned_locations": [],
    "keys_found": {}, # key_hash -> {masked, sources: []}
    "account_probes": {}
}

# Regex for nvapi keys
KEY_PAT = re.compile(r"nvapi-[A-Za-z0-9_-]{20,}")

candidate_dirs = [
    os.path.expanduser("~/.secrets"),
    os.path.expanduser("~/.config"),
    os.path.expanduser("~/estate"),
    os.path.expanduser("~/projects"),
]

candidate_files = [
    os.path.expanduser("~/.bashrc"),
    os.path.expanduser("~/.profile"),
    os.path.expanduser("~/.bash_profile"),
    os.path.expanduser("~/.env"),
]

found_keys = {} # raw_key -> list of file paths

def scan_text(text, source_path):
    for match in KEY_PAT.finditer(text):
        k = match.group(0)
        found_keys.setdefault(k, []).append(source_path)

# 1. Scan env vars
for k, v in os.environ.items():
    if "nvapi" in v.lower() or "nvidia" in k.lower():
        scan_text(f"{k}={v}", "environ:" + k)

# 2. Scan specific files
for fpath in candidate_files:
    if os.path.isfile(fpath):
        try:
            with open(fpath, "r", errors="ignore") as f:
                scan_text(f.read(), fpath)
        except Exception as e:
            pass

# 3. Walk directories (skipping huge/binary dirs)
skip_dirs = {".git", "node_modules", ".cache", "venv", ".venv", "dist", "build", ".bazel", ".cargo", "target"}

for base_dir in candidate_dirs:
    if not os.path.isdir(base_dir):
        continue
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            # Check likely files
            ext = os.path.splitext(fname)[1].lower()
            if ext in [".json", ".yaml", ".yml", ".toml", ".sh", ".env", ".ts", ".js", ".py", ".conf", ".txt", ""] or "secret" in fname.lower() or "key" in fname.lower() or "router" in fname.lower():
                fpath = os.path.join(root, fname)
                try:
                    # Limit file size to 2MB to avoid huge binaries
                    if os.path.getsize(fpath) < 2 * 1024 * 1024:
                        with open(fpath, "r", errors="ignore") as f:
                            scan_text(f.read(), fpath)
                except Exception:
                    pass

TARGET_ACCOUNT = "iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY"

probe_results = []

for raw_key, sources in found_keys.items():
    masked = raw_key[:10] + "..." + raw_key[-6:]
    info = {
        "masked": masked,
        "sources": list(set(sources)),
        "account_id": None,
        "is_target_account": False,
        "chat_status": None,
        "chat_detail": None,
        "models_status": None
    }
    
    # Probe 1: GET /v1/models
    try:
        req = urllib.request.Request(
            "https://integrate.api.nvidia.com/v1/models",
            headers={"Authorization": f"Bearer {raw_key}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            info["models_status"] = resp.status
    except urllib.error.HTTPError as e:
        info["models_status"] = e.code
    except Exception as e:
        info["models_status"] = str(e)
        
    # Probe 2: POST /v1/chat/completions with moonshotai/kimi-k3 to extract the account ID from the NVCF error
    try:
        body = json.dumps({
            "model": "moonshotai/kimi-k3",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 5
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {raw_key}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            info["chat_status"] = resp.status
    except urllib.error.HTTPError as e:
        info["chat_status"] = e.code
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
            detail = err_json.get("detail", "")
            info["chat_detail"] = detail
            
            # Match account: Function '...': Not found for account 'ACCOUNT_ID'
            m = re.search(r"Not found for account '([^']+)'", detail)
            if m:
                info["account_id"] = m.group(1)
                if info["account_id"] == TARGET_ACCOUNT:
                    info["is_target_account"] = True
        except Exception as pe:
            info["chat_detail"] = str(pe)
    except Exception as e:
        info["chat_status"] = str(e)
        
    # Probe 3: Try standard model (meta/llama-3.1-8b-instruct)
    try:
        body = json.dumps({
            "model": "meta/llama-3.1-8b-instruct",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 1
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {raw_key}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            info["standard_model_status"] = resp.status
    except urllib.error.HTTPError as e:
        info["standard_model_status"] = e.code
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
            info["standard_model_detail"] = err_json.get("detail", "")
            if not info["account_id"]:
                m = re.search(r"Not found for account '([^']+)'", str(err_json))
                if m:
                    info["account_id"] = m.group(1)
                    if info["account_id"] == TARGET_ACCOUNT:
                        info["is_target_account"] = True
        except Exception:
            pass
    except Exception as e:
        info["standard_model_status"] = str(e)

    probe_results.append(info)

final_data = {
    "target_account": TARGET_ACCOUNT,
    "total_unique_keys": len(found_keys),
    "probe_results": probe_results
}

with open(OUT_FILE, "w") as f:
    json.dump(final_data, f, indent=2)

print(f"DONE: found {len(found_keys)} keys. Wrote to {OUT_FILE}")
