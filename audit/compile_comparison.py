#!/usr/bin/env python3
import json
import os

out_dir = "/home/toxic/sovereign/artifacts"
models = ["exaone-1.2b", "strangemerges-19-7b", "gemma-4-12b"]

comparison_md = """# Model Comparison Report: File Analysis Task

We evaluated the performance of three local models on the same file analysis and classification batch task.

## Key Metrics Comparison

| Model | Size | Latency | Speed | Format Output | Path Integrity |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""

for model in models:
    path = f"{out_dir}/class_result_{model}.json"
    if not os.path.exists(path):
        comparison_md += f"| {model} | N/A | N/A | N/A | Missing | Missing |\n"
        continue
        
    with open(path) as f:
        data = json.load(f)
        
    raw = data["raw_response"]
    
    # Parse format check
    is_json = "No"
    try:
        parsed = json.loads(raw.strip().replace("<|im_end|>", "").strip())
        if isinstance(parsed, list):
            is_json = "Yes (Clean JSON Array)"
    except Exception:
        if raw.strip().startswith("[") and ("\n  {" in raw or "rel" in raw):
            is_json = "Yes (Partial/Truncated)"
        else:
            is_json = "No (Conversational Text)"
            
    # Check path integrity
    path_int = "N/A"
    if is_json != "No":
        try:
            # Simple check
            clean_raw = raw.replace("<|im_end|>", "").strip()
            # If truncated, close brackets to parse
            if clean_raw.endswith('"') or clean_raw.endswith('}'):
                if not clean_raw.endswith(']'):
                    if clean_raw.endswith('}'):
                        clean_raw += ']'
                    else:
                        clean_raw += '"} ]'
            parsed = json.loads(clean_raw)
            original_paths = [
                "weight_pack_sm86_fixed.cu",
                "turboquant_patches/ggml_turboquant.h",
                "turboquant_patches/02_ggml_turboquant_h_new.patch",
                "turboquant_patches/04_llama_kv_cache_h.patch",
                "turboquant_patches/07_issue_1205_gemma_kv_corruption.patch",
                "turboquant_patches/test-turboquant"
            ]
            matched = 0
            for item in parsed:
                if item.get("rel") in original_paths:
                    matched += 1
            path_int = f"{matched}/{len(original_paths)} matched"
        except Exception as e:
            path_int = "Failed to parse paths"
            
    comparison_md += f"| **{model}** | {'1.2B' if '1.2b' in model else '7B' if '7b' in model else '12B'} | {data['latency_s']:.2f}s | {data['tokens_per_s']:.1f} tok/s | {is_json} | {path_int} |\n"

comparison_md += """
## Detailed Findings

### 1. LGAI-EXAONE-4.0-1.2B-Instruct
* **Strengths**: Blazing fast (`375+ tokens/second`). Prompt evaluation took only `4ms` when cached.
* **Weaknesses**: Failed the strict formatting instructions. Instead of outputting a JSON array, it returned a conversational markdown list explaining the files.

### 2. StrangeMerges_19-7B-dare_ties
* **Strengths**: Fast (`139 tokens/second`), followed instructions perfectly, and outputted a clean JSON array with 100% path integrity preserved.
* **Weaknesses**: Its reasoning and classification capabilities are average (classified patches as `experiments` which makes sense, but misses deeper project linkages).

### 3. Gemma-4-12B-it-uncensored
* **Strengths**: Highly precise, excellent classification quality (correctly identified the `turboquant` project relationship across files).
* **Weaknesses**: Slower generation speed (`63 tokens/second`), and due to its internal hidden reasoning loop, it generates a large chain of thoughts, requiring a higher token budget and time to complete.
"""

with open(f"{out_dir}/model_comparison_report.md", "w") as f:
    f.write(comparison_md)

print("SUCCESS: Comparison report saved.")
print(comparison_md)
