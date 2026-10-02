content = open('/tmp/main-push/agents/oracle-market/agent.toml').read()
# Remove the HEAD version (gemini-2.0-flash), keep our llama-swap version
lines = content.split('\n')
out = []
skip_head = False
for line in lines:
    if line.startswith('<<<<<<< HEAD'):
        skip_head = True
        continue
    if line.startswith('>>>>>>>'):
        skip_head = False
        continue
    if skip_head:
        continue
    out.append(line)
open('/tmp/main-push/agents/oracle-market/agent.toml','w').write('\n'.join(out))
print('resolved')
