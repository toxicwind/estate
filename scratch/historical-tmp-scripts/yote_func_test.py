import importlib.util, importlib.machinery
spec = importlib.util.spec_from_loader('sp', importlib.machinery.SourceFileLoader('sp', 'bin/progress-watchdog.py'))
sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)
import tempfile, time, os
from pathlib import Path
d = Path(tempfile.mkdtemp())
now = time.time()
p = d / '00001-intake.md'
p.write_text('---\nmsg_type: intake_request\ntask_id: t1\ntitle: hello\n---\nbody')
os.utime(p, (now-1200, now-1200))
bl, sf = sp.intake_backlog(d, [], now)
assert isinstance(bl, list) and len(bl) == 1 and bl[0]['task_id'] == 't1', bl
assert isinstance(sf, list)
print('intake_backlog function: OK ->', bl[0]['task_id'], bl[0]['age_s'], 's')
