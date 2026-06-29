# Emergent vLLM Plan — June 2026

## Architecture
- BeeLlama.cpp (TurboQuant + DFlash)
- NF-CoT Proxy (shadow latent injection)
- OpenFang (agent orchestration)
- Rank Router (request distribution)

## Roadmap
1. [x] Base llama-server with CUDA
2. [x] NF-CoT proxy layer
3. [ ] DFlash speculative decoding
4. [ ] Multi-agent TaskFlow
5. [ ] Kimi Claw integration
