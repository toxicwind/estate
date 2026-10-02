You're right. I've been handing you slices. Here's the whole picture and one prompt that does all of it.

The full state as of the last output

Done and verified:

· VansRouter: sqlite ok: 3.53.2, key at ~/.9router/api.key, /v1/models → 200
· 262 dependent files rewritten (scripts, launchers, nix configs) — 4 binary files skipped
· 3 symlinks replaced with real copies (omp, launcher/tau, frida-compile)
· Engine packages are real copies (nlink=1), no inode overlap with vendor
· tau runs: tau/18.2.8

Partially done / unverified:

· @toxicwind rename — never confirmed
· Submodule fork — pi-utils, pi-ai, pi-tui, pi-catalog, pi-agent-core state unknown
· Workspace relink — bun.lock regenerated but bun pm ls never confirmed
· 20+ sovereign skills — frontmatter fixed, content unverified
· MIRROR-DIFF-vs-upstream.md — stale by 2–4 versions

Broken / pending:

· 49 session JSONL files modified in the prior run (some corrupted)
· Upstream v18.3.0 not merged
· herd daemon on :25100 not running (llama-swap binary missing)
· tau-tmux audit: 6/7 (herd failure is the miss)

Unknown:

· Whether the fork is on forge/gate-retire-final or a renamed branch
· Whether engine package.json workspaces config is complete
· Whether @oh-my-pi/* still appears anywhere outside vendor

One prompt, all phases

```text
# TASK: Full tau recovery and upstream advance

Sequence matters. Phases run in order. Do not start a phase until the
prior one reports clean or explicitly UNRESOLVED with a reason.

# HARD SCOPE — never violate

Never read, write, rg, sed, or classify:
  ~/.tau/sessions/  ~/.tau/logs/  ~/.tau/cache/  ~/.tau/db/  ~/.tau/run/
  *.jsonl  *.db  *.db-shm  *.db-wal  *.sqlite
  node_modules/  .git/  .bun/  scratch/

Guard every operation:

  scope_ok() {
    case "$1" in
      *"/sessions/"*|*"/logs/"*|*"/cache/"*|*"/db/"*|*"/run/"*) return 1 ;;
      *".jsonl"|*".db"|*".db-shm"|*".db-wal"|*".sqlite") return 1 ;;
      *"node_modules"*|*".git"*|*".bun"*|*"/scratch/"*) return 1 ;;
    esac
    return 0
  }

# ═══════════════════════════════════════════════════════════════════════
# PHASE A — Session store integrity
# ═══════════════════════════════════════════════════════════════════════

The prior run rewrote /bin/tau inside session JSONL files. Some are
corrupted. Check what, restore what's possible.

  # Count session files containing the corrupted replacement
  corrupted=$(find ~/.tau/sessions -name '*.jsonl' -mmin -120 2>/dev/null \
    | while read f; do
        grep -q 'HOME/.local/home/toxic' "$f" 2>/dev/null && echo "$f"
      done | wc -l)
  echo "corrupted: $corrupted"

  # Locate pre-merge tarball
  TARBALL=$(ls -t ~/.tau-premerge-*.tar.zst 2>/dev/null | head -1)
  echo "tarball: ${TARBALL:-(none)}"

  # If tarball exists and corrupted > 0, restore per-file
  if [ -n "$TARBALL" ] && [ "$corrupted" -gt 0 ]; then
    mkdir -p /tmp/session-restore
    find ~/.tau/sessions -name '*.jsonl' -mmin -120 2>/dev/null \
      | while read f; do
          rel=${f#/home/toxic/}
          tar --zstd -xf "$TARBALL" -C /tmp/session-restore "$rel" 2>/dev/null \
            && cmp -s /tmp/session-restore/"$rel" "$f" \
            || cp /tmp/session-restore/"$rel" "$f" 2>/dev/null
        done
    echo "restoration attempted"
  fi

Report: corrupted count, tarball status, files restored.

Do NOT attempt to reconstruct session files by hand. If tarball is absent,
mark SESSION_UNRESOLVED and move on.

# ═══════════════════════════════════════════════════════════════════════
# PHASE B — Engine fork state verification
# ═══════════════════════════════════════════════════════════════════════

What scope does the engine actually use? Report, do not change.

  cd ~/sovereign/engine

  # Which packages are under @toxicwind vs @oh-my-pi
  for pj in packages/*/package.json; do
    name=$(jq -r .name "$pj" 2>/dev/null)
    case "$name" in
      "@toxicwind/"*) : ;;
      "@oh-my-pi/"*)  echo "OLD $pj $name" ;;
      *)              echo "OTHER $pj $name" ;;
    esac
  done

  # Any remaining @oh-my-pi references anywhere in engine
  rg -c '@oh-my-pi/' packages/ --glob '!node_modules' 2>/dev/null \
    | head -20

  # Workspace manifest state
  jq '.workspaces, .name' package.json

  # Fork manifest exists?
  cat FORK_MANIFEST.tsv 2>/dev/null || echo "no fork manifest"

Report:
  packages using @toxicwind: <n>
  packages using @oh-my-pi:  <n>
  packages using other:     <n>
  remaining @oh-my-pi refs: <n>
  workspace config:         <verdict>

If packages using @oh-my-pi > 0: mark SCOPE_UNRESOLVED and stop after
Phase G. The rename must happen before the merge, or the merge
reintroduces @oh-my-pi imports.

# ═══════════════════════════════════════════════════════════════════════
# PHASE C — Submodule inventory
# ═══════════════════════════════════════════════════════════════════════

Which @oh-my-pi packages are forked and which aren't.

  for d in ~/sovereign/projects/tau/vendor/oh-my-pi/packages/*/; do
      pkg=$(basename "$d")
      pj="$d/package.json"
      [ -f "$pj" ] || continue
      upstream_name=$(jq -r .name "$pj")
      fork_pj=~/sovereign/engine/packages/"$pkg"/package.json
      if [ -f "$fork_pj" ]; then
          fork_name=$(jq -r .name "$fork_pj")
          echo "FORKED $pkg | $upstream_name -> $fork_name"
      else
          echo "MISSING $pkg | $upstream_name"
      fi
  done

Report:
  forked:   <list>
  missing:  <list>

For each MISSING, copy vendor → engine preserving the fork's scope:

  for pkg in <missing list>; do
      src=~/sovereign/projects/tau/vendor/oh-my-pi/packages/"$pkg"
      dst=~/sovereign/engine/packages/"$pkg"
      rm -rf "$dst"
      mkdir -p "$dst"
      cp -a --no-preserve=links "$src/." "$dst/"
      # rename to @toxicwind if PHASE B reports @toxicwind scope
      if [ "$NEW_SCOPE" = "toxicwind" ]; then
          tmp="$dst/package.json.tmp"
          jq --arg n "@toxicwind/$pkg" '.name = $n' "$dst/package.json" > "$tmp" \
              && mv "$tmp" "$dst/package.json"
      fi
      echo "FORKED $pkg"
  done

# ═══════════════════════════════════════════════════════════════════════
# PHASE D — Upstream v18.3.0 merge
# ═══════════════════════════════════════════════════════════════════════

  cd ~/sovereign/projects/tau/vendor/oh-my-pi
  git fetch vendor --tags 2>&1 | tail -3
  git rev-parse v18.3.0                    # 62bc57be1b03...

  # Find the actual fork point from the mirror-diff doc
  FORK_POINT=$(grep -oP 'fork point[^\n]*\K[a-f0-9]{7,}' \
    ~/sovereign/projects/tau/MIRROR-DIFF-vs-upstream.md | head -1)
  [ -z "$FORK_POINT" ] && FORK_POINT=$(git merge-base HEAD v18.3.0)
  echo "fork point: $FORK_POINT"

  # Delta upstream made
  git diff --name-status "$FORK_POINT" v18.3.0 > /tmp/merge-upstream.txt

  # Delta fork made
  git diff --name-status "$FORK_POINT"..HEAD > /tmp/merge-fork.txt

  # Intersection = files both sides touched
  comm -12 <(cut -f2 /tmp/merge-upstream.txt | sort) \
           <(cut -f2 /tmp/merge-fork.txt | sort) > /tmp/merge-conflicts.txt

  echo "upstream changed: $(wc -l < /tmp/merge-upstream.txt)"
  echo "fork changed:     $(wc -l < /tmp/merge-fork.txt)"
  echo "conflicts:        $(wc -l < /tmp/merge-conflicts.txt)"

For each conflict, classify:

  AUTO_UPSTREAM — take v18.3.0 verbatim
  AUTO_FORK     — keep engine's version
  MANUAL        — three-way merge by hand
  DELETE        — file removed on one side

Known permanent divergences (always MANUAL):
  crates/pi-builtins/src/bre.rs
  crates/pi-builtins/src/grep.rs
  crates/pi-builtins/src/sed.rs
  packages/ai/src/auth-storage.ts
  packages/ai/src/auth-storage/*
  packages/coding-agent/src/debug/*

Apply:
  git worktree add /tmp/v18.3.0-work v18.3.0

  for f in <AUTO_UPSTREAM>; do
      cp /tmp/v18.3.0-work/"$f" ~/sovereign/engine/"$f"
  done

  for f in <MANUAL>; do
      git -C /tmp/v18.3.0-work diff "$FORK_POINT"..v18.3.0 -- "$f" \
        > /tmp/upstream-"$(basename $f)".patch
      git -C ~/sovereign/projects/tau/vendor/oh-my-pi diff "$FORK_POINT"..HEAD -- "$f" \
        > /tmp/fork-"$(basename $f)".patch
      echo "MANUAL: $f — apply both patches, resolve by hand"
  done

After merge, clean up:
  git worktree remove /tmp/v18.3.0-work

# ═══════════════════════════════════════════════════════════════════════
# PHASE E — Workspace reconcile
# ═══════════════════════════════════════════════════════════════════════

  cd ~/sovereign/projects/tau/engine

  bun run scripts/merge-workspace.ts 2>&1 | tail -20
  bun run scripts/cargo-fix.ts 2>&1 | tail -20
  bun run scripts/reconcile.ts 2>&1 | tee /tmp/reconcile.log | tail -30

Report: reconcile exit code, last 5 lines.

# ═══════════════════════════════════════════════════════════════════════
# PHASE F — Build and binary
# ═══════════════════════════════════════════════════════════════════════

  cd ~/sovereign/projects/tau/engine
  timeout 300 bun run build 2>&1 | tail -30

  # If build succeeded, back up the current binary before replacing
  if [ -f dist/omp ] || [ -f dist/tau ]; then
      cp ~/.local/bin/tau ~/.local/bin/tau.pre-merge.$(date +%s)
  fi

  # tau still runs
  tau --version

Report: build status, tau --version output.

# ═══════════════════════════════════════════════════════════════════════
# PHASE G — Dependent repair (real files only)
# ═══════════════════════════════════════════════════════════════════════

Scope strictly limited:

  for root in ~/sovereign/skills ~/sovereign/projects/tau/launcher \
              ~/sovereign/projects/tau/engine/nix ~/.local/bin \
              ~/.tau/extensions ~/.config/tau; do
      [ -d "$root" ] || continue
      find "$root" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' \
                    -not -path '*/scratch/*' 2>/dev/null
  done > /tmp/deps-scope.txt

  # Filter through scope_ok
  awk '{ if ($0 ~ /sessions\/|logs\/|cache\/|db\/|run\/|node_modules|\.git\/|\.bun\/|scratch\/|\.jsonl|\.db$|\.db-/) next; print }' \
    /tmp/deps-scope.txt > /tmp/deps-clean.txt

  echo "scope: $(wc -l < /tmp/deps-clean.txt)"

For each file, classify by word-boundary grep:

  grep -qE '(^|[^a-zA-Z0-9_/])/bin/tau([^a-zA-Z0-9_/]|$)' "$f" && STALE
  grep -qE '(^|[^a-zA-Z0-9_/])/bin/omp([^a-zA-Z0-9_/]|$)' "$f" && STALE
  grep -qE '(^|[^a-zA-Z0-9_/])dist/omp([^a-zA-Z0-9_/]|$)' "$f" && STALE

Fix STALE with word-boundary sed only:

  sed -i -E 's:(^|[^a-zA-Z0-9_/])/bin/tau([^a-zA-Z0-9_/]|$):\1'"$canonical_tau"'\2:g' "$f"
  sed -i -E 's:(^|[^a-zA-Z0-9_/])/bin/omp([^a-zA-Z0-9_/]|$):\1'"$canonical_tau"'\2:g' "$f"
  sed -i -E 's:(^|[^a-zA-Z0-9_/])dist/omp([^a-zA-Z0-9_/]|$):\1dist/tau\2:g' "$f"

One file per round. Max 3 retries per file. Max 5 rounds.

# ═══════════════════════════════════════════════════════════════════════
# PHASE H — Skill validation
# ═══════════════════════════════════════════════════════════════════════

  find ~/sovereign/skills -name 'SKILL.md' -not -path '*/node_modules/*' \
    | while read f; do
        m=$(awk '/^---$/{n++; next} n==1{print}' "$f" | head -30)
        name=$(echo "$m" | grep '^name:' | sed 's/name: *//')
        dir=$(basename "$(dirname "$f")")
        [ "$name" = "$dir" ] || echo "MISMATCH $f name=$name dir=$dir"
        echo "$m" | grep -q 'Triggers on:' || echo "NO_TRIGGERS $f"
      done

Report: mismatches, missing triggers.

Do not rewrite skills unless mismatches > 0. Fix only what's broken.

# ═══════════════════════════════════════════════════════════════════════
# PHASE I — Pitchfork daemons
# ═══════════════════════════════════════════════════════════════════════

  pitchfork status 2>&1 | head -20

  # Specifically herd on :25100
  ss -tlnp 2>/dev/null | grep 25100 && echo "herd listening" \
    || echo "herd NOT listening"

  # Check the herd launch script's binary target
  grep -E '^BIN=|llama-swap' ~/sovereign/stack/services/herd.sh 2>/dev/null

If the llama-swap binary is missing, one search:

  search: "sovereign-swap llama-swap build install <filesystem>"

Apply the documented fix once, retry once. If still failing, mark
HERD_UNRESOLVED and continue.

# ═══════════════════════════════════════════════════════════════════════
# PHASE J — Final verification
# ═══════════════════════════════════════════════════════════════════════

  # Engine and vendor are still independent
  find ~/sovereign/engine/packages -type f -links +1 | wc -l    # 0
  find ~/sovereign/projects/tau/vendor/oh-my-pi/packages -type f -links +1 | wc -l  # 0

  # No @oh-my-pi remains outside vendor
  rg -lF '@oh-my-pi/' ~/sovereign --glob '!**/vendor/**' \
    --glob '!**/node_modules/**' --glob '!**/scratch/**' 2>/dev/null | wc -l

  # tau runs
  tau --version

  # Audits
  bash ~/.local/bin/tau-audit.sh 2>&1 | tail -1
  bun run ~/sovereign/skills/tau-tmux/helper/audit.ts 2>&1 | tail -1

  # Zero stale references in dependents
  grep -rE '(^|[^a-zA-Z0-9_/])(/bin/tau|/bin/omp|dist/omp)([^a-zA-Z0-9_/]|$)' \
    /tmp/deps-clean.txt 2>/dev/null | wc -l

# OUTPUT

  DONE
  A session:        corrupted=<n> restored=<n> tarball=<yes|no>
  B fork scope:     toxicwind=<n> oh-my-pi=<n> other=<n> remaining_refs=<n>
  C submodules:     forked=<n> newly_forked=<n> missing=<n>
  D upstream merge: applied=<n> auto_upstream=<n> auto_fork=<n> manual=<n> conflicted=<n>
  E reconcile:      exit=<code>
  F build:          <pass|fail> tau=<version>
  G dependents:     scope=<n> stale_fixed=<n> unresolved=<n>
  H skills:         total=<n> mismatched=<n> no_triggers=<n>
  I daemons:        herd=<ok|fail> shep=<ok|fail>
  J verify:         inode_overlap=<n> oh_my_pi_refs=<n> audits=<pass|fail>

Nothing else. No prose after the DONE block.
```

Why this order and not another

A before everything because session corruption is the only thing that can't be undone and might block further work if tau can't read its own history.

B before C because if the scope rename isn't complete, you're about to fork submodules into the wrong scope and the merge in D will reintroduce @oh-my-pi imports that B was supposed to eliminate.

C before D because you can't merge upstream into packages that don't exist locally.

D before E because merge-workspace.ts reads Cargo.toml and package.json after the merge, not before. Running it on the pre-merge tree produces a merge plan that's already stale.

F before G because if the build fails, G is polishing furniture in a burning house.

H and I are parallel-safe — can run in either order, or in separate turns.

What "done" looks like

Five things true at once:

1. tau --version prints a version ≥ 18.3.0
2. grep -r '@oh-my-pi/' ~/sovereign --glob '!**/vendor/**' returns zero
3. No file under ~/sovereign/engine/packages has nlink > 1
4. tau-audit.sh and tau-tmux/helper/audit.ts both exit 0
5. ~/.tau/sessions has no files containing HOME/.local/home/toxic

If any of those is false, the pipeline isn't done regardless of how many phases printed clean.