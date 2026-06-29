FLOX_INSTALL_MULTI_USER=/usr/share/nix/scripts/flox-install-multi-user.sh

is_running_systemd() {
    [ -e /run/systemd/system ] || return 1
    type -p systemctl > /dev/null || return 1
    # Wait 10 seconds for systemd to finish booting.
    deadline="$(( $(date +%s) + 10 ))"
    while ! status="$(systemctl is-system-running)"; do
        echo "WARNING: 'systemctl is-system-running' returned '$status'" >&2
        if [ "$status" = "starting" ] || \
           [ "$status" = "degraded" ] || \
           [ "$status" = "initializing" ]; then
            echo "systemd is starting, proceeding with systemd installation" >&2
            return 0
        fi
        if [ "$(date +%s)" -ge "$deadline" ]; then
            echo "Timed out waiting for systemd to start" >&2
            return 1
        fi
        sleep 1
    done
    return 0
}

is_os_wsl2() {
    case "$(uname -r)" in
        *-WSL2)
            # It's not enough just to be running WSL2, but we also
            # need for the /usr/sbin/service command to be available.
            type -p service > /dev/null;;
        *)
            return 1;;
    esac
}

# Version of install-systemd-multi-user.sh:poly_configure_nix_daemon_service()
# which does not depend upon having installed nix to the default profile.
flox_poly_configure_nix_daemon_service() {
    if is_running_systemd; then
        task "Setting up the nix-daemon systemd service"

        _sudo "to create the nix-daemon tmpfiles config" \
              ln -sfn $NIX_INSTALLED_NIX$TMPFILES_SRC $TMPFILES_DEST

        _sudo "to run systemd-tmpfiles once to pick that path up" \
             systemd-tmpfiles --create --prefix=/nix/var/nix

        _sudo "to disable an already installed nix-daemon" \
              systemctl disable nix-daemon.service || :

        _sudo "to disable an already installed nix-daemon socket" \
              systemctl disable nix-daemon.socket || :

        if [ -e /etc/systemd/system/nix-daemon.service ] || \
           [ -L /etc/systemd/system/nix-daemon.service ] ; then
              _sudo "to remove link to nix-daemon.service" \
                    rm /etc/systemd/system/nix-daemon.service || :
        fi
        if [ -e /etc/systemd/system/nix-daemon.socket ] || \
           [ -L /etc/systemd/system/nix-daemon.socket ] ; then
              _sudo "to remove link to nix-daemon.socket" \
                    rm /etc/systemd/system/nix-daemon.socket || :
        fi

        # N.B. we do NOT invoke `systemctl link` to create a link from /etc/systemd/system
        # because that will mask the service manifest that we have installed to the "vendor"
        # location in /usr/lib/systemd/system. It was a bug for the Nix installer to do this
        # in the first place, because the Nix installer should be considered the "vendor",
        # not the "user".
        # _sudo "to set up the nix-daemon service" \
        #       systemctl link "$NIX_INSTALLED_NIX$SERVICE_SRC"

        _sudo "to set up the nix-daemon socket service" \
              systemctl enable /usr$SOCKET_SRC

        handle_network_proxy

        _sudo "to load the systemd unit for nix-daemon" \
              systemctl daemon-reload

        _sudo "to start the nix-daemon.socket" \
              systemctl start nix-daemon.socket

        _sudo "to start the nix-daemon.service" \
              systemctl restart nix-daemon.service
    elif is_os_wsl2; then
        # Experimental: fall back to sysv init
        # Start by installing init script.
        task "Setting up the nix-daemon systemV service for WSL2"

        # Then set up runlevels.
        for i in /etc/rc{{3,4,5}.d/S,{0,1,2,6}.d/K}01nix-daemon; do
            _sudo "to set up the $i runlevel" \
                ln -f -s ../init.d/nix-daemon $i
        done

        _sudo "to start the nix-daemon service" \
            service nix-daemon start
    else
        reminder "I don't support your init system yet; you may want to add nix-daemon manually."
    fi
}

# SElinux/debugging commands:
#   semanage module -l | grep nix # check if module loaded
#   semanage module -P 300 -r nix # remove nix-daemon module
#   semodule -X 300 --remove=nix  # another way to remove nix-daemon
#   tail -100 /var/log/audit/audit.log | \
#     ausearch -c '(x-daemon)' --raw | audit2allow -M nix
#
# To collect SElinux rules on a completely test system:
#   echo > /var/log/audit/audit.log
#   semodule -X 300 --remove=nix # To build a single set of rules
#   < trigger the selinux violations >
#   cat /var/log/audit/audit.log | audit2allow -m nix
#
# Inspired by https://github.com/NixOS/nix/pull/2670
flox_check_selinux() {
    if test -e /sys/fs/selinux; then
        # Always install the selinux policy to prevent Nix from
        # breaking if it is enabled at a later date.
        if command -v semodule > /dev/null 2>&1; then
            semodule -X 300 -i "/usr/share/selinux/packages/nix.pp"
        fi
        if command -v sestatus restorecon > /dev/null 2>&1; then
            if [ "$(sestatus | awk '/Current mode:/ {print $NF}')" = "enforcing" ]; then
                # this was necessary for the daemon to start successfully on Fedora 37
                restorecon -FR /nix
            fi
        fi
        if command -v systemctl && systemctl is-system-running > /dev/null 2>&1; then
            # Reexec systemd (is this really required?)
            systemctl daemon-reexec
        fi
    fi
}

# Override the `generate_mount_command` from `<nix>/scripts/create-darwin-volume.sh`
# no-op on linux, as its not even run there.
flox_generate_mount_command() {
    : # no-op on linux
}
