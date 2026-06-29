#!/usr/bin/env python3
import time
import json
import sys
import requests

url = "http://127.0.0.1:25001/v1/chat/completions"
model_name = sys.argv[1] if len(sys.argv) > 1 else "unknown"

system_prompt = """You are a polyglot codebase analyst. Your task is to classify a batch of files.
For each file in the user's input, you MUST return a classification object in a JSON array.
The JSON array MUST contain exactly the same number of elements as the number of input files.

Rings:
- core:        complete project (has package manifest, tests, and README)
- active:      substantial code, identifiable purpose, in-progress work
- experiments: single-file or tiny exploratory, POC, scratch
- utils:       helper script, tool, build artifact, config, one-purpose file
- archive:     old, ambiguous, likely duplicate, unclear provenance
- assets:      non-code: data files, media, CSVs, JSON dumps, configs, benchmark results, evaluation outputs, audit logs

Group files into "projectName" slugs. Files that implement the same feature or belong to the same repository belong in the same projectName.

Respond ONLY with a valid JSON array of objects. Do not write markdown code fences or any conversational filler.
Example output format:
[
  {
    "rel": "path/to/file.py",
    "ring": "active",
    "projectName": "project-name",
    "confidence": 0.9,
    "reason": "impl logic"
  }
]"""

user_prompt = """rel: "weight_pack_sm86_fixed.cu"
size: 1056 bytes, ext: .cu
type: full
SNIPPET:
// weight_pack_sm86_fixed.cu
// CUDA kernels optimized for sm_86 (RTX 3090) to pack quantized weights.
#include <cuda_runtime.h>
#include <device_launch_parameters.h>
#include <stdint.h>
---

rel: "turboquant_patches/ggml_turboquant.h"
size: 1400 bytes, ext: .h
type: full
SNIPPET:
#ifndef GGML_TURBOQUANT_H
#define GGML_TURBOQUANT_H
#include "ggml.h"
// Quantization layouts optimized for sm_86
---

rel: "turboquant_patches/02_ggml_turboquant_h_new.patch"
size: 2867 bytes, ext: .patch
type: full
SNIPPET:
diff --git a/ggml_turboquant.h b/ggml_turboquant.h
index a83f21..b33c09 100644
--- a/ggml_turboquant.h
+++ b/ggml_turboquant.h
@@ -12,6 +12,12 @@
---

rel: "turboquant_patches/04_llama_kv_cache_h.patch"
size: 700 bytes, ext: .patch
type: full
SNIPPET:
diff --git a/llama_kv_cache.h b/llama_kv_cache.h
---

rel: "turboquant_patches/07_issue_1205_gemma_kv_corruption.patch"
size: 3524 bytes, ext: .patch
type: full
SNIPPET:
diff --git a/src/gemma.cpp b/src/gemma.cpp
// Fix KV corruption on sliding window attention
---

rel: "turboquant_patches/test-turboquant"
size: 20944 bytes, ext: 
type: LARGE-chunked
SNIPPET:
#!/usr/bin/env bash
# Integration test runner for turboquant kernels
# Compiles CUDA test harness and runs verification suite
---"""

print(f"Querying active model (tag={model_name}) on {url}...")
t0 = time.time()
try:
    r = requests.post(
        url,
        json={
            "model": "local",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 4096
        },
        timeout=120
    )
    dt = time.time() - t0
    
    if r.status_code == 200:
        res = r.json()
        content = res["choices"][0]["message"]["content"]
        timings = res.get("timings", {})
        predicted_s = timings.get("predicted_per_second", 0)
        
        # Save to output file
        out_dir = "/home/toxic/sovereign/artifacts"
        import os
        os.makedirs(out_dir, exist_ok=True)
        out_path = f"{out_dir}/class_result_{model_name}.json"
        
        output_data = {
            "model": model_name,
            "latency_s": dt,
            "tokens_per_s": predicted_s,
            "raw_response": content
        }
        with open(out_path, "w") as f:
            json.dump(output_data, f, indent=2)
            
        print(f"SUCCESS: Result saved to {out_path}")
        print(f"Latency: {dt:.2f}s, Speed: {predicted_s:.1f} tok/s")
        print("\n--- RAW RESPONSE ---")
        print(content)
        print("--------------------")
    else:
        print(f"Error {r.status_code}: {r.text}")
except Exception as e:
    print(f"Request failed: {e}")
