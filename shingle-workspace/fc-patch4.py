import pathlib
p = pathlib.Path('/home/toxic/fc-ci-fix-2721520964/.github/workflows/ci.yml')
src = p.read_text()
old = '''      - name: protocol and state tests
        run: python -m unittest discover -s tests -p "test_*.py" -v'''
new = '''      - name: protocol and state tests
        # -t . makes `tests` a package so tests/__init__.py provisions
        # throwaway fleet identity keys (FLEET_KEYS_DIR) before any test
        # module runs -- the audit path signs events and fails closed
        # without key material, which CI runners don't have.
        run: python -m unittest discover -s tests -t . -p "test_*.py" -v'''
assert old in src, 'ci test step not found'
p.write_text(src.replace(old, new, 1))
print('ci.yml updated')
