#!/usr/bin/env python3
"""unshare-root.py: Run commands in unshared namespaces as root.

Fork-based id mapping via newuidmap/newgidmap (the setuid helpers) instead of
direct /proc/self/uid_map writes, which fail EPERM in this container.
Parent installs the maps for the child, then the child execs.
"""
import os, sys, subprocess, ctypes

SYS_unshare = 272
CLONE_NEWUSER = 0x10000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNS = 0x00020000
CLONE_NEWNET = 0x40000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWUTS = 0x04000000

FLAGS = CLONE_NEWUSER | CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWNET | CLONE_NEWIPC | CLONE_NEWUTS

libc = ctypes.CDLL(None, use_errno=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: unshare-root.py <command> [args...]")
        sys.exit(1)
    uid, gid = os.getuid(), os.getgid()
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        # Child: unshare, wait for parent to install the id maps, then exec.
        try:
            os.close(w)
            if libc.syscall(SYS_unshare, FLAGS) == -1:
                err = ctypes.get_errno()
                print(f"unshare failed: errno {err}", file=sys.stderr)
                os._exit(1)
            os.read(r, 1)
            os.close(r)
            os.execlp(sys.argv[1], *sys.argv[1:])
        except Exception as e:
            print(f"child failed: {e}", file=sys.stderr)
            os._exit(1)
    # Parent: install uid/gid maps for the child via the setuid helpers.
    os.close(r)
    try:
        subprocess.run(["/usr/bin/newuidmap", str(pid), "0", str(uid), "1"],
                       check=True, capture_output=True, text=True)
        subprocess.run(["/usr/bin/newgidmap", str(pid), "0", str(gid), "1"],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"idmap failed: {e.stderr.strip()}", file=sys.stderr)
        os.write(w, b"x")
        os.close(w)
        os.waitpid(pid, 0)
        sys.exit(1)
    os.write(w, b"x")
    os.close(w)
    _, status = os.waitpid(pid, 0)
    sys.exit(os.waitstatus_to_exitcode(status))


if __name__ == "__main__":
    main()
