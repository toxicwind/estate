# grafana-mesh recreates /home/toxic/estate (D-2026-10-28 #49)

## Symptom
During the full-disk estate sweep, /home/toxic/estate spontaneously materialized as a directory (mode 750, containing grafana/data) at 2026-10-28 15:27:59 while it had been deleted. bin-contract-audit lease FAILed ("estate exists"). The sweep's restart of the grafana daemon triggered it.

## Root cause
`stack/services/grafana-mesh.sh` line 6: `SOV="${ESTATE_ROOT:-/home/toxic/estate}"` hardcodes the estate path as default, and `GF_PATHS_DATA="${GF_PATHS_DATA:-$SOV/grafana/data}"` prompts grafana to mkdir -p /home/toxic/pens/estate/grafana/data on every restart. estate-reconcile-watch had the identical `ESTATE_ROOT:-/home/toxic/estate` default. Multiple daemon launchers root on /home/toxic/estate — each start recreates it.

## Fix
Perl mass-apply across pens/estate/{stack,tools,ops,services,scripts,bridge}: `s{/home/toxic/estate(?!pens/) }{/home/toxic/pens/estate/}g` — 87 files, all daemon launchers now pens-rooted, zero bare estate refs remain. grafana data/logs/plugins now write to pens/estate/grafana/. Restarted grafana → /home/toxic/estate stayed absent.
Commit: 364b68ddf9. Pushed to origin/main.

## Contract test
restart estate/grafana → running on 25110, pens/estate/grafana/data created, /home/toxic/estate remains absent. bin-contract-audit → lease ok.
