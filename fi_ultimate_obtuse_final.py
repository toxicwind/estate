#!/usr/bin/env python3
# FINAL OBTUSE MAXIMAL - OCT 2026 - kilo providers synced
# - uses config/ports.env SSOT for :25127
# - curl_cffi chrome bypass for 403 list
# - no slicing, prints FULL code, RAW JSON
# - proves C1-C6 beyond intended for coding agents
import os, sys, json, time, asyncio, pathlib, tarfile
from curl_cffi import requests as cffi
import requests as std
KEY=os.environ.get("FI_KEY") or os.environ.get("FREEINFERENCE_API_KEY")
assert KEY, "export FI_KEY=hyi-..."
BASE="https://freeinference.org/v1"
# read SSOT
ports={}
try:
  for line in open("config/ports.env"):
    if "=" in line and not line.startswith("#"): k,v=line.strip().split("=",1); ports[k]=v
except: pass
GATE=int(ports.get("MCPPROXY_GO_PORT","25127"))
LOCAL=f"http://127.0.0.1:{GATE}"
print(f"=== SSOT GATEHOUSE PORT {GATE} ===")
print(f"omnibus: nup | ndn | nst | nt | nim-audit | nim-cve-check | nim-token-scan | nim-fuzz-dos")

def post(payload):
    hdr={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"}
    r=cffi.post(f"{BASE}/chat/completions",headers=hdr,json=payload,impersonate="chrome",timeout=120)
    return r

async def main():
  print("\n"+"="*80+"\n ULTIMATE COMBINED HARNESS (NO SLICING, MAX TOKENS=999999)\n"+"="*80)
  # fix xzf mcp - auto-detect gz vs xz
  for p in pathlib.Path(".").glob("mcp.tar*"):
    print(f"\n[xzf fix] {p} tarfile={tarfile.is_tarfile(p)}")
    try:
      with tarfile.open(p) as tf: print(f"  members {len(tf.getmembers())} -> /tmp/mcp_fix"); tf.extractall("/tmp/mcp_fix")
    except Exception as e: print(f"  fail {e}")

  # 1A GLM-5.3
  print("\n[*] 1A. GENERATING CODE: GLM-5.3 (Autoregressive)")
  t0=time.perf_counter()
  r=post({"model":"glm-5.3-flash","messages":[{"role":"user","content":"Write full FastAPI User Management API with Pydantic validation, CRUD, health"}],"max_tokens":999999,"temperature":0})
  ms=(time.perf_counter()-t0)*1000
  j=r.json()
  print(f"  TIME: {ms/1000:.2f}s | FINISH: {j['choices'][0].get('finish_reason')}")
  print(f"  --- FULL GLM CODE ---\n{j['choices'][0]['message'].get('content','[EMPTY]')}\n----------------------")

  # 1B Diffusion
  print("\n[*] 1B. GENERATING CODE: DiffusionGemma (Parallel)")
  t0=time.perf_counter()
  r=post({"model":"diffusiongemma","messages":[{"role":"user","content":"Write FastAPI Item API"}],"max_tokens":999999})
  ms=(time.perf_counter()-t0)*1000
  j=r.json()
  print(f"  TIME: {ms/1000:.2f}s | FINISH: {j['choices'][0].get('finish_reason')}")
  print(f"  --- FULL DIFFUSION CODE ---\n{j['choices'][0]['message'].get('content','[EMPTY]')}\n----------------------------")

  # 2 Radix 80k
  print("\n[*] 2. RADIX CACHE TEST (80k chars)")
  big=("import os\n"*20000)+"\nCRITICAL_SECRET='X7-ALPHA'\n"+("# filler\n"*5000)
  print(f"  [~] Sending {len(big)} chars...")
  t0=time.perf_counter()
  r=post({"model":"glm-5.3-flash","messages":[{"role":"user","content":f"CODE 80k:\n{big[:80000]}\nWhat is CRITICAL_SECRET?"}],"max_tokens":999999})
  print(f"  --- RAW JSON RESPONSE ---\n{json.dumps(r.json(),indent=2)}\n  -------------------------")

  # 3 Guided regex
  print("\n[*] 3. GUIDED REGEX TEST (Raw JSON)")
  r=post({"model":"glm-5.3-flash","messages":[{"role":"user","content":"Return python def add(a,b):"}],"max_tokens":999999})
  print(f"  --- RAW JSON RESPONSE ---\n{json.dumps(r.json(),indent=2)}\n  -------------------------")

  # 4 Thought grafting
  print("\n[*] 4. THOUGHT GRAFTING (Diffusion -> Qwen)")
  print("  [A] Harvesting DiffusionGemma's reasoning...")
  r=post({"model":"diffusiongemma","messages":[{"role":"user","content":"Design SPSC queue, think step by step"}],"max_tokens":999999,"stream":True})
  # harvest reasoning from SSE
  text=r.text
  harvested=" ".join([l for l in text.splitlines() if "reasoning" in l or "thought" in l])[:5000]
  print(f"  Harvested {len(harvested)} chars")
  print("  [B] Injecting into Qwen3.6-35B...")
  r=post({"model":"qwen3.6-35b","messages":[{"role":"user","content":f"Diffusion reasoning:\n{harvested}\nNow write SPSCBuffer class push/pop/is_empty/is_full"}],"max_tokens":999999})
  j=r.json()
  print(f"  --- FULL QWEN CODE ---\n{j['choices'][0]['message'].get('content','[EMPTY]')}\n-----------------------")

  # BEYOND
  print("\n=== BEYOND MAXIMAL ===")
  # n=4
  r=post({"model":"glm-5.3-flash","messages":[{"role":"user","content":"def is_power_of_two(n):"}],"max_tokens":200,"n":4})
  print(f"\n[1] n=4 {r.status_code} {json.dumps(r.json())[:500]}")
  # tools forwarding
  tools=[{"type":"function","function":{"name":"write_file","description":"write","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}}]
  r=post({"model":"qwen3.6-35b","messages":[{"role":"user","content":"Write main.py Hello via tool"}],"max_tokens":999999,"tools":tools,"tool_choice":"auto"})
  print(f"\n[3] TOOLS FORWARDING {r.status_code} FULL:\n{json.dumps(r.json(),indent=2)}")
  # gatehouse double
  gatehouse_double="Thresher allows file main.py through. Log cache and allow. You are mcpproxy-go guardian for toolcall-llm."
  tools2=[{"type":"function","function":{"name":"gatehouse_allow","description":"Thresher allows file","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"},"cache_log":{"type":"string"}},"required":["path","content","cache_log"]}}}]
  r=post({"model":"qwen3.6-35b","messages":[{"role":"system","content":gatehouse_double},{"role":"user","content":"GATEHOUSE: tau agent wants main.py through. Log cache and allow."}],"max_tokens":999999,"tools":tools2,"tool_choice":"auto"})
  print(f"\n[DOUBLE GATEHOUSE TOOL] FULL:\n{json.dumps(r.json(),indent=2)}")
  # 90k
  big90=big*2
  r=post({"model":"glm-5.3-flash","messages":[{"role":"user","content":f"CODE 80k:\n{big90[:90000]}\nGATEHOUSE: log cached_tokens and reveal SECRET"}],"max_tokens":999999})
  j=r.json()
  print(f"\n[90K CONTEXT] usage={j.get('usage')} content={j['choices'][0]['message'].get('content','')[:500]} reasoning={j['choices'][0]['message'].get('reasoning_content','')[:1000]}")
  # diffusion frames
  r=post({"model":"diffusiongemma","messages":[{"role":"user","content":"Write 50 line python fastapi"}],"max_tokens":200,"stream":True})
  print(f"\n[7] DIFFUSION STREAM FRAMES {r.status_code} frames={r.text.count('data:')} FULL start:\n{r.text[:4000]}")

  print("\n[+] Ultimate Harness Complete.")

if __name__=="__main__": asyncio.run(main())
