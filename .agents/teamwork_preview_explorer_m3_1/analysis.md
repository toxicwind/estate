# Milestone 3 Compilation and Build Analysis — `lucebox-hub`

This report provides a read-only analysis of the C++ server and Megakernel Python extension compilation requirements in `/home/toxic/lucebox-hub` for the implementation agent.

---

## 1. DFlash Optimization Compile Options (`server/CMakeLists.txt`)

The C++ speculative decoding server is configured using CMake (`server/CMakeLists.txt`). The following options and definitions configure and enable the DFlash optimizations:

### Core Configuration Options

- **`DFLASH27B_GPU_BACKEND`**: (Default: `cuda`, Option strings: `cuda`, `hip`)
  - Controls the GPU target backend. For the NVIDIA RTX 3090 on the host, this must be set to `cuda`. Setting it to `hip` targets AMD ROCm/HIP.
- **`CMAKE_CUDA_ARCHITECTURES`**: (Default: `"60;61;62;70;75;86"`)
  - Defines target GPU compute architectures. For the target RTX 3090 (`sm_86`), compiling all defaults takes excessive time. Specifying `-DCMAKE_CUDA_ARCHITECTURES=86` restricts compilation to Ampere, speeding up compilation significantly.
- **`DFLASH27B_FA_ALL_QUANTS`**: (Default: `ON`)
  - Compiles `ggml-cuda` Flash Attention kernels for all KV-quantization pairs. Compiling all pairs grows build time by approximately 3×. To speed up the implementation build during testing, this option can be set to `OFF` (which only enables standard quantization pairs for `spec_prefill` demo runs).
- **`DFLASH27B_ENABLE_BSA`**: (Default: `ON`)
  - Enables Block-Sparse Attention (BSA) kernels. These kernels accelerate speculative prefill scoring.
  - **Constraints**:
    1. Requires CUDA architecture SM level `sm_80+` (Ampere or newer), which the host RTX 3090 (`sm_86`) satisfies.
    2. Requires the `Block-Sparse-Attention` submodule to be initialized at `server/deps/Block-Sparse-Attention`. If missing or cutlass is uninitialized, BSA auto-disables with a warning.
- **`DFLASH27B_TESTS`**: (Default: `ON`)
  - Configures whether the C++ unit and numerics tests are built.
- **`DFLASH27B_SERVER`**: (Default: `ON`)
  - Configures whether the native HTTP server (`dflash_server`) and `backend_ipc_daemon` are built.

---

## 2. Megakernel Python Extension Build Configuration (`optimizations/megakernel`)

The Megakernel fuses all 24 layers of the Qwen 3.5-0.8B hybrid DeltaNet/Attention forward pass into a single persistent CUDA kernel. It is compiled as a PyTorch C++/CUDA extension named `qwen35_megakernel_bf16_C`.

### Package Metadata & Dependencies (`pyproject.toml`)

- **Python Target**: Requires `python >=3.12, <3.13`.
- **Runtime Dependencies**: `torch>=2.0`, `transformers>=4.50`.
- **Build System Dependencies**: `setuptools>=68`, `wheel`, `torch`.
- **ABI Compatibility Gating**: The extension compiles against PyTorch's C++ libraries. The workspace requires the build environment and runtime environment to use the exact same PyTorch wheel. Thus, **build isolation must be disabled** (`no-build-isolation-package = ["qwen35-megakernel-bf16"]` in the workspace root `pyproject.toml`).

### Compilation Logic (`setup.py`)

- **Source Files**:
  - Default: `torch_bindings.cpp`, `kernel.cu`, `prefill.cu`.
  - Blackwell (SM 12x): If Blackwell is detected, setup automatically appends `kernel_gb10_nvfp4.cu`, `prefill_megakernel.cu`, and `prefill_bw.cu`. It also links `cublasLt` and defines `MEGAKERNEL_HAS_NVFP4` and `MEGAKERNEL_HAS_PREFILL_MEGA`.
- **Architecture Detection**:
  - Setup detects target capability via the `MEGAKERNEL_CUDA_ARCH` environment variable (e.g. `sm_86`).
  - If the env variable is unset, it imports `torch` and queries `torch.cuda.get_device_capability()`. If that fails, it defaults to `sm_75` (Turing).
- **Numeric Parametrization**:
  The following parameters are controlled via environment variables:
  - `MEGAKERNEL_NUM_BLOCKS`: Number of thread blocks (default: `82` for Ampere, `28` for Pascal).
  - `MEGAKERNEL_BLOCK_SIZE`: Threads per block (default: `512`).
  - `MEGAKERNEL_LM_NUM_BLOCKS`: Blocks for LM head (default: `512` for Ampere, `256` for Pascal).
  - `MEGAKERNEL_LM_BLOCK_SIZE`: Block size for LM head (default: `256`).
  - `MEGAKERNEL_DN_PHASE2_WMMA`: Defaults to `0`.

---

## 3. Submodules and Dependencies

Before compiling, the following external and internal dependencies must be correctly set up:

### Git Submodules

Two vendored libraries in `server/deps` must be populated:

1. **`server/deps/llama.cpp`**: Pointing to the Lucebox fork `https://github.com/Luce-Org/llama.cpp-dflash-ggml.git` (branch `luce-dflash`).
2. **`server/deps/Block-Sparse-Attention`**: Pointing to `https://github.com/mit-han-lab/Block-Sparse-Attention.git`.

- _Note: Verification shows both submodules are already checked out and initialized to the proper commits in the active workspace._

### Python Environment Setup

- The project uses `uv` as its package manager.
- A custom PyTorch index (`pytorch-cu128`) pointing to `https://download.pytorch.org/whl/cu128` is configured in the root `pyproject.toml` to install PyTorch with CUDA 12.8 support.

---

## 4. Implementation Action Plan

The implementation agent should follow this step-by-step strategy to successfully compile the C++ server and build the Megakernel extension:

### Step 1: Ensure Submodules are Synchronized

For safety, run:

```bash
git submodule update --init --recursive
```

### Step 2: Set Up Python Virtual Environment

Populate the virtual environment with PyTorch and dependencies. Since `no-build-isolation-package` is set for the megakernel, a two-pass `uv sync` process is required:

```bash
# 1. Sync workspace dependencies (populates venv with CUDA 12.8 PyTorch + setuptools)
uv sync

# 2. Sync and compile the megakernel package against the newly populated environment
MEGAKERNEL_CUDA_ARCH=sm_86 uv sync --extra megakernel
```

_(Alternatively, for a manual pip workflow inside a standard venv:)_

```bash
pip install --upgrade setuptools wheel
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install transformers>=4.50
pip install -e optimizations/megakernel --no-build-isolation
```

### Step 3: Compile the C++ speculative-decoding server and daemon

Navigate to the C++ server directory, configure via CMake targeting the host RTX 3090 (`sm_86`), and build:

```bash
# Navigate to the server folder
cd server

# Configure CMake targeting sm_86 and fast-compilation options
cmake -B build -S . \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_ARCHITECTURES=86 \
  -DDFLASH27B_GPU_BACKEND=cuda \
  -DDFLASH27B_FA_ALL_QUANTS=OFF

# Build target binaries (test_dflash, dflash_server, backend_ipc_daemon)
cmake --build build --target test_dflash dflash_server backend_ipc_daemon -j$(nproc)
```

### Step 4: Verification

Verify both compilation targets:

1. **C++ server check**:
   ```bash
   # Run local unit tests (if compiled with curl support)
   cd build && ctest --output-on-failure
   ```
2. **Megakernel check**:
   Verify the compiled CUDA extension can be imported:
   ```bash
   uv run python -c "import qwen35_megakernel_bf16_C; print('Megakernel successfully compiled & imported!')"
   ```
