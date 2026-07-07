# Milestone 3 Analysis Report: Lucebox-Hub Compilation & Optimization Enablement

This report details the compilation and optimization enablement strategy for compiling the `lucebox-hub` C++ server (DFlash) and building the Megakernel (Ampere TMA Emulation) Python extension.

---

## 1. DFlash Optimization Compile Settings

In `server/CMakeLists.txt`, several CMake options and compile definitions control the **DFlash** speculative decoding and speculative prefill optimizations. Below is a structured summary of these settings:

### 1.1 CMake Variables and Defaults

| CMake Variable                         | Default Value           | Purpose / Impact                                                                                                                                                                                      |
| :------------------------------------- | :---------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DFLASH27B_GPU_BACKEND`                | `"cuda"`                | Target GPU backend. Supported values: `cuda` or `hip` (case-insensitive).                                                                                                                             |
| `DFLASH27B_USER_CUDA_ARCHITECTURES`    | `""` (nvcc auto-detect) | Semicolon-separated list of target CUDA compute architectures (e.g. `"86"`). Overrides the default list (`"60;61;62;70;75;86;120"`).                                                                  |
| `DFLASH27B_HIP_ARCHITECTURES`          | `""`                    | Target HIP GPU architectures (e.g. `"gfx1151;gfx1100"`).                                                                                                                                              |
| `DFLASH27B_FA_ALL_QUANTS`              | `ON`                    | Compiles ggml-cuda/hip FlashAttention kernels for all KV-quantization pairs (required for asymmetric KV cache). Increases compile time by ~3×.                                                        |
| `DFLASH27B_ENABLE_BSA`                 | `ON` (auto-gates)       | Enables Block-Sparse Attention (BSA) for speculative prefill scoring. Gated by GPU architecture (`sm_80+` for CUDA) and submodule initialization.                                                     |
| `DFLASH27B_HIP_SM80_EQUIV`             | `OFF`                   | Gated on HIP builds. If `ON`, compiles rocWMMA-native flashprefill kernels (Phase 2). Requires `rocwmma/rocwmma.hpp` headers in `ROCM_PATH`.                                                          |
| `DFLASH27B_USE_BLACKWELL_CONSUMER_FIX` | `OFF`                   | Bypasses Blackwell `sm_12x -> sm_12xa` instruction changes and excludes FP4 kernels to prevent illegal instruction faults on consumer chips. Auto-enables if target CUDA arch includes a `12x` entry. |
| `DFLASH27B_TESTS`                      | `ON`                    | Builds C++ numerics and smoke tests.                                                                                                                                                                  |
| `DFLASH27B_SERVER`                     | `ON`                    | Builds `dflash_server` and `backend_ipc_daemon`.                                                                                                                                                      |

### 1.2 Required & Available Compile Definitions

Depending on the configuration, `server/CMakeLists.txt` defines several compile-time definitions passed to NVCC or the C++ compiler:

- **GPU Backend Identification**:
  - `DFLASH27B_BACKEND_CUDA=1` (for CUDA backend builds)
  - `DFLASH27B_BACKEND_HIP=1` and `GGML_USE_HIP` (for HIP backend builds)
- **Minimum Compute Capabilities**:
  - `DFLASH27B_CUDA_MIN_SM=<sm>` and `DFLASH27B_MIN_SM=<sm>` (e.g. `86` for RTX 3090, extracted from target architecture list).
- **BSA (Block-Sparse Attention)**:
  - `DFLASH27B_HAVE_BSA=1` (when `DFLASH27B_ENABLE_BSA` is resolved to `ON`). Passes additional definitions to cutlass kernels: `FLASHATTENTION_DISABLE_DROPOUT`, `FLASH_NAMESPACE=flash`.
- **FlashPrefill Kernels**:
  - `DFLASH27B_HAVE_FLASHPREFILL=1` (defined for HIP builds with `DFLASH27B_HIP_SM80_EQUIV=ON`).
  - `DFLASH27B_HAVE_CUDA_WMMA_FLASHPREFILL=1` + `DFLASH27B_HAVE_SM80_FLASHPREFILL=1` (for CUDA `sm_80+` builds).
  - `DFLASH27B_HAVE_CUDA_WMMA_FLASHPREFILL=1` + `DFLASH27B_HAVE_VOLTA_FLASHPREFILL=1` (for CUDA `sm_70` to `sm_79` builds).
  - `DFLASH27B_HAVE_CUDA_SCALAR_FLASHPREFILL=1` + `DFLASH27B_HAVE_PASCAL_FLASHPREFILL=1` (for CUDA `sm_60` to `sm_69` builds).
- **Curl Support**:
  - `DFLASH_HAS_CURL=1` (when `libcurl` is found on the system).

---

## 2. Megakernel Optimization Build System

The Megakernel optimization fuses all 24 layers of the Qwen 3.5-0.8B hybrid DeltaNet/Attention model into a single CUDA dispatch. It lives in `optimizations/megakernel`.

### 2.1 Build System Analysis (`pyproject.toml` & `setup.py`)

- **Dependency and ABI Requirements**:
  - The Megakernel uses `torch.utils.cpp_extension.CUDAExtension` to compile C++/CUDA code and link it against PyTorch’s C++ libraries (`libtorch`).
  - Because it links against PyTorch, it is critical that the build environment and runtime environment use the exact same PyTorch wheel. An ABI mismatch will cause an import failure (e.g. undefined symbol `_ZNR5torch7Library4_def...`).
  - Therefore, the root `pyproject.toml` specifies `no-build-isolation-package = ["qwen35-megakernel-bf16"]`. Build isolation must be disabled during the build so `setup.py` sees the Torch wheel installed in the main `.venv` (sourced from the custom `pytorch-cu128` index).
- **Target Architecture Auto-detection (`_detect_arch` in `setup.py`)**:
  - Checks the environment variable `MEGAKERNEL_CUDA_ARCH` first.
  - If not set, it imports `torch` and calls `torch.cuda.get_device_capability()`. For Blackwell (`sm_12x`), it appends `a` (e.g., `sm_120a`). Otherwise, it resolves to `sm_{major}{minor}` (e.g. `sm_86` for the RTX 3090).
  - If Torch or CUDA is unavailable, it defaults to `sm_75`.
- **Environment Overrides for Tuning**:
  - `MEGAKERNEL_CUDA_ARCH`: Forces target CUDA architecture (e.g. `sm_86`).
  - `MEGAKERNEL_NUM_BLOCKS`: Grid size for block persistent execution (default `82` for non-Pascal, `28` for Pascal).
  - `MEGAKERNEL_BLOCK_SIZE`: CUDA thread block size (default `512`).
  - `MEGAKERNEL_LM_NUM_BLOCKS`: Number of blocks for the language model head (default `512` for non-Pascal, `256` for Pascal).
  - `MEGAKERNEL_LM_BLOCK_SIZE`: LM thread block size (default `256`).
  - `MEGAKERNEL_DN_PHASE2_WMMA`: Binary flag for DeltaNet Phase 2 Tensor Core WMMA usage (default `0`).
- **Blackwell-Specific Codepaths**:
  - If Blackwell (`sm_120`/`sm_121a`) is detected, it compiles extra sources (`kernel_gb10_nvfp4.cu`, `prefill_megakernel.cu`, `prefill_bw.cu`), adds `cublasLt` library, and sets `-DMEGAKERNEL_HAS_NVFP4` and `-DMEGAKERNEL_HAS_PREFILL_MEGA`.

---

## 3. Submodule & External Dependencies

Before starting compilation, all submodules and system libraries must be present.

### 3.1 Submodules (`.gitmodules` / `server/deps/`)

1. **llama.cpp Submodule**:
   - Location: `server/deps/llama.cpp`
   - URL: `https://github.com/Luce-Org/llama.cpp-dflash-ggml.git` (branch: `luce-dflash`)
   - Purpose: Supplies the underlying `ggml` inference library.
2. **Block-Sparse-Attention Submodule**:
   - Location: `server/deps/Block-Sparse-Attention`
   - URL: `https://github.com/mit-han-lab/Block-Sparse-Attention.git`
   - Purpose: Supplies the Cutlass block-sparse attention kernels required to build `DFLASH27B_ENABLE_BSA=ON`.

### 3.2 External Dependencies (Host Toolchain)

The host system has the following toolchain versions installed:

- **CMake**: `4.3.4` (requires minimum `3.21` for first-class HIP support, or `3.18` for CUDA)
- **G++**: `16.1.1` (requires minimum GCC `11` C++17)
- **NVCC**: CUDA Toolkit `13.3.33` (requires minimum `12.0+` for DFlash/Megakernel)
- **uv**: `0.11.21` (Python dependency management)
- **Python**: `3.14.5` (default). Since the project specifies Python `>=3.12,<3.13`, `uv` will automatically read `/home/toxic/lucebox-hub/.python-version` containing `3.12` and download a standalone Python 3.12 interpreter.

_Optional System Packages for full server support_:

- `libcurl4-openssl-dev` / `curl` (for proxy routing in `dflash_server`).
- `libgomp1` (OpenMP runtime library for multi-threaded CPU kernels).

### 3.3 Weights and Model Dependencies

For runtime testing and integration testing, weights are retrieved from Hugging Face:

- Target Model: `unsloth/Qwen3.6-27B-GGUF` (specifically `Qwen3.6-27B-Q4_K_M.gguf`).
- Draft Model: `Lucebox/Qwen3.6-27B-DFlash-GGUF` (specifically `dflash-draft-3.6-q4_k_m.gguf`).
- Megakernel Model: `Qwen/Qwen3.5-0.8B` (Auto-downloaded by transformers via Hugging Face Hub during `final_bench.py` execution).
  _(Note: Since network access is disabled under CODE_ONLY mode, the implementation agent will need to verify whether local cache files or Hugging Face Hub offline modes are required, or configure local symlinks for offline execution)._

---

## 4. Step-by-Step Compilation & Build Strategy

Below is the concrete, step-by-step strategy for the implementation agent to compile the C++ server and build the Megakernel Python extension on the target host (GeForce RTX 3090, `sm_86`).

### Step 1: Initialize Git Submodules

Ensure submodules are fully checked out before running CMake:

```bash
git submodule update --init --recursive
```

### Step 2: Configure & Compile C++ server

Configure CMake using the specific `sm_86` CUDA architecture matching the host's GeForce RTX 3090. This cuts NVCC compilation time by 5-6× compared to building the default multi-arch fatbinary.

```bash
# Clean previous build artifacts if any exist
rm -rf server/build

# Configure with CMake, explicitly targeting Ampere sm_86
cmake -S server -B server/build \
      -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DDFLASH27B_USER_CUDA_ARCHITECTURES="86" \
      -DCMAKE_CUDA_ARCHITECTURES="86"

# Build all target binaries (server, daemon, unit tests)
cmake --build server/build --target dflash_server test_dflash test_server_unit -j
```

_Expected Outputs_:

- `server/build/dflash_server`
- `server/build/test_dflash`
- `server/build/test_server_unit`

### Step 3: Populate Base Python Environment (`uv sync`)

Run a two-pass `uv` synchronization. The first pass populates the main virtual environment with PyTorch from the `pytorch-cu128` index:

```bash
# Sinks deps (dflash & pflash) and downloads Python 3.12 if not cached
uv sync
```

### Step 4: Compile Megakernel CUDA Extension

Now, compile the Megakernel python package using the main environment's libraries (build isolation is skipped for this package):

```bash
# Compile and install the Megakernel CUDA Extension
uv sync --extra megakernel
```

_Verification_: Check that the C extension compiles successfully and can be imported under Python 3.12:

```bash
uv run python -c "import qwen35_megakernel_bf16_C; print('Import Succeeded!')"
```

---

## 5. Verification Plan

The implementation agent can verify the builds using the following commands:

### 5.1 C++ Server Verification

Run the server unit tests using ctest:

```bash
cd server/build
ctest --output-on-failure
```

Or run the custom `check` target directly:

```bash
cmake --build server/build --target check
```

### 5.2 Megakernel Verification

Run the quick correctness test script (compares megakernel output parity against PyTorch reference):

```bash
uv run --directory optimizations/megakernel python bench_pp_tg.py
```

Run the performance benchmark (after verifying correctness):

```bash
uv run --directory optimizations/megakernel python final_bench.py
```

_(Note: Because these tests download Qwen3.5-0.8B weights/tokenizer from Hugging Face Hub, they might fail in offline CODE_ONLY environments unless the model cache is prepopulated or `--local-files-only` is set. The agent should ensure that any model download steps are performed or stubbed before verifying)._
