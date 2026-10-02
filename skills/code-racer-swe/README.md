# code-racer-swe

[![CI](https://github.com/toxic/estate/skills/code-racer-swe/actions/workflows/ci.yml/badge.svg)]
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]

A universal code racer and dynamic AST engine for autonomous software engineering agents. code-racer-swe enables agents to race multiple code implementations, compare performance, and select optimal solutions.

## Hero

Accelerate software development by automatically racing code implementations and choosing the fastest, most efficient solution.

## Features

- **Multi-impl Racing** — simultaneously execute and compare different code implementations
- **Dynamic AST Analysis** — parse, optimize, and profile code structures in real-time
- **Performance Benchmarking** — measure execution speed, memory usage, and resource consumption
- **Optimization Suggestions** — receive actionable refactoring recommendations
- **Agent Orchestration** — coordinate multiple agents for distributed testing

## Quick Start

```bash
# Install code-racer-swe
pip install code-racer-swe

# Race two implementations
code-racer-swe race hello_world.c impl1.c impl2.c

# Compare performance
code-racer-swe profile --benchmark app.py

# Get optimization suggestions
code-racer-swe suggest --target function.py
```

## Architecture

Code-racer-swe follows a three-stage pipeline:

1. **Parser** — extracts AST and metadata from source files
2. **Racer** — executes implementations in sandboxed environments
3. **Analyzer** — compares results and generates optimization reports

Key components:
- **AST Engine** — structural refactoring and optimization passes
- **Race Controller** — manages concurrent execution and timing
- **Benchmark Suite** — standardized performance measurement protocols
- **Suggestion Engine** — generates code improvements based on benchmarks

## Configuration

Configuration is managed via `config/racer.yaml`:

```yaml
races:
  enabled: true
  max_implementations: 5
  timeout_per_impl: 300
  parallelism: 4

metrics:
  warmup_runs: 3
  sample_size: 100
  sampling_interval: 10ms

suggestions:
  enable_refactoring: true
  priority: high
  output_format: json
```

## Optional Services

- **Distributed Racer** — scales across multiple machines for massive parallelism
- **Cloud Integration** — connects to cloud functions for offloading heavy computations
- **Integration SDK** — plugins for IDEs and CI/CD pipelines

## Development

```bash
# Clone the repository
git clone https://github.com/toxic/estate/skills/code-racer-swe
cd code-racer-swe

# Install dependencies
pip install -e .

# Run the test suite
pytest

# Start the racer daemon
code-racer-swe daemon --config config/racer.yaml
```

## License

MIT License.

## Security

- Sandboxed execution prevents malicious code from harming the host
- Resource limits prevent infinite loops or excessive CPU usage
- All race results are cryptographically signed
- Secure communication channels for distributed races
