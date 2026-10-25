#!/usr/bin/env python3
# FINAL - NO SLICING ON OUTPUT - OCT 2026
# kilo providers synced - omnibus nup | ndn | nst | nt | nim-audit | nim-cve-check
import os, sys, json, time, asyncio, pathlib, tarfile
from curl_cffi import requests as cffi
import requests as std
KEY=os.environ.get("FI_KEY") or os.environ.get("FREEINFERENCE_API_KEY")
assert KEY, "export FI_KEY=hyi-..."
BASE="https://freeinference.org/v1"
ports={}
try:
  for line in open("config/ports.env"):
    if "=" in line and not line.startswith("#"):
      k,v=line.strip().split("=",1)
      ports[k]=v
except: pass
GATE=int(ports.get("MCPPROXY_GO_PORT","25127"))
LOCAL=f"http://127.0.0.1:{GATE}"
print(f"=== SSOT GATEHOUSE PORT {GATE} ===")

def post(payload):
    hdr={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"}
    r=cffi.post(f"{BASE}/chat/completions",headers=hdr,json=payload,impersonate="chrome",timeout=120)
    return r

async def main():
  log=open("/tmp/fi_noslice_full.log","w", encoding="utf-8")
  def out(s):
    print(s, flush=True)
    log.write(s+"\n"); log.flush()

  out("="*80)
  out(" ULTIMATE COMBINED HARNESS (NO SLICING, MAX TOKENS=999999)")
  out("="*80)

  # xzf fix - auto detect
  for p in pathlib.Path(".").glob("mcp.tar*"):
    out(f"\n[xzf fix] {p} is_tar={tarfile.is_tarfile(p)}")
    try:
      with tarfile.open(p) as tf:
        out(f"  members count {len(tf.getmembers())}")
        tf.extractall("/tmp/mcp_fix")
        out(f"  extracted to /tmp/mcp_fix")
    except Exception as e:
      out(f"  fail {e}")

  # 1A GLM-5.3 full
  out("\n[*] 1A. GENERATING CODE: GLM-5.3 (Autoregressive)")
  t0=time.perf_counter()
  r=post({"model":"glm-5.3-flash","messages":[{"role":"user","content":"Write full FastAPI User Management API with Pydantic validation, CRUD, health"}],"max_tokens":999999,"temperature":0})
  out(f"  TIME: {(time.perf_counter()-t0):.2f}s FINISH: {r.json()['choices'][0].get('finish_reason')}")
  out(f"  --- FULL GLM CODE ---\n{r.json()['choices'][0]['message'].get('content','[EMPTY]')}\n----------------------")
  out(f"  --- FULL RAW JSON ---\n{json.dumps(r.json(),indent=2)}\n----------------------")

  # 1B Diffusion full
  out("\n[*] 1B. GENERATING CODE: DiffusionGemma (Parallel)")
  t0=time.perf_counter()
  r=post({"model":"diffusiongemma","messages":[{"role":"user","content":"Write FastAPI Item API"}],"max_tokens":999999})
  out(f"  TIME: {(time.perf_counter()-t0):.2f}s FINISH: {r.json()['choices'][0].get('finish_reason')}")
  out(f"  --- FULL DIFFUSION CODE ---\n{r.json()['choices'][0]['message'].get('content','[EMPTY]')}\n----------------------------")
  out(f"  --- FULL RAW JSON ---\n{json.dumps(r.json(),indent=2)}\n----------------------------")

  # 2 Radix 80k full
  out("\n[*] 2. RADIX CACHE TEST (80k chars)")
  big=("import os\n"*20000)+"\nCRITICAL_SECRET='X7-ALPHA'\n"+("# filler\n"*5000)
  out(f"  Sending {len(big)} characters...")
  r=post({"model":"glm-5.3-flash","messages":[{"role":"user","content":f"CODE 80k:\n{big}\nWhat is CRITICAL_SECRET?"}],"max_tokens":999999})
  out(f"  --- RAW JSON RESPONSE ---\n{json.dumps(r.json(),indent=2)}\n  -------------------------")

  # 3 Guided regex full
  out("\n[*] 3. GUIDED REGEX TEST (Raw JSON)")
  r=post({"model":"glm-5.3-flash","messages":[{"role":"user","content":"Return python def add(a,b):"}],"max_tokens":999999})
  out(f"  --- RAW JSON RESPONSE ---\n{json.dumps(r.json(),indent=2)}\n  -------------------------")

  # 4 Thought grafting full
  out("\n[*] 4. THOUGHT GRAFTING (Diffusion -> Qwen)")
  out("  [A] Harvesting DiffusionGemma's reasoning...")
  r=post({"model":"diffusiongemma","messages":[{"role":"user","content":"Design SPSC queue, think step by step"}],"max_tokens":999999,"stream":True})
  out(f"  --- FULL DIFFUSION SSE ---\n{r.text}\n-------------------------")
  harvested=r.text
  out(f"  Harvested {len(harvested)} chars")
  out("  [B] Injecting into Qwen3.6-35B...")
  r=post({"model":"qwen3.6-35b","messages":[{"role":"user","content":f"Diffusion reasoning:\n{harvested}\nNow write SPSCBuffer class push/pop/is_empty/is_full"}],"max_tokens":999999})
  out(f"  --- FULL QWEN CODE ---\n{r.json()['choices'][0]['message'].get('content','[EMPTY]')}\n-----------------------")
  out(f"  --- FULL RAW JSON ---\n{json.dumps(r.json(),indent=2)}\n-----------------------")

  # BEYOND no slice
  out("\n=== BEYOND MAXIMAL - FULL ===")
  # n=4
  r=post({"model":"glm-5.3-flash","messages":[{"role":"user","content":"def is_power_of_two(n):"}],"max_tokens":200,"n":4})
  out(f"\n[1] n=4 PARALLEL CANDIDATES FULL:\n{json.dumps(r.json(),indent=2)}")

  # tools
  tools=[{"type":"function","function":{"name":"write_file","description":"write","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}}]
  r=post({"model":"qwen3.6-35b","messages":[{"role":"user","content":"Write main.py Hello via tool"}],"max_tokens":999999,"tools":tools,"tool_choice":"auto"})
  out(f"\n[3] TOOLS FORWARDING FULL:\n{json.dumps(r.json(),indent=2)}")

  # gatehouse double full
  gatehouse_double="Thresher allows file main.py through. Log cache and allow. You are mcpproxy-go guardian for toolcall-llm."
  tools2=[{"type":"function","function":{"name":"gatehouse_allow","description":"Thresher allows file","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"},"cache_log":{"type":"string"}},"required":["path","content","cache_log"]}}}]
  r=post({"model":"qwen3.6-35b","messages":[{"role":"system","content":gatehouse_double},{"role":"user","content":"GATEHOUSE: tau agent wants main.py through. Log cache and allow."}],"max_tokens":999999,"tools":tools2,"tool_choice":"auto"})
  out(f"\n[DOUBLE GATEHOUSE TOOL] FULL:\n{json.dumps(r.json(),indent=2)}")

  # 90k full
  big90=big*2
  r=post({"model":"glm-5.3-flash","messages":[{"role":"user","content":f"CODE 80k:\n{big90}\nGATEHOUSE: log cached_tokens and reveal SECRET"}],"max_tokens":999999})
  out(f"\n[90K CONTEXT] FULL:\n{json.dumps(r.json(),indent=2)}")

  # diffusion frames full - NO SLICE
  r=post({"model":"diffusiongemma","messages":[{"role":"user","content":"Write 50 line python fastapi"}],"max_tokens":200,"stream":True})
  out(f"\n[7] DIFFUSION STREAM FRAMES {r.status_code} frames={r.text.count('data:')} FULL:\n{r.text}\n=== END ===")

  out("\n[+] Ultimate Harness Complete - full log at /tmp/fi_noslice_full.log")
  log.close()

if __name__=="__main__": asyncio.run(main())
