# Handoff Report: Milestone 3 (Compile lucebox-hub) Investigation

## 1. Observation

We have inspected the `lucebox-hub` repository to identify all configurations and dependencies for compiling the C++ speculative-decoding server and building the Megakernel Python extension.

### A. Submodules Configuration (`.gitmodules`)

The file `/home/toxic/lucebox-hub/.gitmodules` specifies:

```ini
[submodule "dflash/deps/llama.cpp"]
	path = server/deps/llama.cpp
	url = https://github.com/Luce-Org/llama.cpp-dflash-ggml.git
	branch = luce-dflash
[submodule "dflash/deps/Block-Sparse-Attention"]
	path = server/deps/Block-Sparse-Attention
	url = https://github.com/mit-han-lab/Block-Sparse-Attention.git
```

### B. Workspace Integration and Build Isolation (`pyproject.toml`)

The root `/home/toxic/lucebox-hub/pyproject.toml` contains:

```toml
# Megakernel's CUDAExtension links against torch's C++ libs, so the build
# and runtime envs must share the same torch wheel. uv's default isolated
# build env resolves `[build-system] requires` independently of the
# project's `[tool.uv.sources]` mapping, pulling torch from PyPI instead
# of the cu128 index below. That produces an ABI-incompatible .so
# (undefined symbol `_ZNR5torch7Library4_def...` on import). Skip
# isolation here and require a two-pass install:
#   1. `uv sync`                  → populates the main venv with cu128
#                                    torch + setuptools (via dflash deps)
#   2. `uv sync --extra megakernel` → compiles setup.py against that env
no-build-isolation-package = ["qwen35-megakernel-bf16"]
```

### C. DFlash CMake Configurations (`server/CMakeLists.txt`)

We observed the following lines in `/home/toxic/lucebox-hub/server/CMakeLists.txt`:

- **GPU Backend Selection (lines 2-4):**
  ```cmake
  set(DFLASH27B_GPU_BACKEND "cuda" CACHE STRING "GPU backend to build: cuda or hip")
  set_property(CACHE DFLASH27B_GPU_BACKEND PROPERTY STRINGS cuda hip)
  string(TOLOWER "${DFLASH27B_GPU_BACKEND}" DFLASH27B_GPU_BACKEND)
  ```
- **Quantization Kernel Control (lines 96-97):**
  ```cmake
  option(DFLASH27B_FA_ALL_QUANTS "Compile ggml-cuda fattn kernels for all KV-quant pairs" ON)
  ```
- **HIP Phase 2 (lines 103-105):**
  ```cmake
  option(DFLASH27B_HIP_SM80_EQUIV
      "HIP: build the rocWMMA flashprefill kernels (Phase 2). Requires rocwmma."
      OFF)
  ```
- **Block-Sparse Attention (lines 326-328):**
  ```cmake
  if(NOT DEFINED DFLASH27B_ENABLE_BSA)
      set(DFLASH27B_ENABLE_BSA ON)
  endif()
  ```
- **Blackwell Consumer Fix (lines 152-153):**
  ```cmake
  option(DFLASH27B_USE_BLACKWELL_CONSUMER_FIX
      "Enable ggml consumer-Blackwell workaround (skip sm_12x→sm_12xa, exclude FP4 mmq kernels)" OFF)
  ```

### D. Megakernel Build System (`optimizations/megakernel/setup.py`)

We observed the following lines in `/home/toxic/lucebox-hub/optimizations/megakernel/setup.py`:

- **Architecture Detection (lines 7-20):**
  ```python
  def _detect_arch():
      arch = os.environ.get("MEGAKERNEL_CUDA_ARCH")
      if arch:
          return arch
      try:
          import torch
          if torch.cuda.is_available():
              major, minor = torch.cuda.get_device_capability()
              if major == 12 and minor in (0, 1):
                  return f"sm_{major}{minor}a"
              return f"sm_{major}{minor}"
      except Exception:
          pass
      return "sm_75"
  ```
- **Source & Gating Options (lines 69-79):**
  ```python
  if is_blackwell:
      sources.append("kernel_gb10_nvfp4.cu")
      sources.append("prefill_megakernel.cu")
      sources.append("prefill_bw.cu")
      cxx_args.append("-DMEGAKERNEL_HAS_NVFP4")
      nvcc_args.append("-DMEGAKERNEL_HAS_NVFP4")
      nvcc_args.append("-DMEGAKERNEL_HAS_PREFILL_MEGA")
      libraries.append("cublasLt")
  ```

---

## 2. Logic Chain

1. **Submodule Completeness:** The CMake build file refers to source directories inside `deps/llama.cpp/` and `deps/Block-Sparse-Attention/` (e.g. line 185 `add_subdirectory(deps/llama.cpp/ggml EXCLUDE_FROM_ALL)` and lines 525-528 target include directories under `deps/Block-Sparse-Attention`). Therefore, the submodules defined in `.gitmodules` must be initialized first.
2. **System Setup:** The `server/scripts/setup_system.sh` script installs all build tools (`cmake`, `make`, `gcc`, `git-lfs`) and the `cuda-toolkit` if not available. Running it or checking for those packages guarantees the basic toolchain is ready.
3. **Build Isolation & ABI Compatibility:** Standard `uv` installation compiles python extensions in an isolated temporary virtual environment. However, because the Megakernel utilizes PyTorch C++ bindings (`CUDAExtension` in `setup.py`), compiling it in isolation leads to downloading a PyTorch wheel from PyPI which does not match the workspace's target `cu128` wheel. This results in runtime ABI mismatch errors (e.g., `undefined symbol`).
4. **Resolution:** To prevent this, the root `pyproject.toml` lists `qwen35-megakernel-bf16` in `no-build-isolation-package`. Thus, the extension must be compiled against the _existing_ host virtual environment, necessitating a two-pass installation flow:
   - First pass (`uv sync`): Installs the host environment dependencies, including correct PyTorch (`pytorch-cu128`) and `setuptools`.
   - Second pass (`uv sync --extra megakernel`): Invokes the setup script without build isolation, using the pre-installed PyTorch headers/libs to compile the Megakernel extension.
5. **DFlash Target Compilation:** Run standard CMake configuration targeting the C++ binaries `test_dflash` and `dflash_server` within the `server` folder.

---

## 3. Caveats

- **Hardware Availability during build:** If `setup.py` runs on a machine without a GPU or active PyTorch CUDA setup, it defaults the target architecture to `sm_75`. If the target deployment GPU is different, the environment variable `MEGAKERNEL_CUDA_ARCH` (e.g. `export MEGAKERNEL_CUDA_ARCH=sm_86`) must be set explicitly before running the build.
- **AMD/HIP support for Megakernel:** The Megakernel optimization `setup.py` uses CUDA-specific options and only checks for CUDA capability. It is not currently set up for ROCm/HIP compilation. However, the C++ `server` code supports HIP.

---

## 4. Conclusion

Milestone 3 requires a specific order of execution to successfully build the project:

1. System dependency installer `server/scripts/setup_system.sh` should be run or verify that `build-essential`, `cmake`, `git`, `git-lfs`, and the `cuda-toolkit` (NVCC) are present.
2. Git submodules must be updated.
3. A two-pass virtual environment sync is mandatory to prevent PyTorch ABI mismatches for the Megakernel package.
4. C++ CMake project under `server` can be configured and built with customized compile flags (e.g., `-DDFLASH27B_ENABLE_BSA=ON`, `-DDFLASH27B_GPU_BACKEND=cuda`).

---

## 5. Verification Method

### A. Step-by-Step Command Flow

The following commands can be executed in sequence to test and compile:

```bash
# 1. System check & update submodules
git submodule update --init --recursive

# 2. Virtual environment setup (First pass)
uv sync

# 3. Compile C++ daemon
cd server
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DDFLASH27B_GPU_BACKEND=cuda
cmake --build build --target test_dflash -j$(nproc)
cmake --build build --target dflash_server -j$(nproc)
cd ..

# 4. Build Megakernel extension (Second pass)
# (Optional: set target arch if not building on deployment machine, e.g. export MEGAKERNEL_CUDA_ARCH=sm_86)
uv sync --extra megakernel
```

### B. In-Project Verification Tests

1. **Verify C++ Server & GGUF loading:**
   ```bash
   cd server/build
   ctest --output-on-failure
   ```
2. **Verify Megakernel compiled library is importable and correct:**
   ```bash
   uv run --directory optimizations/megakernel python bench_pp_tg.py
   ```
   _(This script tests the correctness of the megakernel output against a reference decode path)._
