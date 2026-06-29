#!/usr/bin/env bash

if [ "$(uname -s)" = "Darwin" -o -e /tmp/flox.install.debug ]; then
    set -x
fi
set -euo pipefail

source /usr/share/flox/include/common.sh
now=$(date +%s)
LOG_FILE=/tmp/flox-installation.log.$now
#########################################################
# Common functions
# TODO use these in after-install.sh and after-upgrade.sh
#########################################################

flox_place_channel_configuration() {
    if [ -z "${NIX_INSTALLER_NO_CHANNEL_ADD:-}" ]; then
        echo "https://github.com/flox/nixpkgs/archive/stable.tar.gz nixpkgs" >"$SCRATCH/.nix-channels"
        _sudo "to set up the default system channel (part 1)" \
            install -m 0664 "$SCRATCH/.nix-channels" "$ROOT_HOME/.nix-channels"
    fi
}

flox_extract_nix() {
    local XZ_PATH="$1"
    tar -C / -xJpf "$XZ_PATH" --no-same-owner
    # Zero out large file rather than removing to prevent package manager
    # from complaining that file disappeared upon package removal.
    dd if=/dev/null of="$XZ_PATH" 2>/dev/null
}

flox_copy_nix() {
    local USR_NIX_DIR="$1"
    tar -C "$USR_NIX_DIR" -xJpf "$USR_NIX_DIR/nix.tar.xz" --no-same-owner
    "$USR_NIX_DIR/old-nix/bin/nix" \
        --extra-experimental-features nix-command \
        --option substitute false \
        copy --from "$USR_NIX_DIR" --all --no-check-sigs

    # Zero out file rather than removing to prevent package manager
    # from complaining that file disappeared upon package removal.
    dd if=/dev/null of="$USR_NIX_DIR/nix.tar.xz" 2>/dev/null
    rm -rf "$USR_NIX_DIR/nix"

    # cleanup after before-install.sh
    rm -f "$USR_NIX_DIR/old-nix"
}

# Apple /etc/zshrc* bugs - see https://github.com/flox/flox/pull/191
flox_patch_darwin_files() {
    # * Mac bash doesn't support associative arrays so we take
    # the more brute-force of always invoking patch and relying on
    # it to exit zero when there is no input.
    # * We also don't want the installation to fail just because
    # we've failed to opportunistically fix the zshrc files, so use
    # the true command to always exit zero.
    # * Would use the --reject-file option to patch but the Mac
    # version is too old and doesn't support "-r -".
    (
        if grep --quiet 'HISTFILE=${ZDOTDIR:-$HOME}/.zsh_history' /etc/zshrc; then
            cat /usr/share/flox/files/darwin-zshrc.patch
        fi
        if grep --quiet 'SHELL_SESSION_DIR="${ZDOTDIR:-$HOME}/.zsh_sessions"' /etc/zshrc_Apple_Terminal; then
            cat /usr/share/flox/files/darwin-zshrc_Apple_Terminal.patch
        fi
    ) | patch -p0 -d / --verbose --backup --suffix=.backup-before-flox || true

    # When we are in a Homebrew install, overrwrite the .pkg update instructions
    if [ -n "${HOMEBREW_PREFIX-}" ]; then
        echo "brew upgrade flox" > /usr/share/flox/files/update-instructions.txt || true
    fi
}

flox_place_nix_configuration() {
    local _singleuser="$1"; shift
    # Start by ensuring that /etc/nix/nix.conf exists by calling Nix's
    # own place_nix_configuration() if it doesn't.
    [ -f /etc/nix/nix.conf ] || place_nix_configuration
    INCLUDE_FLOX="include flox.conf"
    grep -q "$INCLUDE_FLOX" /etc/nix/nix.conf || echo "$INCLUDE_FLOX" >> /etc/nix/nix.conf
    # Single-user mode relies on build-users-group being both defined and empty
    # in /etc/nix/nix.conf. Credit goes to Domen for figuring that out:
    # https://github.com/cachix/install-nix-action/blob/master/install-nix.sh#L58
    if [ "$_singleuser" = "true" ]; then
        sed -i 's/build-users-group =.*/build-users-group =/' /etc/nix/nix.conf
    fi
}

####################################################################################################
# Common functions that we would like to make idempotent upstream
# Wrapping these here instead of calling is_upgrade in main is a bit of premature optimization for
# adding some validation here
####################################################################################################

# whether this script is performing either of
#   - an installation when Nix is already installed
#   - an upgrade on darwin
# Note that Linux upgrades are performed by after-upgrade.sh
is_upgrade() {
    [[ "$IS_UPGRADE" == "true" ]]
}

flox_cure_artifacts() {
    ! is_upgrade && cure_artifacts || true

    # Also take this opportunity to back out any previous nix installation
    # customizations using code borrowed from uninstall_directions().
    for profile_target in "${PROFILE_TARGETS[@]}"; do
        if [ -e "$profile_target" ] && [ -e "$profile_target$PROFILE_BACKUP_SUFFIX" ]; then
            mv $profile_target $profile_target.backup-before-flox
            mv $profile_target$PROFILE_BACKUP_SUFFIX $profile_target
        fi
    done
}

flox_validate_starting_assumptions() {
    # This is a copy of `validate_starting_assumptions()` from the Nix
    # "scripts/install-multi-user.sh" which has been updated to redact
    # the part at the end that aborts the installation when systemd is
    # not found to be running. We do this so that we can preserve this
    # Nix sanity check while allowing our installer to automatically
    # detect and launch into single-user mode installation when necessary.
    task "Checking for artifacts of previous installs"
    cat <<EOF
Before I try to install, I'll check for signs Nix already is or has
been installed on this system.
EOF
    if type -P nix-env >/dev/null; then
        warning <<EOF
Nix already appears to be installed. This installer may run into issues.
If an error occurs, try manually uninstalling, then rerunning this script.

$(uninstall_directions)
EOF
    fi

    # TODO: I think it would be good for this step to accumulate more
    #       knowledge of older obsolete artifacts, if there are any.
    #       We could issue a "reminder" here that the user might want
    #       to clean them up?

    for profile_target in "${PROFILE_TARGETS[@]}"; do
        # TODO: I think it would be good to accumulate a list of all
        #       of the copies so that people don't hit this 2 or 3x in
        #       a row for different files.
        if [ -e "$profile_target$PROFILE_BACKUP_SUFFIX" ]; then
            # this backup process first released in Nix 2.1
            failure <<EOF
I back up shell profile/rc scripts before I add Nix to them.
I need to back up $profile_target to $profile_target$PROFILE_BACKUP_SUFFIX,
but the latter already exists.

Here's how to clean up the old backup file:

1. Back up (copy) $profile_target and $profile_target$PROFILE_BACKUP_SUFFIX
   to another location, just in case.

2. Ensure $profile_target$PROFILE_BACKUP_SUFFIX does not have anything
   Nix-related in it. If it does, something is probably quite
   wrong. Please open an issue or get in touch immediately.

3. Once you confirm $profile_target is backed up and
   $profile_target$PROFILE_BACKUP_SUFFIX doesn't mention Nix, run:
   mv $profile_target$PROFILE_BACKUP_SUFFIX $profile_target
EOF
        fi
    done
    # flox: removed systemd check
}

flox_poly_prepare_to_install() {

  # Run `poly_prepare_to_install` unconditionally to apply update to
  # e.g. the volume mount service.
  #
  # When upgrading run a subset of `prepare_to_install`,
  # that is update the darwin store launch daemon.
  if ! is_upgrade; then
    poly_prepare_to_install
  elif is_os_darwin; then
    # Linux upgrades are handled in after-upgrade.sh, so this isn't reachable on Linux
    # And we only support single user mode on Linux
    # So at this point we must be doing a Darwin multi-user upgrade
    uuid="$(diskutil info -plist /nix | plutil -extract VolumeUUID raw -)"
    device_node="$(diskutil info -plist /nix | plutil -extract DeviceNode raw -)"

    # `setup_volume_daemon` uses `ex` to write the file,
    # but apparently won't update it if already in place.
    if [ -f "$NIX_VOLUME_MOUNTD_DEST" ]; then
      _sudo "to remove the old darwin store daemon at $NIX_VOLUME_MOUNTD_DEST" rm "$NIX_VOLUME_MOUNTD_DEST"
    fi

    if volume_encrypted "$device_node"; then
       setup_volume_daemon "encrypted" "$uuid"
    else
       setup_volume_daemon "unencrypted" "$uuid"
    fi
  fi
}

flox_create_build_group() {
    # The following is idempotent and when upgrading from single
    # user installation the build group and users will not exist.
    create_build_group || true
}

flox_create_build_users() {
    # The following is idempotent and when upgrading from single
    # user installation the build group and users will not exist.
    create_build_users || true
}

# This is a copy of create_directories() from install-multi-user.sh, modified to
# skip the expensive recursive chown.
_flox_create_directories() {
    task "Setting up the basic directory structure"
    # The flox version runs as root from the installer so no need to spend the
    # expense of again chowning the entirety of /nix to root. However when
    # installing over a single-user installation we need to make sure that
    # critical directories are owned by root.
    if [ -d "$NIX_ROOT" ]; then
        local -a NIX_DIRS=( /nix /nix/var /nix/var/log /nix/var/log/nix /nix/var/log/nix/drvs /nix/var/nix{,/db,/gcroots,/profiles,/temproots,/userpool,/daemon-socket} /nix/var/nix/{gcroots,profiles}/per-user )
        # Taken nearly verbatim from nix install-multi-user.sh.
        local get_chr_own="$(PATH="$(getconf PATH 2>/dev/null)" command -vp chown)"
        if [[ -z "$get_chr_own" ]]; then
            get_chr_own="$(command -v chown)"
        fi

        if [[ -z "$get_chr_own" ]]; then
            reminder <<EOF
I wanted to take root ownership of existing Nix store files,
but I couldn't locate 'chown'. (You may need to fix your PATH.)
To manually change file ownership, you can run:
    sudo chown 'root:$NIX_BUILD_GROUP_NAME' "${NIX_DIRS[@]}"
EOF
        else
            # Root is more than capable of setting the appropriate ownership
            # of files over time, but it is the ownership of the "stateDir"
            # /nix/var/nix that triggers the nix client to go in "daemon" mode.
            # See src/libstore/store-api.cc:openFromNonUri() for more details.
            # Ensure this and other critical directories are owned by root.
            _sudo "to take root ownership of existing Nix store files" \
                  "$get_chr_own" "root:$NIX_BUILD_GROUP_NAME" "${NIX_DIRS[@]}" || true
        fi
    fi

    _sudo "to make the basic directory structure of Nix (part 1)" \
          install -dv -m 0755 "${NIX_DIRS[@]}"

    _sudo "to make the basic directory structure of Nix (part 2)" \
          install -dv -g "$NIX_BUILD_GROUP_NAME" -m 1775 /nix/store

    _sudo "to place the default nix daemon configuration (part 1)" \
          install -dv -m 0555 /etc/nix
}

flox_create_directories() {
    # The following is idempotent and when upgrading from single
    # user installation will need to chown directories under /nix.
    _flox_create_directories || true
}

######
# Main
######

# Our version of the upstream main() which only invokes the parts
# that we need. This is factored out into its own function to make
# it easier to incorporate changes from upstream.
function flox_main() {
    # We want the functions from "install-multi-user.sh", but the last 18
    # lines of the script invoke main(), so get rid of those. Also take
    # this opportunity to set EXTRACTED_NIX_PATH required elsewhere.
    (
        cat /usr/share/nix/scripts/install-multi-user.sh |
            awk '/set an empty initial arg for bare invocations/ {exit} {print}' |
            sed -e 's%EXTRACTED_NIX_PATH=.*%EXTRACTED_NIX_PATH="/usr/share/nix/scripts"%'
    ) >"$FLOX_INSTALL_MULTI_USER"
    . "$FLOX_INSTALL_MULTI_USER"

    # The Nix scripts/install-nix-from-closure.sh script either launches
    # into the install-multi-user.sh script or continues with a basic
    # single-user install, duplicating much of the functionality found
    # in the install-multi-user.sh script in the process. We will do
    # different, automatically detecting the need for single-user mode
    # and redacting certain specific actions accordingly.
    if is_os_linux && ! is_running_systemd && ! is_os_wsl2; then
        readonly IS_SINGLEUSER="true"
    else
        readonly IS_SINGLEUSER="false"
    fi

    if is_os_darwin; then
        # shellcheck source=./install-darwin-multi-user.sh
        . "$EXTRACTED_NIX_PATH/install-darwin-multi-user.sh"
    elif is_os_linux; then
        # shellcheck source=./install-systemd-multi-user.sh
        . "$EXTRACTED_NIX_PATH/install-systemd-multi-user.sh" # most of this works on non-systemd distros also
        # override the upstream failure function to call flox_exit_error
        failure() {
            header "oh no!"
            _textout "$RED" "$@"
            echo ""
            _textout "$RED" "$(get_help)"
            flox_exit_error
        }
    else
        failure "Sorry, I don't know what to do on $(uname)"
    fi

    if [ -f /nix/var/nix/db/db.sqlite ]; then
        readonly IS_UPGRADE="true"
        # Update the UID range due to conflicts: https://github.com/NixOS/nix/issues/10892
        if is_os_darwin; then
            # Migrate if some users exist already
            if poly_group_exists "$NIX_BUILD_GROUP_NAME" && [ -z "${FLOX_SKIP_UID_MIGRATIONS-}" ] ; then
                export NIX_FIRST_BUILD_UID=351
                export NIX_BUILD_GROUP_ID=$(poly_group_id_get "$NIX_BUILD_GROUP_NAME")
                /usr/share/flox/scripts/migrate_uids_to_sequoia.sh
                export FLOX_SKIP_UID_MIGRATIONS=1
            fi
        fi
        . /usr/share/flox/include/upgrade.sh
    else
        readonly IS_UPGRADE="false"
        # Update the UID range due to conflicts: https://github.com/NixOS/nix/issues/10892
        if is_os_darwin; then
            export NIX_FIRST_BUILD_UID=351
        fi
        . /usr/share/flox/include/install.sh
    fi

    # Flox backport: https://github.com/NixOS/nix/commit/11d03893f81dc2399ea511e059d8d98676d7d0d0
    # Set profile targets after OS-specific scripts are loaded
    if command -v poly_configure_default_profile_targets > /dev/null 2>&1; then
        # shellcheck disable=SC2207
        PROFILE_TARGETS=($(poly_configure_default_profile_targets))
    else
        # Fallback to defaults if OS-specific function not available
        PROFILE_TARGETS=("/etc/bashrc" "/etc/profile.d/nix.sh" "/etc/zshrc" "/etc/bash.bashrc" "/etc/zsh/zshrc")
    fi

    # welcome_to_nix

    if ! is_root; then
        chat_about_sudo
    fi

    flox_cure_artifacts
    # TODO: there's a tension between cure and validate. I moved the
    # the sudo/root check out of validate to the head of this func.
    # Cure is *intended* to subsume the validate-and-abort approach,
    # so it may eventually obsolete it.
    flox_validate_starting_assumptions

    setup_report

    # dpkg runs scripts interactively
    # if ! ui_confirm "Ready to continue?"; then
    #     ok "Alright, no changes have been made :)"
    #     get_help
    #     trap finish_cleanup EXIT
    #     exit 1
    # fi

    flox_poly_prepare_to_install

    # N.B. the build group and users are not required in single-user
    # mode so long as the "build-users-group" is defined and _empty_
    # in /etc/nix/nix.conf.
    if [ "$IS_SINGLEUSER" = "false" ]; then
        flox_create_build_group
        flox_create_build_users
    fi
    flox_create_directories
    flox_place_channel_configuration
    # place nix configuration before flox_poly_poly_install_nix because it uses experimental features
    flox_place_nix_configuration "$IS_SINGLEUSER"
    # Flox: install_from_extracted_nix not needed; use flox alternative of populating /nix from the flox
    # tarballs.
    flox_poly_poly_install_nix

    # Now that Nix closure has been extracted, set path to prefer
    # tools as provided in installation bundle. (Essential for `sed`.)
    export PATH=/nix/store/74sind1d6vf2bfwd7yklg8chsvzqxmmq-coreutils-9.10/bin:/nix/store/q9mkalz07gwsj77js4q48f4j034f6m8b-daemonize-1.7.8/bin:/nix/store/c89zz4vh8v9dbs8169wk8ahwxvrdxgm5-findutils-4.10.0/bin:/nix/store/jpsqy47rdl0j0dvyyzb4kw8gqajw8nx0-gnused-4.9/bin:$PATH

    # must be performed after install_nix
    flox_check_selinux

    # Flox: configure_shell_profile unwanted since we don't want to modify shell rc files

    # Flox: since we didn't modify /etc/profile we don't need to source it again
    # set +eu
    # # shellcheck disable=SC1091
    # . /etc/profile
    # set -eu

    # Flox: don't install anything to the default profile since we put symlinks to nix paths
    # somewhere under /usr rather than using a profile
    # setup_default_profile
    # performed above: place_nix_configuration
    if [ "$IS_SINGLEUSER" = "false" ]; then
        flox_poly_poly_configure_nix_daemon_service
    fi

    # Extra flox customizations.
    if is_os_darwin; then
        flox_patch_darwin_files
    fi

    # The Nix installer invokes finish_success() which then prints out
    # a list of reminders and soliciting feedback to be sent to the
    # Nix community prior to invoking finish_cleanup(). We don't want
    # to do either of those so we just go straight to the cleanup.
    trap finish_cleanup EXIT
}

# Redirect output to a log file on Linux.
if [ "$(uname -s)" = "Linux" ]; then
    # save stderr to 3 for use in failure()
    exec 3>&2
    # redirect stdout and stderr to $LOG_FILE since the nix installer is so
    # noisy
    exec >> "$LOG_FILE" 2>&1
    # Now that we're logging to a file, be as verbose as you like.
    set -x
    flox_exit_error() {
        # stop being verbose and sending stderr to the log file
        set +x
        exec 2>&3 3>&-
        echo "Installation failed. See $LOG_FILE for logs." 1>&2
        trap finish_cleanup EXIT
        exit 1
    }
    trap flox_exit_error ERR
fi

# Invoke just the parts of main() that we want.
flox_main

exit 0
