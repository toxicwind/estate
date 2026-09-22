import pathlib, re
d = pathlib.Path('/home/toxic/.shingle/squawk-root/fleet')
files = []
for p in d.glob('*.md'):
    m = re.match(r'(\d+)-', p.name)
    if m:
        files.append((int(m.group(1)), p))
files.sort()
sizes = []
for _, p in files[-200:]:
    try:
        sizes.append((p.name, len(p.read_bytes())))
    except Exception:
        pass
tot = sum(s for _, s in sizes)
mx = max(sizes, key=lambda x: x[1])
print('files:', len(sizes), 'total_bytes:', tot, 'max:', mx[0], mx[1])
over500 = sum(1 for _, s in sizes if s > 500)
print('bodies_over_500_bytes:', over500)
