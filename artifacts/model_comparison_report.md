# Model Comparison Report: File Analysis Task

We evaluated the performance of three local models on the same file analysis and classification batch task.

## Key Metrics Comparison

| Model | Size | Latency | Speed | Format Output | Path Integrity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **exaone-1.2b** | 1.2B | 1.24s | 375.0 tok/s | No (Conversational Text) | Failed to parse paths |
| **strangemerges-19-7b** | 7B | 3.96s | 139.1 tok/s | Yes (Clean JSON Array) | 6/6 matched |
| **gemma-4-12b** | 12B | 23.24s | 63.1 tok/s | Yes (Clean JSON Array) | 6/6 matched |

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
