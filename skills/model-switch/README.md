# model-switch

[![CI](https://github.com/toxic/estate/skills/model-switch/actions/workflows/ci.yml/badge.svg)]
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]

A flexible model switching framework that dynamically loads and swaps machine learning inference engines at runtime. model-switch enables seamless migration between different architectures (Transformer, LFM, quantized variants) without code changes.

## Hero

Switch your model backend in milliseconds — swap between Transformer, LFM, and optimized variants without downtime.

## Features

- **Hot-swap capability** — replace model weights on the fly with zero downtime
- **Multi-architecture support** — supports Transformers, LFM, and custom backends
- **Gradual rollout** — canary deployments and traffic splitting for safe migrations
- **Performance profiling** — compare latency, throughput, and memory across models
- **Automatic fallback** — switch to a secondary model if primary fails

## Quick Start

```bash
# Install model-switch
pip install model-switch

# Initialize with default models
model-switch init

# Switch to LFM model
model-switch switch lfm

# Monitor performance
model-switch stats
```

## Architecture

Model-switch implements a plug-and-play architecture:

- **Model Registry** — central store of available model configurations
- **Loader** — dynamically loads model weights from disk or registry
- **Router** — selects model based on traffic, latency, or policy
- **Profiler** — collects performance metrics for each model variant
- **Swapper** — handles hot-swapping with atomic file replacement

## Configuration

Key configuration areas:

- `models/` — directory containing model weights and configs
- `routes/` — routing rules for traffic distribution
- `swaps/` — scheduled swap policies and canary definitions
- `profiles/` — performance profiles for benchmarking

Example `models/config.yaml`:

```yaml
models:
  lfm: { path: ./weights/lfm, size: 7B }
  transformer: { path: ./weights/transformer, size: 5B }
  quantized: { path: ./weights/q8, size: 4B }

routes:
  default: lfm
  canary: transformer
  failover: quantized
```

## Optional Services

- **Metrics Service** — exposes Prometheus endpoints for model health
- **Dashboard** — Grafana-ready visualization of model performance
- **Audit Log** — tracks all model switches for compliance

## Development

```bash
# Setup development environment
pip install -e .

# Run the test suite
pytest tests/

# Build the CLI
make build
```

## License

MIT License.

## Security

- Model weights are signed and verified before loading
- Access to sensitive models is gated by authentication
- All configuration changes require commit approval
- Regular security scanning integrated into CI
