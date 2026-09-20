import pathlib
p = pathlib.Path('/home/toxic/fc-ci-fix-2721520964/relay/feed.py')
src = p.read_text()
old = """            for wd, mask, name in _read_events():
                path = _wd_to_path.get(wd, "")
                # new dir under chat root -> watch it if it's a channel"""
new = """            for wd, mask, name in _read_events():
                # new dir under chat root -> watch it if it's a channel"""
assert old in src, 'dead assignment not found'
p.write_text(src.replace(old, new, 1))
print('dead path assignment removed')
