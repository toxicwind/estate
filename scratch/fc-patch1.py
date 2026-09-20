import pathlib
p = pathlib.Path('/home/toxic/fc-ci-fix-2721520964/tests/test_tasks.py')
src = p.read_text()
old = """        finally:
            linked_channel.unlink(missing_ok=True)
            (outside_channel / "_meta.json").unlink(missing_ok=True)
            (outside_channel / ".cursors").rmdir()
            outside_channel.rmdir()
            outside_root.rmdir()"""
new = """        finally:
            linked_channel.unlink(missing_ok=True)
            (outside_channel / "_meta.json").unlink(missing_ok=True)
            (outside_channel / ".cursors").rmdir()
            outside_channel.rmdir()
            # cmd_init writes root-level fleet state (op log, channel index)
            (outside_root / ".channels-index").unlink(missing_ok=True)
            (outside_root / ".ops.jsonl").unlink(missing_ok=True)
            outside_root.rmdir()"""
assert old in src, 'boundary finally block not found'
p.write_text(src.replace(old, new, 1))
print('tasks boundary test fixed')
