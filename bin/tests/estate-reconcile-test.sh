#!/usr/bin/env bash
# bin/tests/estate-reconcile-test.sh — sandbox tests for bin/estate-reconcile (WS2).
# All scenarios run in a temp dir with a scratch manifest; the real estate is
# never touched. Squawk is disabled (no fleet dir under scratch SQUAWK_ROOT).
set -u

ER="${ER:-/home/toxic/sovereign/bin/estate-reconcile}"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "PASS: $1"; }
bad()  { FAIL=$((FAIL+1)); echo "FAIL: $1"; }

new_sandbox() {
  T="$(mktemp -d)"; export T
  export ESTATE_ROOT="$T/estate" SQUAWK_ROOT="$T/squawk"
  mkdir -p "$ESTATE_ROOT/log" "$SQUAWK_ROOT"
  MANIFEST="$T/manifest.yaml"
  sha_a="$(printf 'binary-a-content' | sha256sum | awk '{print $1}')"
  printf 'binary-a-content' > "$T/a.bin"
  chmod 755 "$T/a.bin"
  cp "$T/a.bin" "$T/a.immutable"
  cat > "$MANIFEST" <<EOF
version: 1
binaries:
  alpha:
    path: $T/a.bin
    sha256: "$sha_a"
    immutable_copy: $T/a.immutable
    source: test
runtime_paths:
  - $T/runtime/
EOF
}

# --- 1. drift detection -------------------------------------------------------
new_sandbox
if "$ER" check --manifest "$MANIFEST" >/dev/null 2>&1; then ok "check clean on healthy sandbox"; else bad "check clean on healthy sandbox"; fi
printf 'CORRUPTED' >> "$T/a.bin"
if out="$("$ER" check --manifest "$MANIFEST" 2>&1)"; then bad "drift detection (corrupt -> exit!=0)"; else
  case "$out" in *DRIFT*alpha*sha-mismatch*) ok "drift detection (corrupt -> DRIFT sha-mismatch)";; *) bad "drift detection (wrong output: $out)";; esac
fi

# --- 2. missing binary (binary moved -> detected) -----------------------------
mv "$T/a.bin" "$T/a.bin.moved"
if out="$("$ER" check --manifest "$MANIFEST" 2>&1)"; then bad "missing binary detected"; else
  case "$out" in *DRIFT*alpha*missing*) ok "binary moved -> DRIFT missing";; *) bad "missing binary (wrong output: $out)";; esac
fi
mv "$T/a.bin.moved" "$T/a.bin"

# --- 3. atomic restore --------------------------------------------------------
printf 'CORRUPTED' >> "$T/a.bin"
if "$ER" --apply --manifest "$MANIFEST" >/dev/null 2>&1; then :; else bad "apply exit code"; fi
if [ "$(sha256sum "$T/a.bin" | awk '{print $1}')" = "$sha_a" ]; then ok "atomic restore from immutable copy"; else bad "atomic restore from immutable copy"; fi
if "$ER" check --manifest "$MANIFEST" >/dev/null 2>&1; then ok "check clean after restore"; else bad "check clean after restore"; fi

# --- 4. kill-mid-restore: file is always old-or-new, never partial ------------
bigok=1
for i in $(seq 1 20); do
  head -c 2000000 /dev/urandom > "$T/a.immutable"   # large immutable to widen the race
  sha_big="$(sha256sum "$T/a.immutable" | awk '{print $1}')"
  # rewrite manifest sha for this round
  sed -i "s/sha256: \".*\"/sha256: \"$sha_big\"/" "$MANIFEST"
  printf 'x' > "$T/a.bin"                            # drifted
  "$ER" --apply --manifest "$MANIFEST" >/dev/null 2>&1 &
  apid=$!
  sleep 0.002
  kill -9 "$apid" 2>/dev/null || true
  wait "$apid" 2>/dev/null || true
  got="$(sha256sum "$T/a.bin" | awk '{print $1}')"
  case "$got" in
    "$sha_big") : ;;                                 # fully restored
    "$(printf 'x' | sha256sum | awk '{print $1}')") : ;;  # untouched old
    *) bigok=0; echo "  partial write detected on round $i: $got" ;;
  esac
done
if [ "$bigok" -eq 1 ]; then ok "kill-mid-restore: always old-or-new (20 rounds)"; else bad "kill-mid-restore"; fi
# final converged restore
"$ER" --apply --manifest "$MANIFEST" >/dev/null 2>&1
new_sandbox   # reset sandbox for remaining tests

# --- 5. unsigned-HEAD: alert instead of git restore -----------------------------
G="$T/gitrepo"; mkdir -p "$G"; ( cd "$G" && git init -q && git config user.email t@t && git config user.name t \
  && printf 'v1' > app.py && git add app.py && git commit -qm init )   # unsigned commit
sha_v1="$(printf 'v1' | sha256sum | awk '{print $1}')"
cat > "$MANIFEST" <<EOF
version: 1
binaries:
  gitapp:
    path: $G/app.py
    sha256: "$sha_v1"
    source: test
    git_path: app.py
runtime_paths: []
EOF
ESTATE_ROOT_SAVED="$ESTATE_ROOT"; export ESTATE_ROOT="$G"
printf 'v2-drift' > "$G/app.py"
if "$ER" --apply --manifest "$MANIFEST" >/dev/null 2>&1; then rc=0; else rc=$?; fi
if [ "$rc" -eq 2 ] && [ "$(cat "$G/app.py")" = "v2-drift" ]; then
  ok "unsigned-HEAD: alert-only, file untouched (exit 2)"
else bad "unsigned-HEAD (rc=$rc content=$(cat "$G/app.py"))"; fi
if grep -q 'HEAD unsigned' "$G"/log/estate-reconcile.log 2>/dev/null || grep -q 'HEAD unsigned' "$ESTATE_ROOT/log/estate-reconcile.log" 2>/dev/null; then
  ok "unsigned-HEAD logged with reason"
else bad "unsigned-HEAD logged with reason"; fi
export ESTATE_ROOT="$ESTATE_ROOT_SAVED"

# --- 6. symlink drift + restore (herd-style) -----------------------------------
new_sandbox
ln -s "$T/a.immutable" "$T/link.bin"
sed -i "s|path: $T/a.bin|path: $T/link.bin|" "$MANIFEST"
if "$ER" check --manifest "$MANIFEST" >/dev/null 2>&1; then ok "symlink target healthy -> check clean"; else bad "symlink healthy check"; fi
ln -sfn "$T/a.bin" "$T/link.bin"   # re-point at the drifted file
printf 'drift' >> "$T/a.bin"
if "$ER" check --manifest "$MANIFEST" >/dev/null 2>&1; then bad "symlink drift detected"; else ok "symlink drift detected"; fi
"$ER" --apply --manifest "$MANIFEST" >/dev/null 2>&1
if [ "$(readlink -f "$T/link.bin")" = "$T/a.immutable" ] && \
   [ "$(sha256sum "$T/link.bin" | awk '{print $1}')" = "$sha_a" ]; then
  ok "symlink atomically re-pointed to immutable copy"
else bad "symlink restore"; fi

# --- 7. runtime path exemption -------------------------------------------------
new_sandbox
mkdir -p "$T/runtime"
printf 'anything' > "$T/runtime/state.json"
if "$ER" check --manifest "$MANIFEST" >/dev/null 2>&1; then ok "runtime path writes ignored"; else bad "runtime path exemption"; fi

echo "---"; echo "estate-reconcile tests: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
