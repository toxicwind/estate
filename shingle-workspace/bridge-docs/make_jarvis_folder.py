import io, os, shutil

base = '/home/toxic/sovereign/docs/Meta/Muse AI/'
jarvis = base + 'Jarvis/'
os.makedirs(jarvis, exist_ok=True)

# move the runtime-cell doc (the JARVIS internals doc) into Jarvis/
src = base + 'runtime-cell.md'
dst = jarvis + 'runtime-cell.md'
if os.path.exists(src):
    shutil.move(src, dst)

# update README index link
p = base + 'README.md'
s = io.open(p).read()
s = s.replace('`(runtime-cell.md)`', '`(Jarvis/runtime-cell.md)`')
io.open(p, 'w').write(s)

print('jarvis folder ready')
print(os.listdir(jarvis))
