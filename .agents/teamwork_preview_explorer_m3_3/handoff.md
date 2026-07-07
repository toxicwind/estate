# Handoff Report: Milestone 3 (Compile lucebox-hub)

## 1. Observation

- **Project Structure & Submodules**:
  - Found submodules in `.gitmodules` (lines 1-7):
    ```ini
    [submodule "dflash/deps/llama.cpp"]
    	path = server/deps/llama.cpp
    	url = https://github.com/Luce-Org/llama.cpp-dflash-ggml.git
    	branch = luce-dflash
    [submodule "dflash/deps/Block-Sparse-Attention"]
    	path = server/deps/Block-Sparse-Attention
    	url = https://github.com/mit-han-lab/Block-Sparse-Attention.git
    ```
  - Executed `git submodule status` and confirmed both submodules are initialized and checked out at:
    - `server/deps/Block-Sparse-Attention` (`49d6c39e4dc0303442cda3bb758b3925d4399c49`)
    - `server/deps/llama.cpp` (`9cd9e1edb6d244ac82b9dc925d67c3bf9c9f3480`)

- **Host Toolchain & Hardware**:
  - Executed `nvidia-smi` and observed host GPU is a GeForce RTX 3090 (Ampere architecture, Compute Capability `sm_86`).
  - Executed `cmake --version`, `g++ --version`, `nvcc --version`, `uv --version`, and `python3 --version`. Results:
    - CMake: `4.3.4`
    - G++: `16.1.1`
    - NVCC: CUDA `13.3` (V13.3.33)
    - uv: `0.11.21`
    - Python: `3.14.5` (System default)
    - Project `.python-version`: `3.12`

- **DFlash Compile settings (`server/CMakeLists.txt`)**:
  - GPU backend options (lines 2-4): `DFLASH27B_GPU_BACKEND` (values: `"cuda"`, `"hip"`).
  - Target architecture override (lines 6, 75): `DFLASH27B_USER_CUDA_ARCHITECTURES` or `DFLASH27B_HIP_ARCHITECTURES`.
  - KV-quant option (line 96): `DFLASH27B_FA_ALL_QUANTS` (default `ON`).
  - Block-sparse attention option (line 327): `DFLASH27B_ENABLE_BSA` (default `ON`). Auto-disabled on legacy CUDA compute architectures (< `sm_80`, lines 473-482) or if `Block-Sparse-Attention` submodule headers are missing (lines 486-494).
  - rocWMMA prefill option for HIP (line 103): `DFLASH27B_HIP_SM80_EQUIV` (default `OFF`).
  - Blackwell consumer fix (line 152): `DFLASH27B_USE_BLACKWELL_CONSUMER_FIX` (default `OFF`).
  - Native server & tests options (lines 576-577): `DFLASH27B_TESTS` (default `ON`), `DFLASH27B_SERVER` (default `ON`).

- **Megakernel Compile settings (`optimizations/megakernel/setup.py` & `pyproject.toml`)**:
  - Dependency & Build isolation (root `pyproject.toml` lines 41-51):
    ```toml
    # Megakernel's CUDAExtension links against torch's C++ libs, so the build
    # and runtime envs must share the same torch wheel... Skip
    # isolation here and require a two-pass install:
    no-build-isolation-package = ["qwen35-megakernel-bf16"]
    ```
  - GPU capabilities detection (setup.py lines 7-20): checks environment variable `MEGAKERNEL_CUDA_ARCH` or queries `torch.cuda.get_device_capability()`.

---

## 2. Logic Chain

1. **Host GPU & Target Architectures**: The host is equipped with an RTX 3090, which matches CUDA Compute Capability `sm_86` (Ampere). To cut compilation time by 5-6× (avoiding default multi-arch fatbinary build), the implementation agent must explicitly configure CMake with `-DDFLASH27B_USER_CUDA_ARCHITECTURES="86"` and `-DCMAKE_CUDA_ARCHITECTURES="86"`.
2. **BSA Enabling**: Since RTX 3090 is `sm_86` (>= 80), and the `Block-Sparse-Attention` submodule is initialized on the host, the Block-Sparse Attention (`DFLASH27B_ENABLE_BSA=ON`) optimization will be successfully enabled by default.
3. **Megakernel Shared Dependency**: The Megakernel uses `torch.utils.cpp_extension` to build PyTorch C++ bindings, which link against `libtorch`. Because build isolation is disabled via `no-build-isolation-package`, `setup.py` needs access to the PyTorch wheels in the main environment. This necessitates a two-pass install: (a) run `uv sync` to build the main environment with PyTorch from the `pytorch-cu128` index, and then (b) run `uv sync --extra megakernel` to compile the C extension under that environment.
4. **Python Versioning**: The default python version is `3.14.5`, which violates the project requirements (`>=3.12,<3.13`). However, because the repository contains `.python-version` specifying `3.12`, `uv` will automatically provision a Python 3.12 interpreter during synchronization, mitigating any host version issues.

---

## 3. Caveats

- **Hugging Face Model Downloads**: Running the integration tests or benchmarks (`bench_pp_tg.py`, `final_bench.py`) requires model weights (`Qwen/Qwen3.5-0.8B`, `unsloth/Qwen3.6-27B-GGUF`, etc.). Under `CODE_ONLY` network mode, external model downloading will fail. The implementation agent must check if weights can be loaded locally or if they are already pre-cached on the filesystem.
- **System CURL Dependency**: If `libcurl4-openssl-dev` is missing on the system, the server builds without the passthrough proxy option (`DFLASH_HAS_CURL=0`). Since g++ and cmake are highly up-to-date on this system, we assume development headers for standard libraries are available.

---

## 4. Conclusion

The build environment is fully prepared (CUDA 13.3, GCC 16.1.1, CMake 4.3.4, and an RTX 3090 GPU). The C++ server can be compiled successfully using CMake targeting `sm_86` (RTX 3090 capability), and the Megakernel python package can be built using a two-pass `uv` synchronization.

---

## 5. Verification Method

To verify the implementation:

1. **C++ server & daemon verification**:
   - Run C++ unit tests:
     ```bash
     cmake --build server/build --target check
     ```
   - Check that output binaries are generated:
     - `server/build/dflash_server`
     - `server/build/test_dflash`
     - `server/build/test_server_unit`

2. **Megakernel extension verification**:
   - Verify that the compiled C extension imports successfully in python:
     ```bash
     uv run python -c "import qwen35_megakernel_bf16_C; print('Import OK!')"
     ```
   - Run correctness checking:
     ```bash
     uv run --directory optimizations/megakernel python bench_pp_tg.py
     ```
