  enterTest = ''
    echo "=== Sovereign Stack Tests ==="
    ${pkgs.git}/bin/git --version | grep --color=auto "${pkgs.git.version}"
    ${pkgs.curl}/bin/curl --version | head -1
    ${pkgs.python3}/bin/python3 --version
    ${pkgs.bun}/bin/bun --version
    echo "✓ All core tools present"
  ''