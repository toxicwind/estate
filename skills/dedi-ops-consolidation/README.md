# dedi-ops-consolidation

[![CI](https://github.com/toxic/estate/skills/dedi-ops-consolidation/actions/workflows/ci.yml/badge.svg)]
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]

A consolidation framework for deduplicating and optimizing the dedi-ops package ecosystem. Combines SSH connection management, deployment targeting, and operational efficiency improvements.

## Hero

Consolidate your dedi-ops tools into a single, optimized deployment pipeline with reduced complexity and improved reliability.

## Features

- **SSH Connection Management** — secure, resilient connections with automatic reconnection
- **Deployment Target Optimization** — smart routing of workloads to appropriate nodes
- **Deduplication Engine** — eliminate redundant processes and resource overlaps
- **Operational Efficiency** — reduce boilerplate and manual intervention
- **Health Monitoring** — real-time status of all deployed components

## Quick Start

```bash
# Install dedi-ops consolidation
pip install dedi-ops-consolidation

# Initialize the consolidation manager
dedici-ops init --config config/consolidation.yaml

# Consolidate and deploy
python dedici-ops deploy --target "node-primary" --profile "production"

# Monitor deployment status
python dedici-ops status
```

## Architecture

Dedi-ops-consolidation follows a hub-and-spoke model:

- **Central Manager** — coordinates all operations and maintains state
- **Node Agents** — handle individual deployment targets and health checks
- **Connection Pool** — manages SSH connections efficiently
- **Deduplication Engine** — analyzes workloads to find redundancies

Key components:
- **SSH Gateway** — handles authentication, tunneling, and remote execution
- **Target Router** — directs workloads to optimal nodes based on capacity
- **Dedup Analyzer** — identifies overlapping processes and suggests merges
- **Health Monitor** — tracks node status and triggers alerts

## Configuration

Core configuration: `config/consolidation.yaml`

Key sections:

- `nodes` — list of target nodes with capabilities and capacities
- `ssh_config` — connection parameters and security settings
- `dedup_rules` — policies for identifying and merging duplicates
- `deployment_targets` — mapping of workloads to preferred nodes

Example configuration:

```yaml
nodes:
  - name: "node-01"
    ip: "192.168.1.10"
    capacity: 100
    role: "compute"
  - name: "node-02"
    ip: "192.168.1.11"
    capacity: 50
    role: "storage"

dsync_rules:
  - name: "redundant-compute"
    pattern: "cpu > 80%"
    action: "merge"
  - name: "duplicate-storage"
    pattern: "volume overlap"
    action: "consolidate"
```

## Optional Services

- **Dedici Agent** — lightweight agent for distributed execution
- **Health Dashboard** — real-time visualization of cluster status
- **Backup Scheduler** — automated snapshots and disaster recovery

## Development

```bash
# Clone the repository
git clone https://github.com/toxic/estate/skills/dedi-ops-consolidation
cd dedici-ops-consolidation

# Install dependencies
pip install -e .

# Run the consolidation tests
pytest tests/consolidation/

# Deploy the manager
python dedici-ops/manager.py --config config/consolidation.yaml
```

## License

MIT License.

## Security

- SSH keys are stored securely and rotated automatically
- Network traffic is encrypted with TLS 1.3
- All node communications are authenticated and authorized
- Audit logs track all consolidation actions
