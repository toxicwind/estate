# Milestone 3 Analysis: Compile lucebox-hub

This document provides a detailed technical analysis of the build system and compilation requirements for **lucebox-hub** (specifically the C++ DFlash daemon and the Megakernel Python extension), as part of Milestone 3.

---

## 1. DFlash Optimization Compile Options and Definitions

The C++ server compilation is managed via `server/CMakeLists.txt`. It supports both NVIDIA CUDA and AMD HIP backends, driving speculative-decoding and flash-prefill optimizations.

### CMake Build Options (Cache Variables)
The following options can be set via `-D<OPTION>=<VALUE>` during CMake configuration:

| Option | Type/Allowed Values | Default | Description |
| :--- | :--- | :--- | :--- |
| `DFLASH27B_GPU_BACKEND` | `cuda` / `hip` | `cuda` | GPU backend target. |
| `DFLASH27B_USER_CUDA_ARCHITECTURES` | List (e.g. `86;120`) | `""` (empty) | Overrides target CUDA architectures (e.g., `CMAKE_CUDA_ARCHITECTURES`). If empty, CMake will auto-detect/set defaults (`60;61;62;70;75;86` and dynamically append `110`, `120`, or `121` based on `nvcc` version). |
| `DFLASH27B_HIP_ARCHITECTURES` | List | `""` | Custom HIP GPU targets (e.g. `gfx906;gfx1100`). Defaults to `gfx1151` (Strix Halo) if unspecified. |
| `DFLASH27B_FA_ALL_QUANTS` | `BOOL` | `ON` | Compiles Flash Attention (fattn) kernels for all KV-quantization pairs. Turning this off reduces C++ compilation time by ~3x but restricts kv-quantization flexibility. |
| `DFLASH27B_HIP_SM80_EQUIV` | `BOOL` | `OFF` | Enables Phase 2 rocWMMA flashprefill kernels for HIP builds. Requires `rocwmma/rocwmma.hpp` headers. |
| `DFLASH27B_USE_BLACKWELL_CONSUMER_FIX`| `BOOL` | `OFF` | Skip `sm_12x` -> `sm_12xa` replacement and exclude FP4 mmq kernels to avoid illegal-instruction faults on consumer Blackwell chips. Auto-enabled if any `12x` arch is in the CUDA architectures list. |
| `DFLASH27B_ENABLE_BSA` | `BOOL` | `ON` | Enable Block-Sparse Attention for speculative-prefill. CUDA requires compute capability `sm_80+` (Ampere+) and the `Block-Sparse-Attention` submodule. HIP requires `DFLASH27B_HIP_SM80_EQUIV=ON`. |
| `DFLASH27B_TESTS` | `BOOL` | `ON` | Build the C++ numerics and regression tests. |
| `DFLASH27B_SERVER` | `BOOL` | `ON` | Build the `dflash_server` binary and the `backend_ipc_daemon`. |

### Key Compile Definitions
The build configuration defines several compile-time flags inside `server/CMakeLists.txt`:
* **Backend:** `DFLASH27B_BACKEND_CUDA=1` or `DFLASH27B_BACKEND_HIP=1`
* **GPU Architecture Capabilities:** `DFLASH27B_CUDA_MIN_SM=<Capability>` and `DFLASH27B_MIN_SM=<Capability>` (extracted from the first item in the CUDA architectures list).
* **Workarounds:** `GGML_CUDA_BLACKWELL_CONSUMER=ON` when the consumer Blackwell fix is active.
* **Prefill Kernels:**
  * CUDA:
    * `DFLAVE27B_HAVE_CUDA_WMMA_FLASHPREFILL=1`
    * `DFLASH27B_HAVE_SM80_FLASHPREFILL=1` (requires SM >= 80, compiles `src/flashprefill_kernels.cu`)
    * `DFLASH27B_HAVE_VOLTA_FLASHPREFILL=1` (requires Volta/Turing SM 70/75, compiles `src/flashprefill_f16.cu`)
    * `DFLASH27B_HAVE_CUDA_SCALAR_FLASHPREFILL=1` / `DFLASH27B_HAVE_PASCAL_FLASHPREFILL=1` (compiles `src/flashprefill_scalar.cu` for Pascal SM 60-69)
  * HIP:
    * `DFLASH27B_HAVE_FLASHPREFILL=1` when `DFLASH27B_HIP_SM80_EQUIV` is enabled (compiles `src/flashprefill_kernels.hip.cu`).
* **Block-Sparse Attention (BSA):**
  * `DFLASH27B_HAVE_BSA=1`
  * `FLASHATTENTION_DISABLE_DROPOUT`
  * `FLASH_NAMESPACE=flash`

---

## 2. Megakernel (Ampere TMA Emulation) Optimization Build

The Megakernel fuses all 24 layers of the Qwen 3.5-0.8B hybrid DeltaNet/Attention model forward pass into a single persistent CUDA dispatch. It is implemented in `optimizations/megakernel/`.

### Setup Script Configuration (`setup.py`)
The C++ extension `qwen35_megakernel_bf16_C` is compiled using `setuptools` and PyTorch's `CUDAExtension` utility:
* **CUDA Architecture Resolution:**
  * Checks the `MEGAKERNEL_CUDA_ARCH` environment variable.
  * Fallback: Auto-detects the host GPU using `torch.cuda.get_device_capability()`. If SM 12.0 or 12.1 is detected (Blackwell), it returns `sm_120a` or `sm_121a`.
  * Ultimate Fallback: Default to `sm_75` (Turing).
* **Compile-time Variables (Controlled via Environment Variables):**
  * `MEGAKERNEL_NUM_BLOCKS` (default: 28 for Pascal SM 60-69, 82 otherwise).
  * `MEGAKERNEL_BLOCK_SIZE` (default: 512).
  * `MEGAKERNEL_LM_NUM_BLOCKS` (default: 256 for Pascal, 512 otherwise).
  * `MEGAKERNEL_LM_BLOCK_SIZE` (default: 256).
  * `MEGAKERNEL_DN_PHASE2_WMMA` (default: 0).
* **Blackwell NVFP4 Optimization:**
  * If the detected/specified architecture begins with `sm_12` (Blackwell):
    * Compiles additional sources: `kernel_gb10_nvfp4.cu`, `prefill_megakernel.cu`, and `prefill_bw.cu`.
    * Links against `cublasLt` in addition to `cublas`.
    * Passes `-DMEGAKERNEL_HAS_NVFP4` and `-DMEGAKERNEL_HAS_PREFILL_MEGA` to NVCC.
* **Host Compiler Flags:** `-O3`, `-std=c++17`, and fast math flags are applied.

### Workspace Integration and Build Isolation
* **Build System Requirements:** The package `qwen35-megakernel-bf16` specifies `requires = ["setuptools>=68", "wheel", "torch"]` in its local `pyproject.toml`.
* **The Build Isolation Challenge:** Because `setup.py` imports `torch` at build time to configure the extension, standard isolated pip/uv builds will attempt to pull PyTorch from PyPI. This can result in downloading a generic PyPI CPU/CUDA wheel instead of the specific `cu128` wheel mapped in the workspace root, leading to ABI incompatibilities (specifically `undefined symbol` runtime errors upon importing the compiled extension).
* **Workspace Resolution:** The root `pyproject.toml` explicitly skips build isolation for the Megakernel package via:
  ```toml
  no-build-isolation-package = ["qwen35-megakernel-bf16"]
  ```
  This mandates a **two-pass installation**:
  1. Synchronize the primary virtual environment with standard dependencies (populating PyTorch `cu128` and `setuptools`).
  2. Build/sync the workspace with the `--extra megakernel` flag, allowing `setup.py` to compile against the pre-installed host environment's PyTorch.

---

## 3. Submodules and Dependencies

To successfully build the server and optimizations, several external assets and submodules must be present:

### Submodules (`.gitmodules`)
Before running any compile command, you must initialize the following submodules:
1. `server/deps/llama.cpp`
   * **Source URL:** `https://github.com/Luce-Org/llama.cpp-dflash-ggml.git` (Private/custom fork, branch: `luce-dflash`)
   * **Role:** Provides the underlying GGML inference backend wrapper.
2. `server/deps/Block-Sparse-Attention`
   * **Source URL:** `https://github.com/mit-han-lab/Block-Sparse-Attention.git`
   * **Role:** Fused Block-Sparse-Attention CUDA kernels.

### System-level External Dependencies
* **CUDA Toolkit / NVCC:** Compiler (such as NVCC 12+) and `libcudart` are required.
* **CURL:** Required to enable the passthrough proxy in `dflash_server`.
* **OpenMP:** CXX bindings/libraries are utilized to optimize parallel CPU operations.
* **nlohmann_json:** Header-only JSON library. CMake will try to find it locally; if unavailable, it downloads version `3.11.3` via `FetchContent`.
* **rocwmma:** (AMD HIP Phase 2 builds only) Requires `rocwmma` package installed (e.g. `sudo apt install rocwmma` or headers from github).

---

## 4. Proposed Implementation and Compilation Strategy

To build the C++ `dflash` daemon and compile the Megakernel Python extension, the implementation agent should follow this step-by-step strategy.

### Step 1: Install System Dependencies
Ensure target build tools are present. Run (as root/sudo) the system configuration script:
```bash
sudo bash server/scripts/setup_system.sh
```
If CUDA was newly installed, export NVCC path:
```bash
export PATH=/usr/local/cuda/bin:$PATH
```

### Step 2: Initialize Submodules
From the repository root:
```bash
git submodule update --init --recursive
```

### Step 3: Synchronize Virtual Environment (First Pass)
Initialize a virtual environment using `uv` and pull in the baseline dependencies (including the specific PyTorch GPU wheel and `setuptools`):
```bash
uv sync
```
This installs the required PyTorch `cu128` build dependency into the local `.venv`.

### Step 4: Build the C++ Server Daemon
Configure the CMake build and compile the speculative-decoding server:
```bash
cd server
cmake -B build -S . \
    -DCMAKE_BUILD_TYPE=Release \
    -DDFLASH27B_GPU_BACKEND=cuda \
    -DDFLASH27B_ENABLE_BSA=ON
cmake --build build --target test_dflash -j$(nproc)
cmake --build build --target dflash_server -j$(nproc)
```
*(The compiled binaries will sit under `server/build/`)*.

### Step 5: Build the Megakernel Python Extension (Second Pass)
Since build isolation is disabled for the megakernel package in `pyproject.toml`, run the workspace synchronization with the `megakernel` extra to compile the extension against the active virtual environment:
```bash
cd ..
uv sync --extra megakernel
```
*(Optionally, one can manually configure `MEGAKERNEL_CUDA_ARCH` to match the target device capability, e.g. `export MEGAKERNEL_CUDA_ARCH=sm_86` or let setup.py auto-detect the GPU capability)*.

### Step 6: Verify Compilations
1. Run C++ unit/numerics tests:
   ```bash
   cd server/build
   ctest --output-on-failure
   ```
2. Verify Megakernel build and correctness:
   ```bash
   cd ../../
   uv run --directory optimizations/megakernel python bench_pp_tg.py
   ```
