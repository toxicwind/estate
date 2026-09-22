import sys, os, tempfile
sys.path.insert(0, '/home/toxic/sovereign/projects/mesh/squawk')
sys.path.append('/home/toxic/squawk')
os.environ['FLEET_KEYS_DIR'] = '/home/toxic/.shingle/squawk-root/keys'
from pathlib import Path
import fleet_relay

kd = Path('/home/toxic/.shingle/squawk-root/keys')

def mk(name, text):
    p = Path(tempfile.mkdtemp()) / name
    p.write_text(text)
    return p

cases = [
    ('sealed-envelope', mk('sealed.md',
        '---\nseq: 1\nfrom: ember\nchannel: fleet\nts: 2026-09-21T00:00:00Z\n---\n'
        '-----BEGIN SQUAWK SEALED MESSAGE-----\nto: x\nalg: sealedbox\n\nQUJD\n'
        '-----END SQUAWK SEALED MESSAGE-----\n'), 'fleet'),
    ('envelope-fragment', mk('frag.md',
        '---\nseq: 1\nfrom: ember\nchannel: fleet\nts: 2026-09-21T00:00:00Z\n---\n'
        '-----BEGIN SQUAWK SEALED MESSAGE-----\ngarbage\n'), 'fleet'),
    ('plain-unsigned', mk('plain.md',
        '---\nseq: 1\nfrom: ember\nchannel: fleet\nts: 2026-09-21T00:00:00Z\n---\nhello world\n'), 'fleet'),
    ('priv-unsigned', mk('priv.md',
        '---\nseq: 1\nfrom: ember\nchannel: priv-test\nts: 2026-09-21T00:00:00Z\n---\nsecret\n'), 'priv-test'),
]

for name, p, ch in cases:
    rec = fleet_relay.build_relay_record(p, channel=ch, identity='relay', key_dir=kd)
    b = rec.get('body')
    print(name, '| sig=' + rec['signature'], '| sealed=' + str(rec['sealed']),
          '| body=' + (repr(b[:40]) if b else 'None'))
