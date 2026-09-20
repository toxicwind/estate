# Service inventory for mise-native migration — tau repair agent (2026-09-14)

Purpose: native `[daemons]` declarations for every service touched/added/fixed during
the kafka+dnsmasq+tau repair. Complete enough to translate directly — no re-derivation needed.

Conventions: `dir` is the working directory; paths below are absolute unless noted.
"auto=start" = start with supervisor. All daemons use `retry = true` (restart on failure).

---

## 1. dnsmasq (NEW — added 2026-09-14)

- **Start command:** `exec ./stack/services/dnsmasq.sh`
- **Working dir:** `/home/toxic/sovereign` (script: `stack/services/dnsmasq.sh`, mode 0755)
- **What the script does:** `exec sudo /usr/bin/dnsmasq -k -C /etc/dnsmasq.conf`
- **Ports bound:** 53/tcp+udp on 10.0.0.218 and 127.0.0.1 (per /etc/dnsmasq.conf:
  `interface=enp12s0`, `listen-address=10.0.0.218,127.0.0.1`, `bind-interfaces`)
- **Env vars:** none
- **Privilege:** needs passwordless `sudo /usr/bin/dnsmasq` (present in /etc/sudoers.d/toxic-nopasswd);
  dnsmasq drops to user `nobody` after binding
- **Readiness:** `ss -ltn 'sport = :53' | grep -q LISTEN`
- **Health:** `dig +short @127.0.0.1 openclaw` → `10.0.0.218`
- **Restart policy:** retry=true, auto=start
- **mise:** false (system binary)
- **Groups:** core, main, all, sovereign-core
- **Replaces:** raw systemd `dnsmasq.service` — DISABLED + MASKED 2026-09-14. Never re-enable.
- **Config:** `/etc/dnsmasq.conf` (system file, verified `dnsmasq --test` clean)

## 2. kafka (REPAIRED 2026-09-14 — was failed since 2026-09-10)

- **Start command:** `exec ./stack/services/kafka.sh`
- **Working dir:** `/home/toxic/sovereign` (script: `stack/services/kafka.sh`, mode 0755)
- **What the script does:** kills stale listeners on 25144/9093, then
  `exec sudo -E -u kafka env JAVA_HOME=/usr/lib/jvm/java-25-graalvm \
  KAFKA_LOG4J_OPTS="-Dkafka.logs.dir=/var/log/kafka" \
  /usr/share/kafka/bin/kafka-server-start.sh /etc/kafka/server.properties`
  (falls back to redpanda stub, then `python3 -m http.server` — last resort only)
- **Ports bound:** 25144/tcp (broker), 9093/tcp (KRaft controller)
- **Env vars:** `KAFKA_PORT=25144`
- **Privilege:** runs as user `kafka` via sudo (passwordless per sudoers); data dir
  `/var/lib/kafka` owned by kafka; KRaft already formatted (node.id=1)
- **Readiness:** `ss -ltn 'sport = :25144' | grep -q LISTEN`
  ⚠️ NOTE: `mise.toml` health-kafka currently expects HTTP on :25144 — WRONG for real
  Kafka (binary protocol). Use TCP readiness, not HTTP.
- **Health:** `/usr/share/kafka/bin/kafka-topics.sh --bootstrap-server 127.0.0.1:25144 --list`
  → `__consumer_offsets`, `sovereign.events`, `sovereign.alerts`
- **Restart policy:** retry=true, auto=start
- **mise:** true
- **Groups:** main, all, sovereign-core (NOT in core)
- **Replaces:** raw systemd `kafka.service` — DISABLED + MASKED 2026-09-14. Never re-enable.
  (Unit failed because KAFKA_PID_DIR=/run/kafka was never created.)
- **Config:** `/etc/kafka/server.properties` (system file; listeners 25144/9093)

## 3. tau-code (PORT MOVED 2026-09-14: 25144 → 25145)

- **Start command:** `exec bun run src/server.ts --port 25145`
- **Working dir:** `/home/toxic/projects/sovereign-projects/tau/engine/packages/metaharness`
- **Ports bound:** 25145/tcp (HTTP)
- **Env vars:** `TAU_CODE_PORT=25145`
- **Readiness:** HTTP `http://127.0.0.1:25145/`
- **Restart policy:** retry=true, auto=start
- **mise:** true (needs bun)
- **Groups:** main, agents, all, sovereign-core
- **Rationale:** 25144 belonged to kafka (6+ references incl. system config); tau-code had
  only 2. Moved to free 25145; `TAU_CODE_PORT` updated in `config/ports.env`.

## 4. nginx (added by sysd-migrate sibling; CONFIG CLEANED by tau 2026-09-14)

- **Start command:** `exec /usr/bin/nginx -c /etc/nginx/nginx.conf -g 'daemon off; pid /tmp/nginx-pitchfork.pid;'`
- **Working dir:** `/home/toxic/sovereign` (dir=".")
- **Ports bound:** 62200/tcp
- **Env vars:** none (`NGINX_PORT=62200` in ports.env is informational)
- **Readiness:** `ss -ltn 'sport = :62200' | grep -q LISTEN`
- **Restart policy:** retry=true, auto=start
- **mise:** false (system binary)
- **Groups:** ⚠️ NONE ASSIGNED — sibling did not add to any group. Needs decision
  (suggest `all` + `sovereign-core`; not `core` — it's a peripheral proxy).
- **Config:** `/etc/nginx/nginx.conf` — 2026-09-14 DISABLED dead upstreams:
  `/scanner/` → 127.0.0.1:62201 and `/agent/` → 127.0.0.1:62010 (both dead, zero code
  references anywhere in sovereign/tau/mist-factory; commented out, backup at
  `/etc/nginx/nginx.conf.bak-20260914`, `nginx -t` clean). Remaining: `/crypto/` static
  alias → /home/toxic/mist-factory/dashboard/ (target dir does not exist — 404s, harmless).
- **Replaces:** raw systemd `nginx.service` — disable pending pitchfork takeover (sibling's item).

## 5. qdrant (BINARY RESTORED 2026-09-14 — was running from deleted inode)

- **Start command:** `exec /home/toxic/.cargo/bin/qdrant-server --config-path ./qdrant-config.yaml`
- **Working dir:** `/home/toxic/sovereign`
- **Ports bound:** 25133/tcp (HTTP), 6334 internal (per qdrant-config.yaml)
- **Env vars:** `QDRANT_PORT=25133`
- **Readiness:** HTTP `http://127.0.0.1:25133/`
- **Health:** returns `{"title":"qdrant - vector search engine","version":"1.19.1",...}`
- **Restart policy:** retry=true, auto=start
- **mise:** false
- **Groups:** core, main, all, sovereign-core
- **Note:** binary was missing; restored 2026-09-14 with official static build 1.19.1.
  Data dir `/home/toxic/sovereign/qdrant_data` intact.

## 6. tau daemon (BROKEN — do NOT migrate as-is)

- **Current (broken):** `exec bun run /home/toxic/projects/sovereign-projects/tau/packages/coding-agent/src/cli.ts`
  — file does not exist (repo restructured to `engine/packages/coding-agent/src/cli/*.ts`).
- **Status 2026-09-14:** stopped + disabled after error-loop. Needs tau maintainer to pick
  the correct entrypoint. Stale copy with old layout: `/home/toxic/sovereign/tau/...`.

---

## ports.env keys added/changed 2026-09-14 (for native layer env)

- `TAU_CODE_PORT=25144` → `25145`
- `KAFKA_PORT=25144` (new)
- `NGINX_PORT=62200` (sibling)

## Raw systemd units retired 2026-09-14 (masked — never re-enable)

- `dnsmasq.service` (was: failed since 08-28, briefly revived then migrated)
- `kafka.service` (was: failed since 09-10)

## Supervisor state 2026-09-14

- Running: pitchfork 2.16.0 supervisor (PID 473253, started ~04:37 MDT) from
  `/home/toxic/.local/share/mise/installs/pitchfork/2.16.0/pitchfork supervisor run`,
  cwd `/home/toxic/sovereign`. Old supervisor (dead IPC) killed.
- Live: dnsmasq, kafka, herd, redis, qdrant, prometheus, grafana, mesh-hub.
- Known-bad: `mesh` (mcpproxy-go binary missing, no go.mod — needs rebuild decision).

## ~/.tau config fixes 2026-09-14 (not services, but tau runtime)

`~/.tau/agent/config.yml` (backup: `config.yml.bak-20260914`) — replaced dead NIM models
with probe-verified `openai/gpt-oss-20b`:
- `modelRoles.task`: `nvidia-nim/nvidia/nemotron-3.5-lightning-30b-a3b` → `nvidia-nim/openai/gpt-oss-20b`
- `modelRoles.advisor`: `nvidia/nvidia/nemotron-3-super-120b-a12b:medium` → `nvidia/openai/gpt-oss-20b:medium`
- `subagents.defaultModel`: `nvidia/nemotron-3-super-120b-a12b:high` → `nvidia/openai/gpt-oss-20b:high`
