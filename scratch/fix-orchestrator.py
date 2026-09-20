p = 'scripts/typecheck.mjs'
s = open(p).read()

old_comment = '//   packages/pi-tasks                 -> its own tsconfig.json (upstream)\n'
new_comment = old_comment + '//   packages/omp-undo-redo            -> its own tsconfig.json (upstream)\n'
assert old_comment in s, 'comment anchor missing'
s = s.replace(old_comment, new_comment)

old_excl = '// omp-kafka) is checked by the root tsconfig, which excludes the four above so'
new_excl = '// omp-kafka) is checked by the root tsconfig, which excludes the five above so'
assert old_excl in s, 'exclude comment anchor missing'
s = s.replace(old_excl, new_excl)

old_step = "  { name: 'pi-tasks', dir: 'packages/pi-tasks', cmd: 'bunx tsc -p tsconfig.json --noEmit' },"
new_step = old_step + "\n  { name: 'omp-undo-redo', dir: 'packages/omp-undo-redo', cmd: 'bunx tsc --noEmit' },"
assert old_step in s, 'step anchor missing'
s = s.replace(old_step, new_step)

# pi-tasks native-check note: extend the parenthetical to cover omp-undo-redo
old_note = '// (pi-tasks was moved to native after its root-config ChildProcess errors\n// proved to be a dual-@types/node resolution artifact; its own tsconfig is green.)'
new_note = ('// (pi-tasks and omp-undo-redo were moved to native after their root-config\n'
            '// diagnostics proved to be resolution artifacts absent under their native\n'
            '// configs; both native tsconfigs are green.)')
if old_note in s:
    s = s.replace(old_note, new_note)

open(p, 'w').write(s)
print('orchestrator updated')
