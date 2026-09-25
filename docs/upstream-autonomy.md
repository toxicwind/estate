# Upstream Autonomy & Fork Synchronization Architecture

To maintain a clean fork basis while retaining sovereign autonomy and seamless upstream syncing against `can1357/oh-my-pi`, we employ a decoupled **Vendor-Overlay / Overlay-Patch** workflow.

---

## 1. Preserving Upstream Autonomy (`vendor` Remote)

1. **Explicit Upstream Tracking**:
   The upstream repository is tracked as a dedicated git remote:
   ```sh
   git remote add vendor https://github.com/can1357/oh-my-pi.git
   ```

2. **Clean Fast-Forward Merges (`vendor/main`)**:
   When upstream releases new versions, pull directly without local commit pollution:
   ```sh
   git fetch vendor
   git merge vendor/main --no-edit
   ```

---

## 2. Isolating Custom Fork Features

To prevent merge conflicts during upstream pulls, sovereign-specific enhancements are organized into:
- **Dedicated Plugins / Extensions** (`projects/ranch/herd`, `flock`, `shep`, `router`).
- **Custom Helper Scripts** (`sovereign/helpers/`).
- **Config Overrides** (`~/.tau/config.yml`, `~/.tau/sovereign-env.sh`).
- **Isolated Documentation** (`projects/tau/docs/upstream/` vs custom fork docs).

---

## 3. Automated CI/CD Upstream Sync & Push Building

Our automated CI/CD pipeline (`buildsrv` on port `25148` + Git `post-commit` hooks) ensures that:
- Every commit or upstream merge triggers an automated background build.
- Version tracking (`v18.3.0`) and content hashes cache artifacts cleanly.
- Immutable binary pinning (`omp-pin`) prevents upstream updates from breaking local paths.
