source /usr/share/flox/include/common.sh

flox_poly_poly_install_nix() {
    tar -C / -xJpf /usr/share/nix/var.tar.xz --no-same-owner
    flox_copy_nix /usr/share/nix
}

flox_poly_poly_configure_nix_daemon_service() {
    # Unload nix-daemon on Darwin prior to reconfiguring.
    if is_os_darwin; then
        launchctl unload "$NIX_DAEMON_DEST"
    fi
    # passes -k to kickstart so this should restart the daemon
    flox_poly_configure_nix_daemon_service
}


# Override the `generate_mount_command` from `<nix>/scripts/create-darwin-volume.sh`
generate_mount_command() {
    flox_generate_mount_command "$@"
}
