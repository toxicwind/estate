#!/usr/bin/env bash
#
# firefox-rs-repair.sh — maximal, future-proof Firefox Remote Settings repair
#
# What it does:
#   1. Discovers every Firefox profile dynamically (parses profiles.ini, falls
#      back to directory scan — never a hard-coded profile name).
#   2. Removes poisoned Remote Settings / Normandy prefs (the
#      `data:,#remote-settings-dummy/v1` test-fixture URL and blank
#      `app.normandy.api_url`) from prefs.js — but ONLY when Firefox is not
#      holding that profile (Firefox rewrites prefs.js on shutdown, so editing
#      a live prefs.js is both racy and pointless).
#   3. Installs enforcement in user.js (read by Firefox at every startup, never
#      written by Firefox), so the correct server URLs win on every launch even
#      if prefs.js ever regains a bad value.
#   4. Deploys /etc/firefox/policies/policies.json (+ README) from the repo.
#   5. Verifies everything (--verify), with a sync-freshness report.
#   6. --install deploys durability: a pacman hook (re-applies after every
#      firefox-nightly upgrade, since package-owned files get overwritten) and
#      a systemd.path unit (event-driven re-apply if policy files change —
#      no timers, no polling).
#
# Safety:
#   - Never kills, restarts, or signals Firefox. Ever.
#   - No pgrep/pkill. A running profile is detected via the profile's own
#     `lock` symlink (points at 127.0.0.1:+<pid>), kill -0 tested.
#   - Idempotent: re-running changes nothing when state is already correct.
#   - --dry-run prints every mutation without applying it.
#   - Durable backups under /var/lib/firefox-rs-repair/backups/<utc-ts>/
#     (never /tmp), with a manifest.
#
# Usage:
#   firefox-rs-repair.sh [--repair] [--verify] [--dry-run] [--install] [--hook]
#                        [--user NAME] [--all-users] [--quiet]
#
set -euo pipefail

VERSION="2.0.0"
PROG="$(basename "$0")"

# --- Canonical good values -------------------------------------------------
# These are Mozilla's own defaults (see services/settings/Utils.sys.mjs and
# toolkit/components/normandy/lib/NormandyApi.sys.mjs in mozilla-central).
# Pinning them in user.js equals "use the default" while defeating any stale
# override that might reappear in prefs.js.
RS_SERVER_DEFAULT="https://firefox.settings.services.mozilla.com/v1"
NORMANDY_API_DEFAULT="https://normandy.cdn.mozilla.net/api/v1"

# Extra enterprise policies merged into /etc/firefox/policies/policies.json.
# Baseline keeps DisableAppUpdate (nightly is pacman-managed on this box).
# DisableFirefoxStudies is intentionally NOT set here: research (2026-09-21)
# showed it disallows the "Shield" feature which gates Normandy recipes
# including emergency remediation — see README.md for the full trace.
# Override with env EXTRA_POLICIES_JSON='{"DisableFoo":true}' if needed.
EXTRA_POLICIES_JSON="${EXTRA_POLICIES_JSON:-{}}"

BACKUP_ROOT="/var/lib/firefox-rs-repair/backups"
LOG_FILE="/var/log/firefox-rs-repair.log"
POLICIES_DIR="/etc/firefox/policies"
REPO_POLICIES_SRC="${REPO_POLICIES_SRC:-}"   # set by --install to repo path

MODE="repair"
DRY_RUN=0
QUIET=0
ONLY_USER=""
ALL_USERS=0
FROM_HOOK=0

CHANGED=0   # set to 1 whenever a real mutation happens

# --- logging ----------------------------------------------------------------
log()  { [ "$QUIET" -eq 1 ] && return 0; printf '%s\n' "$*"; }
vlog() { [ "$QUIET" -eq 1 ] && return 0; printf '  %s\n' "$*"; }
log_to_file() { { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >>"$LOG_FILE"; } 2>/dev/null || true; }
note_change() { CHANGED=1; log_to_file "CHANGE: $*"; log "  [changed] $*"; }

die() { printf '%s: ERROR: %s\n' "$PROG" "$*" >&2; exit 1; }

# --- argument parsing --------------------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        --repair)  MODE="repair" ;;
        --verify)  MODE="verify" ;;
        --install) MODE="install" ;;
        --hook)    MODE="repair"; FROM_HOOK=1 ;;
        --dry-run) DRY_RUN=1 ;;
        --quiet)   QUIET=1 ;;
        --user)    ONLY_USER="${2:?--user needs a name}"; shift ;;
        --all-users) ALL_USERS=1 ;;
        -h|--help)
            sed -n '2,/^#$/p' "$0" | sed 's/^# \?//'; exit 0 ;;
        *) die "unknown argument: $1 (see --help)" ;;
    esac
    shift
done

[ "$(id -u)" -eq 0 ] || { [ "$MODE" = "verify" ] || [ "$DRY_RUN" -eq 1 ]; } \
    || die "must run as root for --repair/--install (use --verify or --dry-run as non-root)"

# --- backups -----------------------------------------------------------------
TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="$BACKUP_ROOT/$TS"
MANIFEST=""

backup_file() {
    # backup_file <path> — copies path into the backup dir (once per run)
    local src="$1" rel dest
    [ -e "$src" ] || return 0
    case "$MANIFEST" in *"$src"*) return 0;; esac
    rel="${src#/}"; rel="${rel//\//__}"
    dest="$BACKUP_DIR/$rel"
    if [ "$DRY_RUN" -eq 1 ]; then
        vlog "(dry-run) would back up $src"
    else
        mkdir -p "$BACKUP_DIR"
        cp -a "$src" "$dest"
        printf '%s\t%s\n' "$src" "$dest" >>"$BACKUP_DIR/MANIFEST.tsv"
        MANIFEST="$MANIFEST $src"
    fi
}

# --- profile discovery --------------------------------------------------------
# Parses profiles.ini properly (IsRelative, Path) instead of globbing names.
discover_profiles() {
    local homes=() h ini line path isrel section
    if [ -n "$ONLY_USER" ]; then
        homes=("/home/$ONLY_USER")
    elif [ "$ALL_USERS" -eq 1 ] || [ -z "$ONLY_USER" ]; then
        for h in /home/* /root; do
            [ -d "$h/.mozilla" ] && homes+=("$h")
        done
    fi
    for h in "${homes[@]}"; do
        [ -d "$h" ] || continue
        ini="$h/.mozilla/firefox/profiles.ini"
        if [ -f "$ini" ]; then
            section=""; path=""; isrel=""
            while IFS= read -r line || [ -n "$line" ]; do
                case "$line" in
                    \[Profile*\]) section="profile"; path=""; isrel="";;
                    \[*\]) section="";;
                    Path=*) [ "$section" = "profile" ] && path="${line#Path=}" ;;
                    IsRelative=*) [ "$section" = "profile" ] && isrel="${line#IsRelative=}" ;;
                esac
                if [ "$section" = "profile" ] && [ -n "$path" ] && [ -n "$isrel" ]; then
                    if [ "$isrel" = "1" ]; then
                        printf '%s\n' "$h/.mozilla/firefox/$path"
                    else
                        printf '%s\n' "$path"
                    fi
                    section=""; path=""; isrel=""
                fi
            done <"$ini"
        fi
        # Fallback: any directory that looks like a profile with a prefs.js
        for d in "$h"/.mozilla/firefox/*.default* "$h"/.mozilla/firefox/*.dev-edition*; do
            [ -d "$d" ] && [ -f "$d/prefs.js" ] && printf '%s\n' "$d"
        done
    done | sort -u
}

profile_locked_pid() {
    # Prints the PID holding the profile lock, or nothing.
    local profile="$1" target pid
    [ -L "$profile/lock" ] || return 0
    target="$(readlink "$profile/lock" 2>/dev/null || true)"
    # target looks like: 127.0.0.1:+3714
    pid="${target##*:+}"
    case "$pid" in
        ''|*[!0-9]*) return 0 ;;
    esac
    if kill -0 "$pid" 2>/dev/null; then
        printf '%s' "$pid"
    fi
    return 0
}

# --- prefs.js / user.js repair -------------------------------------------------
# Poison patterns:
POISON_RS='user_pref\("services\.settings\.server", "data:'   # any data: URL (test fixture)
POISON_RS_EXACT='data:,#remote-settings-dummy/v1'
POISON_NORMANDY_BLANK='user_pref\("app\.normandy\.api_url", ""\)'

clean_prefs_js() {
    # clean_prefs_js <profile> — only called when Firefox is NOT holding it.
    local profile="$1" prefs="$profile/prefs.js" tmp removed=0
    [ -f "$prefs" ] || return 0
    if grep -qE "$POISON_RS|$POISON_NORMANDY_BLANK" "$prefs"; then
        backup_file "$prefs"
        tmp="$(mktemp)"
        grep -vE "$POISON_RS|$POISON_NORMANDY_BLANK" "$prefs" >"$tmp" || true
        if [ "$DRY_RUN" -eq 1 ]; then
            vlog "(dry-run) would remove poisoned lines from $prefs:"
            grep -E "$POISON_RS|$POISON_NORMANDY_BLANK" "$prefs" | sed 's/^/    /'
            rm -f "$tmp"
        else
            # sanity: never write an empty prefs.js
            if [ -s "$tmp" ]; then
                cat "$tmp" >"$prefs"
                note_change "removed poisoned prefs from $prefs"
            else
                vlog "REFUSED to empty $prefs (filter matched everything?)"
                log_to_file "REFUSED to empty $prefs"
            fi
            rm -f "$tmp"
        fi
        removed=1
    fi
    # Warn (don't auto-fix) on a non-data:, non-default custom server — the
    # operator may have set it on purpose (self-hosted RS).
    local srv
    srv="$(grep -oE 'user_pref\("services\.settings\.server", "[^"]*"\)' "$prefs" 2>/dev/null | head -1 || true)"
    if [ -n "$srv" ]; then
        case "$srv" in
            *"$RS_SERVER_DEFAULT"*) ;;
            *) vlog "NOTE: custom services.settings.server left alone: $srv"
               log_to_file "NOTE custom RS server left alone in $prefs: $srv" ;;
        esac
    fi
    return 0
}

enforce_user_js() {
    # enforce_user_js <profile> — idempotent user.js pinning of good values.
    # Safe while Firefox runs: Firefox reads user.js only at startup.
    local profile="$1" ujs="$profile/user.js" tmp key val
    [ -d "$profile" ] || return 0
    for key in "services.settings.server" "app.normandy.api_url"; do
        case "$key" in
            services.settings.server) val="$RS_SERVER_DEFAULT" ;;
            app.normandy.api_url)     val="$NORMANDY_API_DEFAULT" ;;
        esac
        if [ -f "$ujs" ] && grep -qF "user_pref(\"$key\", \"$val\");" "$ujs"; then
            continue  # already enforced
        fi
        backup_file "$ujs"
        if [ "$DRY_RUN" -eq 1 ]; then
            vlog "(dry-run) would enforce in $ujs: user_pref(\"$key\", \"$val\");"
        else
            tmp="$(mktemp)"
            if [ -f "$ujs" ]; then
                grep -vF "user_pref(\"$key\"," "$ujs" >"$tmp" || true
            else
                : >"$tmp"
            fi
            printf 'user_pref("%s", "%s");\n' "$key" "$val" >>"$tmp"
            # keep original owner/perms when replacing
            if [ -f "$ujs" ]; then
                cat "$tmp" >"$ujs"
            else
                cat "$tmp" >"$ujs"
                owner="$(stat -c %U "$profile")"
                chown "$owner:$owner" "$ujs" 2>/dev/null || true
                chmod 644 "$ujs"
            fi
            rm -f "$tmp"
            note_change "enforced $key in $ujs"
        fi
    done
}

repair_one_profile() {
    local profile="$1" pid
    [ -d "$profile" ] || return 0
    pid="$(profile_locked_pid "$profile")"
    if [ -n "$pid" ]; then
        vlog "profile $profile is LIVE (pid $pid): prefs.js untouched, user.js enforced"
        log_to_file "profile $profile live (pid $pid): prefs.js skipped"
        enforce_user_js "$profile"
    else
        vlog "profile $profile is idle: cleaning prefs.js + enforcing user.js"
        clean_prefs_js "$profile"
        enforce_user_js "$profile"
    fi
}

# --- enterprise policies -------------------------------------------------------
# policies.json is built by merging: repo baseline + EXTRA_POLICIES_JSON.
# python3 is required for the merge (no hand-rolled JSON).
write_policies() {
    local dest="$POLICIES_DIR/policies.json" baseline tmp merged
    command -v python3 >/dev/null || die "python3 required for policy merge"
    baseline='{"policies":{"DisableAppUpdate":true}}'
    tmp="$(mktemp)"
    EXTRA_POLICIES_JSON="$EXTRA_POLICIES_JSON" BASELINE="$baseline" python3 - "$dest" >"$tmp" <<'EOF'
import json, os, sys
dest = sys.argv[1]
base = json.loads(os.environ["BASELINE"])
extra = json.loads(os.environ.get("EXTRA_POLICIES_JSON") or "{}")
pols = dict(base.get("policies", {}))
pols.update(extra if isinstance(extra, dict) else {})
out = {"policies": pols}
cur = {}
try:
    with open(dest) as f:
        cur = json.load(f)
except Exception:
    pass
if cur == out:
    print("UNCHANGED")
else:
    print(json.dumps(out, indent=2, sort_keys=True))
EOF
    merged="$(cat "$tmp"; rm -f "$tmp")"
    if [ "$merged" = "UNCHANGED" ]; then
        vlog "policies.json already correct"
        return 0
    fi
    backup_file "$dest"
    if [ "$DRY_RUN" -eq 1 ]; then
        vlog "(dry-run) would write $dest:"
        printf '%s\n' "$merged" | sed 's/^/    /'
    else
        mkdir -p "$POLICIES_DIR"
        printf '%s\n' "$merged" >"$dest"
        chmod 644 "$dest"
        note_change "wrote $dest"
    fi
}

write_policies_readme() {
    local dest="$POLICIES_DIR/README.md"
    [ -n "$REPO_POLICIES_SRC" ] || return 0
    local src="$REPO_POLICIES_SRC/README.md"
    [ -f "$src" ] || { vlog "no repo README at $src, skipping"; return 0; }
    if [ -f "$dest" ] && cmp -s "$src" "$dest"; then
        vlog "policies README already deployed"
        return 0
    fi
    backup_file "$dest"
    if [ "$DRY_RUN" -eq 1 ]; then
        vlog "(dry-run) would deploy $src -> $dest"
    else
        cp -a "$src" "$dest"
        chmod 644 "$dest"
        note_change "deployed policies README"
    fi
}

# --- distribution dir check ------------------------------------------------------
check_distribution() {
    # /usr/lib/firefox*/distribution is package-owned; a stray policies.json
    # there could fight /etc. Report, don't auto-delete package files.
    local d f
    for d in /usr/lib/firefox-nightly/distribution /usr/lib/firefox/distribution; do
        f="$d/policies.json"
        if [ -f "$f" ]; then
            if grep -q "remote-settings-dummy" "$f" 2>/dev/null; then
                vlog "POISON in package file $f (package-owned; needs hook/overlay handling)"
                log_to_file "POISON in package file $f"
            else
                vlog "distribution policies present: $f (review manually)"
                log_to_file "distribution policies present: $f"
            fi
        fi
    done
}

# --- durability: install script, pacman hook, systemd path unit -----------------
SELF_SRC="$(readlink -f "$0")"
DEPLOY_BIN="/usr/local/bin/firefox-rs-repair"
HOOK_FILE="/usr/share/libalpm/hooks/firefox-rs-repair.hook"
PATH_UNIT="/etc/systemd/system/firefox-rs-repair.path"
SVC_UNIT="/etc/systemd/system/firefox-rs-repair.service"

do_install() {
    # 1. Deploy this script to a durable root-owned location.
    backup_file "$DEPLOY_BIN"
    if [ "$DRY_RUN" -eq 1 ]; then
        vlog "(dry-run) would install $SELF_SRC -> $DEPLOY_BIN"
    else
        cp -a "$SELF_SRC" "$DEPLOY_BIN"
        chmod 755 "$DEPLOY_BIN"
        note_change "installed $DEPLOY_BIN"
    fi

    # 2. Pacman hook: re-apply after every firefox-nightly install/upgrade,
    #    because package-owned files (distribution/, defaults/) get overwritten.
    local hook_content
    hook_content="[Trigger]
Operation = Install
Operation = Upgrade
Type = Package
Target = firefox-nightly
Target = firefox

[Action]
Description = Re-apply Firefox Remote Settings repair after upgrade...
When = PostTransaction
Exec = $DEPLOY_BIN --hook --quiet
NeedsTargets
"
    if [ ! -f "$HOOK_FILE" ] || ! cmp -s <(printf '%s' "$hook_content") "$HOOK_FILE"; then
        backup_file "$HOOK_FILE"
        if [ "$DRY_RUN" -eq 1 ]; then
            vlog "(dry-run) would write pacman hook $HOOK_FILE"
        else
            printf '%s' "$hook_content" >"$HOOK_FILE"
            chmod 644 "$HOOK_FILE"
            note_change "installed pacman hook $HOOK_FILE"
        fi
    else
        vlog "pacman hook already installed"
    fi

    # 3. systemd.path unit: event-driven re-apply when policy files change.
    #    No timers, no polling — the kernel notifies us.
    local path_content svc_content
    path_content="[Unit]
Description=Watch Firefox enterprise policies for drift

[Path]
PathModified=$POLICIES_DIR/policies.json
Unit=firefox-rs-repair.service

[Install]
WantedBy=multi-user.target
"
    svc_content="[Unit]
Description=Re-apply Firefox Remote Settings repair on policy drift

[Service]
Type=oneshot
ExecStart=$DEPLOY_BIN --repair --quiet
"
    for unit in "$PATH_UNIT:$path_content" "$SVC_UNIT:$svc_content"; do
        local f="${unit%%:*}" want="${unit#*:}"
        if [ ! -f "$f" ] || ! cmp -s <(printf '%s' "$want") "$f"; then
            backup_file "$f"
            if [ "$DRY_RUN" -eq 1 ]; then
                vlog "(dry-run) would write $f"
            else
                printf '%s' "$want" >"$f"
                chmod 644 "$f"
                note_change "installed $f"
            fi
        else
            vlog "$(basename "$f") already installed"
        fi
    done
    if [ "$DRY_RUN" -eq 0 ]; then
        systemctl daemon-reload 2>/dev/null || true
        systemctl enable --now firefox-rs-repair.path 2>/dev/null \
            && vlog "enabled firefox-rs-repair.path" \
            || vlog "could not enable path unit (non-systemd environment?)"
    else
        vlog "(dry-run) would daemon-reload + enable firefox-rs-repair.path"
    fi
}

# --- verification ----------------------------------------------------------------
FAILURES=0
fail() { FAILURES=$((FAILURES+1)); printf 'FAIL: %s\n' "$*"; log_to_file "VERIFY FAIL: $*"; }
pass() { vlog "ok: $*"; }

do_verify() {
    local profile prefs ujs now newest age
    log "== $PROG --verify =="
    # 1. policies.json parses and has required policies
    if [ -f "$POLICIES_DIR/policies.json" ]; then
        if python3 -c "import json,sys; d=json.load(open('$POLICIES_DIR/policies.json')); assert d['policies']['DisableAppUpdate'] is True" 2>/dev/null; then
            pass "policies.json valid, DisableAppUpdate=true"
        else
            fail "policies.json invalid or missing DisableAppUpdate"
        fi
    else
        fail "policies.json missing at $POLICIES_DIR/policies.json"
    fi
    # 2. no poison anywhere
    while IFS= read -r profile; do
        [ -d "$profile" ] || continue
        for f in "$profile/prefs.js" "$profile/user.js"; do
            if [ -f "$f" ] && grep -q "remote-settings-dummy" "$f"; then
                fail "poison string present in $f"
            fi
        done
        # 3. user.js enforcement present
        ujs="$profile/user.js"
        for key in "services.settings.server" "app.normandy.api_url"; do
            if [ -f "$ujs" ] && grep -qF "user_pref(\"$key\"," "$ujs"; then
                pass "$profile: user.js enforces $key"
            else
                fail "$profile: user.js missing enforcement for $key"
            fi
        done
        # 4. sync freshness (informational): newest RS last_check vs now
        prefs="$profile/prefs.js"
        if [ -f "$prefs" ]; then
            newest="$(grep -oE 'services\.settings\.(main\.[a-z0-9-]+|last_update_seconds)[^,]*, [0-9]+' "$prefs" 2>/dev/null \
                | grep -oE '[0-9]+$' | sort -n | tail -1 || true)"
            now="$(date -u +%s)"
            if [ -n "$newest" ]; then
                age=$(( (now - newest) / 3600 ))
                if [ "$age" -gt 48 ]; then
                    vlog "NOTE: $profile newest RS sync ${age}h ago ($(date -u -d "@$newest" +%FT%TZ)) — no successful sync in 48h"
                    log_to_file "VERIFY NOTE: $profile RS sync ${age}h stale"
                else
                    pass "$profile: RS sync ${age}h ago (fresh)"
                fi
            else
                vlog "NOTE: $profile has no RS last_check markers"
            fi
        fi
    done < <(discover_profiles)
    # 5. durability artifacts
    [ -f "$HOOK_FILE" ] && pass "pacman hook installed" || vlog "NOTE: pacman hook not installed (run --install)"
    if systemctl is-enabled firefox-rs-repair.path >/dev/null 2>&1; then
        pass "path unit enabled"
    else
        vlog "NOTE: firefox-rs-repair.path not enabled (run --install)"
    fi
    if [ "$FAILURES" -gt 0 ]; then
        log "$FAILURES verification FAILURE(S)"
        return 1
    fi
    log "verify: all hard checks passed"
    return 0
}

# --- squawk alert (best-effort, never fatal) ---------------------------------------
maybe_alert() {
    [ "$CHANGED" -eq 1 ] || return 0
    [ "$DRY_RUN" -eq 1 ] && return 0
    local cli=""
    for c in /home/hatch/workspace/bin/squawk "$HOME/workspace/bin/squawk"; do
        [ -x "$c" ] && cli="$c" && break
    done
    if [ -n "$cli" ]; then
        "$cli" send fleet "$PROG corrected Firefox RS/policy drift on $(hostname) (mode=$MODE). See $LOG_FILE." >/dev/null 2>&1 || true
    fi
    # yote-local fallback: drop a message file straight into the squawk root
    local root="/home/toxic/shingle/squawk-root/fleet"
    [ -d "/home/toxic/.shingle/squawk-root/fleet" ] && root="/home/toxic/.shingle/squawk-root/fleet"
    if [ -z "$cli" ] && [ -d "$root" ]; then
        printf -- '---\nfrom: %s\nts: %s\n---\n%s corrected Firefox RS/policy drift on %s (mode=%s). See %s.\n' \
            "$PROG" "$(date -u +%FT%TZ)" "$PROG" "$(hostname)" "$MODE" "$LOG_FILE" \
            >"$root/$PROG-$(date -u +%Y%m%dT%H%M%SZ).md" 2>/dev/null || true
    fi
    return 0
}

# --- main ---------------------------------------------------------------------------
main() {
    log_to_file "run: mode=$MODE dry_run=$DRY_RUN user=${ONLY_USER:-all}"
    case "$MODE" in
        verify)
            do_verify
            ;;
        install)
            do_install
            write_policies
            write_policies_readme
            while IFS= read -r profile; do repair_one_profile "$profile"; done < <(discover_profiles)
            check_distribution
            ;;
        repair)
            write_policies
            write_policies_readme
            while IFS= read -r profile; do repair_one_profile "$profile"; done < <(discover_profiles)
            check_distribution
            ;;
    esac
    maybe_alert
    if [ "$DRY_RUN" -eq 1 ]; then
        log "(dry-run complete — no changes applied)"
    elif [ "$CHANGED" -eq 1 ]; then
        log "done — changes applied (backups in $BACKUP_DIR, log $LOG_FILE)"
    else
        log "done — no drift found, nothing changed"
    fi
}

main "$@"
