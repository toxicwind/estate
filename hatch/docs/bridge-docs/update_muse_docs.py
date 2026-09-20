import io

d = '/home/toxic/sovereign/docs/Meta/Muse AI/'

# --- README.md: hatch first-class ---
p = d + 'README.md'
s = io.open(p).read()
s = s.replace('(internal codename **Jarvis**)', '(platform codename **hatch**)')
s = s.replace(
    'No Meta docs were harmed (or consulted).',
    'No Meta docs were harmed (or consulted). '
    + chr(96) + 'JARVIS' + chr(96)
    + ' remains only as the runtime-cell internal codename.')
io.open(p, 'w').write(s)

# --- runtime-cell.md ---
p = d + 'runtime-cell.md'
s = io.open(p).read()

s = s.replace(
    '- Internal platform: **Jarvis**.',
    '- Platform codename: **hatch** (first-class). '
    + chr(96) + 'JARVIS' + chr(96)
    + ' is only the runtime-cell internal codename ('
    + chr(96) + 'JARVIS_HOME' + chr(96) + ', '
    + chr(96) + 'JARVIS_CD_CHANNEL' + chr(96) + ').')

s = s.replace(
    '| Internal codename ' + chr(96) + 'JARVIS' + chr(96)
    + ' (' + chr(96) + 'JARVIS_HOME=/home/hatch' + chr(96)
    + ', per-VM ' + chr(96) + 'JARVIS_CD_CHANNEL' + chr(96)
    + ') | ' + chr(96) + 'guest.env' + chr(96) + ' |',
    '| Platform codename ' + chr(96) + 'hatch' + chr(96)
    + ' (binaries ' + chr(96) + 'hatch' + chr(96) + '/'
    + chr(96) + 'spawnd' + chr(96) + '/' + chr(96) + 'authd' + chr(96)
    + '/' + chr(96) + 'hatch-execd' + chr(96) + '); '
    + chr(96) + 'JARVIS' + chr(96)
    + ' only the cell-internal codename | '
    + chr(96) + 'guest.env' + chr(96) + ', binary names |')

s = s.replace(
    '5. ' + chr(96) + 'hatch-execd' + chr(96)
    + ' serves tool execution; subagents run as daemon children'
    + ' \u2014 so when the cell dies, they all die instantly.',
    '5. ' + chr(96) + 'hatch-execd' + chr(96)
    + ' serves tool execution; subagents are logical agents run as daemon'
    + ' tool calls (no separate OS processes observed 2026-09-14)'
    + ' \u2014 so when the cell dies, they all die instantly.')

parentage = '''
## Process parentage (traced 2026-09-14, uid=0 inside the cell)

From `/` downward, verified via `ps -ef --forest` and
`/proc/<pid>/status` (`NSpid`/`PPid`):

- **Above the cell (host, invisible from inside):** the spawner. Both
  `hatch daemon --runtime-cell-leader=<pid>` and `hatch-execd` report
  **PPid 0** \u2014 their parent lives outside this PID namespace. That is as
  high as the trace goes from inside; the host side is unobservable here.
- **PID 1:** `/usr/lib/systemd/systemd` \u2014 the cell init. Direct parent of
  every in-cell daemon (ws bridge, squawk push client, buildsrvd,
  proxy_fwd, health poller, journald).
- **The fleet is not processes.** Subagents/workers have no OS PIDs; they
  are logical rows in the external Postgres (`agent.agents`,
  `agent.subagent_spawns`) executed as `hatch-execd` tool calls. Consequence:
  the DB can report agents "running" with zero processes behind them
  (ghost rows, dangling activity cards) \u2014 process inspection alone cannot
  audit the fleet; the DB ledger is the source of truth.
'''
if '## Process parentage' not in s:
    s = s.rstrip('\n') + '\n' + parentage
io.open(p, 'w').write(s)

# --- open-questions.md: fold in what's now known ---
p = d + 'open-questions.md'
s = io.open(p).read()
s = s.replace(
    '5. **What is Sentinel?** Referenced as the egress-routing layer ('
    + chr(96) + 'hatch-egress-proxy' + chr(96)
    + ', "Sentinel-routed egress"). Separate service? Unknown.',
    '5. **What is Sentinel?** Partially answered 2026-09-14: it routes egress ('
    + chr(96) + 'hatch-egress-proxy' + chr(96)
    + ', "Sentinel-routed") AND owns the approval store \u2014 Sentinel'
    + chr(39) + 's approval records are explicitly outside the '
    + chr(96) + 'muse.db' + chr(96)
    + ' query surface (per the DB schema guide). Still unknown: where it runs,'
    + ' its full responsibilities.')
io.open(p, 'w').write(s)

print('docs updated ok')
