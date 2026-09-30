<div align="center">

![fork](https://img.shields.io/badge/toxicwind-fork-blue)
![benchmarks](https://img.shields.io/badge/benchmarks-python_http_libs-0ea5e9)

# toxicwind/http-bench-toxicwind — fork

**[toxicwind](https://github.com/toxicwind)'s fork of the
`python-http-libraries-benchmark` project.** Upstream's README and methodology
are preserved below; this fork adds:

| Addition | What it is |
|---|---|
| [`benchmark_analytics.py`](./benchmark_analytics.py) | Analytics pass over raw benchmark data |
| [`factory.py`](./factory.py), [`model.py`](./model.py) | Benchmark factory + data model |
| [`benchmark_tests.py`](./benchmark_tests.py) | Benchmark test suite |
| [`benchmark_results.csv`](./benchmark_results.csv) | Our measured results (100-request batches, req/sec + total + connection + TLS latency) |
| `mean_*.png` | Rendered charts: requests/sec, connection time, TLS handshake time, total response time |

</div>

---
