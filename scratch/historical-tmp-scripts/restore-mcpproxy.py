import tarfile, re, os
ups = set(open("/tmp/upstream-paths.txt").read().split())
wt = set(open("/tmp/worktree-paths.txt").read().split())
missing = [m for m in sorted(ups - wt) if re.match(r"(internal|cmd|web|oas)/", m)]
print("to restore:", len(missing))
prefix = "mcpproxy-go-69572f091933b1451a1483476efebacdc49b1887a/"
tf = tarfile.open("/tmp/upstream.tgz")
names = {n: n[len(prefix):] for n in tf.getnames() if n.startswith(prefix)}
by_stripped = {v: k for k, v in names.items()}
a = tf.extractfile(by_stripped["cmd/mcpproxy/main.go"]).read()
b = open("/tmp/mcpproxy-verify/projects/mesh/gateway/cmd/mcpproxy/main.go", "rb").read()
print("anchor cmd/mcproxy/main.go byte-identical:", a == b)
restored, absent = 0, []
for m in missing:
    if m in by_stripped:
        data = tf.extractfile(by_stripped[m]).read()
        dest = "/tmp/mcpproxy-verify/projects/mesh/gateway/" + m
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(data)
        restored += 1
    else:
        absent.append(m)
print("restored:", restored)
for m in absent:
    print("NOT IN TARBALL":, m)
