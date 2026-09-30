# omp-marketplace

The `darkphilosophy` [Oh My Pi](https://github.com/can1357/oh-my-pi) plugin marketplace. This repository contains only the catalog (`.omp-plugin/marketplace.json`) — every plugin lives in its own repository.

## Usage

```bash
omp plugin marketplace add DarkPhilosophy/omp-marketplace
```

Then install any listed plugin:

```bash
omp plugin install omp-headroom@darkphilosophy
omp plugin install omp-discord@darkphilosophy
```

Upgrade with `omp plugin upgrade`, or set `marketplace.autoUpdate = auto` in OMP settings to upgrade automatically at startup.

## Plugins

| Plugin | Repository | Description |
|---|---|---|
| `omp-headroom` | [DarkPhilosophy/omp-headroom](https://github.com/DarkPhilosophy/omp-headroom) | Headroom context compression for OMP: proxy lifecycle, tool-output compression, session archive compaction with CCR retrieval, and a live savings widget. |
| `omp-discord` | [DarkPhilosophy/omp-discord](https://github.com/DarkPhilosophy/omp-discord) | Explicit, local Discord account operations for Oh My Pi. |

## License

GPL-3.0-or-later
