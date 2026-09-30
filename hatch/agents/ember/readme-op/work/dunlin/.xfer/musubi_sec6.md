## VI. Source Layout & External References

### What's actually in this repo

| Path | What it is |
|------|-----------|
| `bin/kataware-doki` | Launcher for the coordinator (`src/coordinator/kataware-doki.ts`) |
| `bin/mitsuha` | Launcher for the worker node (`src/worker/mitsuha.ts`) |
| `bin/taki` | Launcher for the CDP node (`src/cdp-node/taki.ts`) |
| `src/coordinator/kataware-doki.ts` | **Kataware-doki** — distributed inference orchestrator. Bun server with a WebSocket control plane on `:9223`; tracks nodes by id/arch/VRAM/model with idle/busy/dead status |
| `src/worker/mitsuha.ts` | **Mitsuha** — worker node. Reports architecture and `nvidia-smi` VRAM, connects to the coordinator over WebSocket |
| `src/cdp-node/taki.ts` | **Taki** — Chrome DevTools Protocol node. Opens inference tabs and injects WASM over CDP (`:9222`, configurable via `CDP_PORT`/`CDP_HOST`) |
| `src/0clKiller/0clKiller_v6.9.py` | The Liberation Module spec (§IV.4): unprivileged user-namespace container identity-swap technique plus payload-drop design |
| `src/morphe/autohook_master.py` | Session management, checkpointing, and HS256 JWT utilities; gateway probing helpers |
| `tools/ens_decode.py` | ENS C2 deobfuscation for Jackskid post-disruption builds (IPv6→IPv4, XOR `0xA5`) |
| `tools/rc4_decrypt.py` | Jackskid / Aisuru-gen2 RC4+LCG config decryptor (3-index PRGA, 5-pass S-box scramble, seed `0xE0A4CBD6`) |
| `corpus/deepfield_corpus.parquet` | Deepfield public research as a zstd columnar store (36 markdown reports, 72 CSV IOC files, 1 YARA rule) |
| `MANIFESTO.md` | *The Anna-Senpai Question* — memetic forensics essay on the 2016 leak |
| `build.sh` | Build script |

### External references (not vendored)

| Source | Role |
|--------|------|
| [deepfield/public-research](https://github.com/deepfield/public-research) | The canonical research corpus |
| [aoao4riri/mirai](https://github.com/aoao4riri/mirai) | Whitehat Mirai variant |
| [CirqueiraDev/OverburstC2](https://github.com/CirqueiraDev/OverburstC2) | C2 panel for educational analysis |
| [jgamblin/Mirai-Source-Code](https://github.com/jgamblin/Mirai-Source-Code) | Original Mirai source (historical) |
