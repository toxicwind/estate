---
name: dedi-ops-consolidation
description: "Procedure to consolidate the dedi-ops package, fix SSH connection, update deployment targets, and verify the dedicated server and agent functionality."
---

# Ded-iOps Consolidation and Verification Skill

This skill encapsulates the procedure to:
1. Fix SSH connection to the dedicated server at 172.96.160.178.
2. Merge and unify the dedi-ops package into a single installable module.
3. Update deployment targets to correctly map container names and hosts.
4. Verify the system is operational via CLI and API.

## Steps

### 1. Fix SSH Connection
- Create `~/.ssh/config` with:
  ```
  Host mildlyawesome.com
      HostName 172.96.160.178
      User root
      Port 22
      ConnectTimeout 10
      ServerAliveInterval 30
      ServerAliveCountMax 3
      StrictHostKeyChecking accept-new
  ```
- Set permissions: `chmod 600 ~/.ssh/config`

### 2. Merge Working Credentials
- Ensure `/home/toxic/projects/dedi-ops/.env` contains the 16-character `DEDI_OPS_AUTH_PASSWORD` and `DEDI_OPS_AUTH_USERNAME` from `/home/toxic/projects/websites/dedi-ops/.env`.
- Keep `.env` strictly gitignored.

### 3. Create Unified Dedi-Ops Package
Create `/home/toxic/projects/dedi-ops/dedi_ops/` with:
- `__init__.py`: exports `DediConfig` and `DediClient`.
- `config.py`: loads credentials from `.env` and `~/.secrets`.
- `client.py`: HTTP/WebSocket client with methods like `get_health()`, `get_dashboard()`, `execute_intent()`, `docker_ps()`, `nuke_port()`, `list_ghosts()`, etc.
- `cli.py`: command-line interface for `python3 -m dedi_ops <command>`.
- `__main__.py`: entry point.

### 4. Fix Deployment Targets
- Update `/home/toxic/projects/dedi-ops/config/deploy-targets.overrides.json` to include correct `containerName`, `service`, and `hosts` for all targets (agent, arlockworks, effusionlabs, tickets, mildlyawesome, dokploy).
- Trigger remote refresh via `dedi_ops client get_deploy_targets(refresh=True)`.

### 5. Verify Operation
- Run `python3 -m dedi_ops dashboard` to see all containers healthy.
- Run `python3 -m dedi_ops targets` to list targets with correct hosts and container names.
- Run `python3 -m dedi_ops` to execute an intent (e.g., `docker_ps`) via the agent's `/ops/intent/execute` endpoint.

### 6. Preserve Critical Assets
- Verify LV assets in `projects/websites/effusion-labs` are intact.
- Verify Cannabis assets in `projects/experimental-crisis/submodules/effusion-labs` are intact.
- Confirm DayZ/Ezstreet legacy is quarantined under `legacy/dayz-discord/`.

## Usage
Run the skill steps in order to consolidate and verify the dedi-ops system.
