import sys
path = '/home/toxic/wt-main-merge/docs/fleet-knowledgebase.md'
lines = open(path).readlines()
out = []
n = -1
side = None
h_buf = []
b_buf = []
K = ['B','H','H','H','H','H','CUSTOM','B']
for l in lines:
    s = l.rstrip('\n')
    if s == '<'*7 + ' HEAD':
        n += 1; side = 'H'; h_buf = []; continue
    if s == '='*7 and side == 'H':
        side = 'B'; b_buf = []; continue
    if s.startswith('>'*7) and side == 'B':
        k = K[n]
        if k == 'H':
            out.extend(h_buf)
        elif k == 'B':
            out.extend(b_buf)
        elif k == 'CUSTOM':
            hb = list(h_buf)
            while hb and hb[-1].strip() == '':
                hb.pop()
            out.extend(hb)
            bb = b_buf
            i = 0
            while i < len(bb) and bb[i].strip() == '':
                i += 1
            if out and out[-1].strip() != '':
                out.append('\n')
            out.extend(bb[i:])
        side = None; continue
    if side == 'H':
        h_buf.append(l)
    elif side == 'B':
        b_buf.append(l)
    else:
        out.append(l)
open(path, 'w').writelines(out)
markers = sum(1 for l in out if l.startswith('<<<<<<<'))
print('markers left: %d' % markers)
