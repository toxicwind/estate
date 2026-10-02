# flicker

[![CI](https://github.com/toxic/estate/skills/flicker/actions/workflows/ci.yml/badge.svg)]
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]

A lightweight, high-performance file system monitoring and alerting toolkit designed for containerized environments. flicker provides real-time file system observation, anomaly detection, and automated remediation workflows.

## Hero

Monitor your filesystem like a pro — detect drift, spot anomalies, and respond instantly with minimal overhead.

## Features

- **Real-time file system monitoring** — watch file creation, modification, deletion, and permission changes
- **Anomaly detection** — identify unexpected file activity, volume spikes, or unauthorized access
- **Automated remediation** — trigger alerts, quarantine suspicious files, and restore snapshots
- **Low-latency instrumentation** — sub-second event processing with minimal CPU footprint
- **Cross-platform support** — Linux, macOS, and Windows containers

## Quick Start

```bash
# Install flicker
pip install flicker

# Start monitoring a directory
flicker monitor /var/log/app

# View live events
flicker events

# Configure alerts
flicker config alert-policy
```

## Architecture

Flicker consists of three core components:

1. **Event Collector** — captures filesystem events via inotify/eventfd/Windows hooks
2. **Analyzer** — applies heuristics and ML-based scoring to detect anomalies
3. **Remediation Engine** — executes predefined actions (quarantine, rollback, notify)

The architecture follows a producer-consumer pattern with a bounded queue for event buffering, ensuring low-latency processing even under heavy load.

## Configuration

Configuration is managed through YAML files in `config/`. Key settings include:

- `monitor_paths` — directories to watch
- `alert_thresholds` — anomaly severity levels
- `remediation_policies` — automated response rules
- `retention_period` — how long to keep event history

Example configuration:

```yaml
monitor_paths:
  - /var/log/
  - /app/data/

alert_thresholds:
  critical: 5
  warning: 10

remediation_policies:
  quarantine: true
  rollback: false
```

## Optional Services

- **Web Dashboard** — visualize events and metrics in real-time
- **Alert Notifications** — integrate with Slack, PagerDuty, or email
- **Snapshot Manager** — create and restore consistent file system states

## Development

```bash
# Clone the repository
git clone https://github.com/toxic/estate/skills/flicker
cd flicker

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Build the binary
make build
```

## License

This project is licensed under MIT.

## Security

Flicker receives file-change events from the watcher and serves them
locally. It makes no outbound network calls and stores no credentials.
