import pathlib

# --- chat.py: getattr for a.ephemeral (argparse sets it in prod; tests bypass argparse) ---
p = pathlib.Path('/home/toxic/fc-ci-fix-2721520964/chat.py')
src = p.read_text()
old = """    if a.ephemeral is not None:
        fleet_ephemeral.mark_ephemeral(d, float(a.ephemeral))"""
new = """    # argparse always sets --ephemeral in production; test fixtures build
    # their own namespaces, so degrade gracefully instead of AttributeError.
    ephemeral = getattr(a, "ephemeral", None)
    if ephemeral is not None:
        fleet_ephemeral.mark_ephemeral(d, float(ephemeral))"""
assert old in src, 'ephemeral check not found'
src = src.replace(old, new, 1)
old2 = """    eph = f" ephemeral(ttl={a.ephemeral}s)" if a.ephemeral is not None else """""
new2 = """    eph = f" ephemeral(ttl={ephemeral}s)" if ephemeral is not None else """""
assert old2 in src, 'ephemeral status string not found'
src = src.replace(old2, new2, 1)
p.write_text(src)
print('chat.py ephemeral hardened')
