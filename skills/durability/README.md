# durability

[![CI](https://github.com/toxic/estate/skills/durability/actions/workflows/ci.yml/badge.svg)]
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]

A durability-focused system for building resilient applications and data pipelines. Implements fault tolerance, data persistence guarantees, and graceful degradation strategies.

## Hero

Design your systems to survive failures — with built-in resilience patterns, automatic recovery, and guaranteed data durability.

## Features

- **Fault Tolerance** — automatic failover and recovery mechanisms
- **Data Durability** — persistent storage with replication and backup
- **Graceful Degradation** — maintain partial functionality during failures
- **Circuit Breakers** — prevent cascade failures in dependent services
- **Retry Logic** — intelligent retry policies with exponential backoff

## Quick Start

```bash
# Install durability framework
pip install durability

# Initialize a durable application
python durability/app.py --config config/durable.yaml

# Enable data persistence
python durability/app.py --enable-persistence

# Simulate failure recovery
python durability/recovery.py --simulate --fail-node 1
```

## Architecture

Durability follows a layered approach:

1. **Application Layer** — business logic with resilience primitives
2. **Persistence Layer** — durable storage with ACID guarantees
3. **Recovery Layer** — automatic restart and state reconstruction
4. **Monitoring Layer** — health checks and alerting

Key components:
- **Resilience Library** — circuit breakers, timeouts, retries
- **Storage Adapter** — abstracted persistence backends (SQL, KV, S3)
- **Recovery Manager** — handles crash recovery and state restoration
- **Health Monitor** — tracks system health and triggers alerts

## Configuration

Primary configuration: `config/durable.yaml`

Key sections:

- `resilience` — circuit breaker settings, timeout values
- `persistence` — storage backend, replication strategy
- `recovery` — restart policies, backup schedules
- `monitoring` — health checks and alerting thresholds

Example configuration:

```yaml
resilience:
  circuit_breakers:
    enabled: true
    failure_threshold: 5
    recovery_timeout: 30
  timeouts:
    default: 30
    db: 10
    http: 5

persistence:
  backend: "postgresql"
  replicas: 3
  backup_interval: "hourly"

recovery:
  restart_policy: "auto"
  state_backup: true
  max_restarts: 3

monitoring:
  health_checks:
    - "database_connection"
    - "cache_access"
    - "api_endpoint"
```

## Optional Services

- **Backup Scheduler** — automated data backups and retention policies
- **Chaos Monkey** — intentional failure injection for resilience testing
- **Metrics Export** — Prometheus/Grafana integration for observability

## Development

```bash
# Setup development environment
pip install -e .

# Run the durability tests
pytest tests/durability/

# Initialize a new durable project
python durability/cli.py init --template "microservice"
```

## License

MIT License.

## Security

- All data is encrypted at rest using AES-256
- Authentication and authorization for all operations
- Regular penetration testing and vulnerability scanning
- Compliance with data protection regulations (GDPR, CCPA)
