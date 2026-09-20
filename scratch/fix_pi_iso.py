p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-iso/src/lib.rs'
s = open(p).read()
old = (
    '\t\t\t#[cfg(windows)]\n'
    '\t\t\tlet _ = std::os::windows::fs::symlink_file(&target, &to);\n'
)
new = (
    '\t\t\t#[cfg(windows)]\n'
    '\t\t\t{\n'
    '\t\t\t\t// Windows needs the dir/file symlink variant up front;\n'
    '\t\t\t// propagate failures instead of reporting a successful\n'
    '\t\t\t// clone with the entry silently missing.\n'
    '\t\t\t\tuse std::os::windows::fs::FileTypeExt as _;\n'
    '\t\t\t\tif ft.is_symlink_dir() {\n'
    '\t\t\t\t\tstd::os::windows::fs::symlink_dir(&target, &to).map_err(io_err)?;\n'
    '\t\t\t\t} else {\n'
    '\t\t\t\t\tstd::os::windows::fs::symlink_file(&target, &to).map_err(io_err)?;\n'
    '\t\t\t\t}\n'
    '\t\t\t}\n'
)
assert old in s, 'windows symlink block not found'
s = s.replace(old, new)
open(p, 'w').write(s)
print('pi-iso symlink fix applied')
