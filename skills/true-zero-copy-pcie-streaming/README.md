# true-zero-copy-pcie-streaming

[![for-the-badge](https://img.shields.io/badge/CUDA-7.0-FF7F0E?style=for-the-badge)](https://developer.nvidia.com/cuda) [![for-the-badge](https://img.shields.io/badge/Triton-0D7377?style=for-the-badge)](https://triton-lang.org) [![for-the-badge](https://img.shields.io/badge/pinned-memory-2GiB-caption?style=for-the-badge)](https://docs.nvidia.com/cuda/)

## true-zero-copy-pcie-streaming

True zero-copy PCIe host-mapped memory streaming in Triton and CUDA runtime. Use when streaming weights directly from host RAM (Ryzen / CPU) into GPU registers over PCIe without explicit VRAM allocation or `cudaMemcpy`.

### Implementation Pattern

1. **Allocate host pinned memory with mapping flags**:
   ```python
   libcudart = ctypes.CDLL("libcudart.so")
   flags = 2 | 4 # cudaHostAllocMapped | cudaHostAllocWriteCombined
   host_ptr = ctypes.c_void_p()
   libcudart.cudaHostAlloc(ctypes.byref(host_ptr), size_bytes, flags)
   
   dev_ptr = ctypes.c_void_p()
   libcudart.cudaHostGetDevicePointer(ctypes.byref(dev_ptr), host_ptr, 0)
   ```

2. **Pass `dev_ptr.value` (integer) into Triton JIT kernel**

3. **Cast integer to pointer in Triton**:
   ```python
   b_ptr = b_ptr_int.to(tl.pointer_type(tl.int8)) + offset
   b_val = tl.load(b_ptr)
   ```

### Quick start (3 commands max)

```bash
# 1. Allocate pinned host memory and get device pointer
python3 -c "
import ctypes
libcudart = ctypes.CDLL('libcudart.so')
flags = 2 | 4  # cudaHostAllocMapped | cudaHostAllocWriteCombined
size = 1024 * 1024  # 1 MiB
host_ptr = ctypes.c_void_p()
libcudart.cudaHostAlloc(ctypes.byref(host_ptr), size, flags)
dev_ptr = ctypes.c_void_p()
libcudart.cudaHostGetDevicePointer(ctypes.byref(dev_ptr), host_ptr, 0)
print(f'host_ptr={host_ptr.value}, dev_ptr={dev_ptr.value}')
"

# 2. Pass dev_ptr.value into Triton JIT kernel
# 3. Cast and load in Triton: b_ptr = b_ptr_int.to(tl.pointer_type(tl.int8)) + offset
```

### Architecture

Zero-copy eliminates the bandwidth tax of `cudaMemcpy` by mapping host memory directly into the GPU's address space. The `cudaHostAllocMapped | cudaHostAllocWriteCombined` flags allocate pinned memory that is simultaneously accessible from both host and device. The `cudaHostGetDevicePointer` call retrieves the device-side pointer, which can then be passed directly into Triton JIT kernels. The integer pointer is cast to `tl.pointer_type(tl.int8)` within Triton, enabling `tl.load` to access host memory as if it were device memory. This pattern is essential for streaming large weights (e.g., 32B model parameters) directly from host RAM into GPU registers without ever touching VRAM allocation.

### Config / optional services

- `cudaHostAllocMapped` (flag 2) — host memory is mapped into device address space
- `cudaHostAllocWriteCombined` (flag 4) — write-combined caching for streaming workloads
- Any `size_bytes` — allocation size (must be page-aligned for `cudaHostAlloc`)
- Triton JIT kernel that accepts `dev_ptr.value` as integer argument
- `tl.pointer_type(tl.int8)` — Triton pointer type for byte-level access

### Dev / contributing

- Verify that allocated host memory is page-aligned (required by `cudaHostAlloc`)
- Test that `cudaHostGetDevicePointer` returns a valid device pointer
- Ensure Triton kernel correctly casts integer to pointer and loads from it
- Profile that streaming performance exceeds `cudaMemcpy`-based approach
- Zero-copy must not require `cudaMalloc` or explicit VRAM allocation
- Works on Ryzen/CPU host systems with NVIDIA GPU

### License

Open Claw — see `skill.toml` for details.

### Security

- Zero-copy must not require `cudaMalloc` or explicit VRAM allocation
- Works on Ryzen/CPU host systems with NVIDIA GPU
- Write-combined caching may cause stale reads; synchronize appropriately for correctness