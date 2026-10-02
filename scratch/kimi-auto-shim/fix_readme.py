import io

r = '/home/toxic/sovereign/tau-extensions/packages/tau-kimi-auto/README.md'
t = io.open(r, encoding='utf-8').read()

old_lines = [
    'resolves it to the best available Kimi model each request, falling back to',
    'the ' + chr(96) + 'gpt-oss' + chr(96) + ' interim when no Kimi candidate is healthy. This extension makes',
    'the alias selectable as a first-class model inside Tau/omp sessions.',
]
new_lines = [
    'resolves it to the best available Kimi model each request. It is Kimi-only by',
    'design ' + chr(45) + ' when no Kimi candidate is healthy the shim answers 503 instead of',
    'silently routing to a non-Kimi model. This extension makes the alias',
    'selectable as a first-class model inside Tau/omp sessions.',
]

old = chr(10).join(old_lines)
new = chr(10).join(new_lines)
assert old in t, 'pattern not found'
io.open(r, 'w', encoding='utf-8').write(t.replace(old, new))
print('README updated OK')
