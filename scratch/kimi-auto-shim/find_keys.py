import os
import re

# Find files that assign actual VALUES to KIMI/MOONSHOT API key vars
# (not just references like keyEnv: KIMI_API_KEY or ${KIMI_API_KEY}).
pat = re.compile(r'(KIMI_API_KEY|MOONSHOT_API_KEY)\s*=\s*["\']?([^\s"\'$][^\s"\']*)')
skip_dirs = {'.git', 'node_modules', '__pycache__', '.cache', 'target'}
hits = []
for root, dirs, files in os.walk('/home/toxic'):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    # keep it bounded: skip the huge bruteforce/staging trees' deep content
    for f in files:
        p = os.path.join(root, f)
        try:
            if os.path.getsize(p) > 2_000_000:
                continue
            with open(p, 'r', errors='ignore') as fh:
                head = fh.read(200000)
            if pat.search(head):
                # show only the variable NAME that matched, never the value
                names = sorted(set(m.group(1) for m in pat.finditer(head)))
                hits.append((p, names))
                if len(hits) >= 15:
                    raise StopIteration
        except StopIteration:
            raise
        except Exception:
            pass
for p, names in hits:
    print(p, names)
print('done, hits:', len(hits))
