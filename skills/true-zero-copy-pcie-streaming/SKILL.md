---
name: true-zero-copy-pcie-streaming
description: True zero-copy PCIe host-mapped memory streaming in Triton and CUDA runtime
---

# True Zero-Copy PCIe Host Streaming via Triton & CUDA Runtime

Use when streaming weights directly from host RAM (Ryzen / CPU) into GPU registers over PCIe without explicit VRAM allocation or cudaMemcpy.

## Implementation Pattern
1. Allocate host pinned memory with mapping flags:
   ```python
   libcudart = ctypes.CDLL("libcudart.so")
   flags = 2 | 4 # cudaHostAllocMapped | cudaHostAllocWriteCombined
   host_ptr = ctypes.c_void_p()
   libcudart.cudaHostAlloc(ctypes.byref(host_ptr), size_bytes, flags)
   
   dev_ptr = ctypes.c_void_p()
   libcudart.cudaHostGetDevicePointer(ctypes.byref(dev_ptr), host_ptr, 0)
   ```
2. Pass `dev_ptr.value` (integer) into Triton JIT kernel.
3. Cast integer to pointer in Triton:
   ```python
   b_ptr = b_ptr_int.to(tl.pointer_type(tl.int8)) + offset
   b_val = tl.load(b_ptr)
   ```
