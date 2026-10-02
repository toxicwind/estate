#!/bin/bash
# L5: syscall/import surface — any reload/watch mechanism?
set -u
BIN=/opt/hatch/bin/hatch
OUT=../findings/lane5_syscalls.txt
{
echo "== dynamic imports: watch/signal/ipc =="
nm -D "$BIN" | grep -iE 'inotify|fanotify|signal|signalfd|epoll|eventfd|ptrace|process_vm|memfd|timerfd' || echo none
echo; echo "== env-related imports =="
nm -D "$BIN" | grep -iE 'getenv|environ|setenv|putenv|clearenv'
echo; echo "== total undefined imports =="
nm -D "$BIN" | grep -c ' U '
} > "$OUT"
cat "$OUT"
