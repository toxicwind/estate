source /usr/share/flox/include/common.sh

flox_poly_poly_install_nix() {
    tar -C / -xJpf /usr/share/nix/var.tar.xz --no-same-owner
    flox_extract_nix /usr/share/nix/nix.tar.xz
}

flox_poly_poly_configure_nix_daemon_service() {
    flox_poly_configure_nix_daemon_service
}

# Override the `generate_mount_command` from `<nix>/scripts/create-darwin-volume.sh`
generate_mount_command() {
    flox_generate_mount_command "$@"
}
