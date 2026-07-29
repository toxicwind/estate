#!/bin/bash
# build-znver4-llm-kernel.sh
# One-shot kernel build for Zen4 + Ampere (RTX 3090)
# Run: bash build-znver4-llm-kernel.sh

set -euo pipefail

echo "🔥 Building linux-cachyos-znver4-llm-cuda86"
echo "============================================"

# ── Clone CachyOS kernel PKGBUILD ──
if [ ! -d ~/cachyos-kernel ]; then
    echo "[1/5] Cloning CachyOS kernel repo..."
    git clone --depth 1 https://github.com/CachyOS/linux-cachyos.git ~/cachyos-kernel
else
    echo "[1/5] Updating existing repo..."
    cd ~/cachyos-kernel
    git pull --depth 1
fi

cd ~/cachyos-kernel/linux-cachyos

# ── Export build environment ──
export CC=clang
export CXX=clang++
export LD=ld.lld
export AR=llvm-ar
export NM=llvm-nm
export STRIP=llvm-strip
export OBJCOPY=llvm-objcopy
export OBJDUMP=llvm-objdump
export LLVM=1
export LTO=full

export KBUILD_CFLAGS="-O3 -march=znver4 -mtune=znver4 -fivopts -fmodulo-sched -funswitch-loops -ftree-vectorize -fvect-cost-model=unlimited -fno-semantic-interposition -fomit-frame-pointer"

# ── Inject kernel config overrides ──
# These are read by the PKGBUILD if _cachy_config is defined
_cachy_config=(
    'CONFIG_TRANSPARENT_HUGEPAGE=y'
    'CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=y'
    'CONFIG_PREEMPT=y'
    'CONFIG_PREEMPT_DYNAMIC=y'
    'CONFIG_HZ_1000=y'
    'CONFIG_HZ=1000'
    'CONFIG_NO_HZ_FULL=y'
    'CONFIG_NO_HZ=y'
    'CONFIG_SCHED_BORE=y'
    'CONFIG_LRU_GEN=y'
    'CONFIG_LRU_GEN_ENABLED=y'
    'CONFIG_DAMON=y'
    'CONFIG_DAMON_VADDR=y'
    'CONFIG_DAMON_PADDR=y'
    'CONFIG_DAMON_SYSFS=y'
    'CONFIG_DAMON_RECLAIM=y'
    'CONFIG_DAMON_LRU_SORT=y'
    'CONFIG_AMD_PSTATE=y'
    'CONFIG_AMD_PSTATE_DEFAULT_MODE=active'
    'CONFIG_AMD_PSTATE_PREFERRED_CORE=y'
    'CONFIG_AMD_CACHE_OPTIMIZER=y'
    'CONFIG_NUMA=y'
    'CONFIG_AMD_NUMA=y'
    'CONFIG_NUMA_BALANCING=y'
    'CONFIG_HUGETLBFS=y'
    'CONFIG_HUGETLB_PAGE=y'
    'CONFIG_CGROUP_DEVICE=y'
    'CONFIG_USER_NS=y'
    'CONFIG_PCI_P2PDMA=y'
    'CONFIG_DMABUF_MOVE_NOTIFY=y'
    'CONFIG_DRM_AMDGPU=y'
    'CONFIG_TCP_CONG_BBR=y'
    'CONFIG_DEFAULT_TCP_CONG="bbr"'
    'CONFIG_IOSCHED_BFQ=y'
    'CONFIG_BFQ_GROUP_IOSCHED=y'
    'CONFIG_DEFAULT_BFQ=y'
)
export _cachy_config

# ── Modify PKGBUILD for our scheduler + arch ──
echo "[2/5] Patching PKGBUILD..."

# Set scheduler to BORE
sed -i 's/^_cpusched=.*/_cpusched=cachy-bore/' PKGBUILD

# Set tick rate to 1000Hz
sed -i 's/^_HZ_ticks=.*/_HZ_ticks=1000/' PKGBUILD

# Set preemption to full
sed -i 's/^_preempt=.*/_preempt=full/' PKGBUILD

# Set tickless to full
sed -i 's/^_tickless=.*/_tickless=full/' PKGBUILD

# Set THP to always
sed -i 's/^_hugepage=.*/_hugepage=always/' PKGBUILD

# Set LTO to full
sed -i 's/^_LTO_mode=.*/_LTO_mode=full/' PKGBUILD

# Set compiler to clang
sed -i 's/^_compiler=.*/_compiler=clang/' PKGBUILD

# Set CPU arch to znver4
sed -i 's/^_processor_opt=.*/_processor_opt=znver4/' PKGBUILD

# Enable CachyOS config
sed -i 's/^_cachy_config=.*/_cachy_config=true/' PKGBUILD

# Enable performance governor
sed -i 's/^_per_gov=.*/_per_gov=true/' PKGBUILD

# Enable BBR3
sed -i 's/^_tcp_bbr3=.*/_tcp_bbr3=true/' PKGBUILD

# Enable DAMON
sed -i 's/^_damon=.*/_damon=true/' PKGBUILD

# Enable NUMA
sed -i 's/^_NUMAdisable=.*/_NUMAdisable=false/' PKGBUILD

# Disable debug
sed -i 's/^_build_debug=.*/_build_debug=false/' PKGBUILD

# Disable ZFS
sed -i 's/^_build_zfs=.*/_build_zfs=false/' PKGBUILD

# Use nvidia-open
sed -i 's/^_nvidia_open=.*/_nvidia_open=true/' PKGBUILD

# Set custom package name
sed -i 's/^pkgbase=.*/pkgbase=linux-cachyos-znver4-llm-cuda86/' PKGBUILD

echo "[3/5] PKGBUILD patched. Preview:"
grep -E '^_cpusched=|^_HZ_ticks=|^_preempt=|^_hugepage=|^_LTO_mode=|^_compiler=|^_processor_opt=|^_cachy_config=|^_per_gov=|^_tcp_bbr3=|^_damon=|^pkgbase=' PKGBUILD

echo ""
echo "[4/5] Starting build (this takes 20-60 minutes)..."
echo "    Ctrl+C to abort. Resume with: cd ~/cachyos-kernel/linux-cachyos && makepkg -si"
echo ""

# Build and install
makepkg -si --noconfirm

echo ""
echo "✅ [5/5] Build complete!"
echo ""
echo "Next steps:"
echo "  1. Add kernel cmdline to bootloader:"
echo "     amd_pstate=active amd_pstate_prefcore=1 transparent_hugepage=always amd_iommu=pt iommu=pt nvidia-drm.modeset=1 nvidia.NVreg_UsePageAttributeTable=1 nvidia.NVreg_EnableGpuFirmware=1 nvidia.NVreg_InitializeSystemMemoryAllocations=0 mitigations=off pcie_aspm=off"
echo ""
echo "  2. Reboot"
echo "  3. Verify: uname -r"
echo "  4. Run: sudo systemctl start llm-tune"