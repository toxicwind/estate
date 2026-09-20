#!/usr/bin/env python3
"""Sovereign naming validator — enforces naming-grammar.md.
Loads live configs, fails non-zero on any violation. Re-runnable.
Usage: python3 validate.py [--no-live]  (--no-live skips the /v1/models + :25104 probes)
"""
import json, sys, yaml, urllib.request, os

HERD = os.environ.get('NAMING_HERD', '/home/toxic/sovereign/config/herd.yaml')
TAU_MODELS = os.environ.get('NAMING_TAU_MODELS', '/home/toxic/.tau/agent/models.yml')
TAU_CONFIG = os.environ.get('NAMING_TAU_CONFIG', '/home/toxic/.tau/agent/config.yml')
ROUTER_JSON = os.environ.get('NAMING_ROUTER_JSON', '/home/toxic/.tau/model-router.json')
HEALTH = os.environ.get('NAMING_HEALTH', '/home/toxic/sovereign/data/model-health.json')

# Generic policy words: grandfathered set may exist, new ones are violations.
GRANDFATHERED_GENERIC = {'fast', 'tiny', 'small', 'medium', 'code', 'long', 'uncensored'}
GENERIC_WORDS = {'fast', 'tiny', 'small', 'medium', 'large', 'code', 'quality',
                 'long', 'uncensored', 'quick', 'slow', 'big', 'huge', 'mini',
                 'cheap', 'best', 'latest-model'}

errors, warnings = [], []

def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)

def live_ids(url):
    try:
        d = json.load(urllib.request.urlopen(url, timeout=15))
        return {m['id'] for m in d.get('data', [])}
    except Exception as e:
        err(f'LIVE PROBE FAILED {url}: {e}')
        return set()

def main():
    no_live = '--no-live' in sys.argv
    try:
        cfg = yaml.safe_load(open(HERD).read())
    except Exception as e:
        err(f'herd.yaml does not parse: {e}'); return report()

    models = cfg.get('models', {}) or {}
    model_names = set(models.keys())

    # ---- 1. alias uniqueness + shadowing ----
    alias_owner = {}
    for mid, mdef in models.items():
        for a in (mdef or {}).get('aliases', []) or []:
            if a in alias_owner:
                err(f'ALIAS COLLISION: {a!r} claimed by {alias_owner[a]} and {mid}')
            else:
                alias_owner[a] = mid
            if a in model_names and a != mid:
                err(f'SHADOWING: alias {a!r} on {mid} shadows model block {a}')
    # ---- 2. no new generic aliases ----
    for a, owner in alias_owner.items():
        if a in GENERIC_WORDS and a not in GRANDFATHERED_GENERIC:
            err(f'NEW GENERIC ALIAS: {a!r} on {owner} — generic words are banned (see naming-grammar.md)')

    # ---- 3. matrix / scheduler refs resolve ----
    router = cfg.get('router', {}) or {}
    mvars = ((router.get('settings') or {}).get('matrix') or {}).get('vars') or {}
    for var, target in mvars.items():
        if target not in model_names:
            err(f'MATRIX DANGLING: var {var} -> {target!r} (no such model block)')
    evict = ((router.get('settings') or {}).get('matrix') or {}).get('evict_costs') or {}
    for k in evict:
        if k not in mvars and k not in model_names:
            err(f'EVICT_COST DANGLING: {k!r} not a matrix var or model')
    exclusive = (((router.get('settings') or {}).get('matrix') or {}).get('sets') or {}).get('exclusive') or ''
    for var in [v.strip() for v in str(exclusive).split('|') if v.strip()]:
        if var not in mvars:
            err(f'EXCLUSIVE DANGLING: {var!r} not a matrix var')
    fifo = ((cfg.get('scheduler') or {}).get('settings') or {}).get('fifo') or {}
    for key in (fifo.get('priority') or {}):
        if key not in model_names:
            err(f'FIFO DANGLING: {key!r} (no such model block)')

    # ---- 4. consumer refs resolve to live+healthy ----
    health = json.load(open(HEALTH))
    dead = {mid for mid, m in health['models'].items() if not m.get('healthy')}
    healthy = {mid for mid, m in health['models'].items() if m.get('healthy')}

    herd_live = set() if no_live else live_ids('http://127.0.0.1:25100/v1/models')
    sov_live = set() if no_live else live_ids('http://127.0.0.1:25104/v1/models')

    def resolve_herd(mid):
        """mid without lane prefix -> (kind, canonical) or (DEAD/STALE, mid)."""
        if mid in model_names: return ('model', mid)
        if mid in alias_owner: return ('alias', alias_owner[mid])
        if not no_live and mid in herd_live: return ('live', mid)
        return ('UNRESOLVED', mid)

    tconf = yaml.safe_load(open(TAU_CONFIG).read())
    roles = (tconf.get('modelRoles') or {})
    mr = json.load(open(ROUTER_JSON))
    profiles = {k: v.get('selector') for k, v in (mr.get('profiles') or {}).items()}
    consumers = {f'role:{k}': v for k, v in roles.items()}
    consumers.update({f'profile:{k}': v for k, v in profiles.items()})

    for name, ref in consumers.items():
        if not isinstance(ref, str) or '/' not in ref:
            err(f'{name}: malformed ref {ref!r}'); continue
        lane, mid = ref.split('/', 1)
        if lane == 'sovereign':
            if not no_live and mid not in sov_live:
                err(f'{name}: sovereign/{mid} not on live :25104 catalog')
            continue
        if lane != 'herd':
            err(f'{name}: unknown lane {lane!r} in {ref!r}'); continue
        kind, canon = resolve_herd(mid)
        if kind == 'UNRESOLVED':
            err(f'{name}: {ref} resolves to NOTHING (stale/dead route)')
        elif canon in dead or mid in dead:
            err(f'{name}: {ref} -> {canon} is DEAD per model-health.json')
        elif not no_live and kind == 'live' and mid not in healthy and mid in herd_live:
            warn(f'{name}: {ref} is live but not in healthy set (unmeasured?)')

    # ---- 5. dead macros (defined, never referenced) ----
    macros = cfg.get('macros', {}) or {}
    blob = open(HERD).read()
    for mname in (macros.keys() if isinstance(macros, dict) else []):
        # count references outside its own definition line
        refs = [l for l in blob.splitlines() if mname in l and not l.strip().startswith(mname + ':')]
        if not refs:
            warn(f'DEAD MACRO: {mname} defined but never referenced')

    return report()

def report():
    for w in warnings: print(f'WARN: {w}')
    for e in errors: print(f'FAIL: {e}')
    print(f'--- {len(errors)} failures, {len(warnings)} warnings')
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
