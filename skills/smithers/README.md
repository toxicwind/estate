# smithers

[![CI](https://github.com/toxic/estate/skills/smithers/actions/workflows/ci.yml/badge.svg)]
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]

A durable control plane for long-running coding agents. smithers provides centralized orchestration, state management, and reliable task execution for autonomous software engineering agents.

## Hero

Manage fleets of autonomous agents with confidence — from initialization to shutdown, with built-in reliability and observability.

## Features

- **Agent Fleet Management** — register, monitor, and control multiple agents
- **Task Orchestration** — distribute work, track progress, and handle failures
- **State Persistence** — durable storage of agent state across restarts
- **Reliable Execution** — ensures tasks complete successfully even with failures
- **Resource Isolation** — prevents agent interference and resource contention

## Quick Start

```bash
# Install smithers
pip install smithers

# Initialize the control plane
smithers init --config config/smithers.yaml

# Register an agent
smithers register --name "code_reviewer" --role "analysis"

# Start the fleet
smithers start --workers 3

# Monitor agent status
smithers status

#