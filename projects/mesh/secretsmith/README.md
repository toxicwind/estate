# secretsmith

Maximal freedesktop Secret Service CLI for the estate. Fork lineage:
[GNOME/libsecret](https://github.com/GNOME/libsecret) (`secret-tool`), forked to
[toxicwind/libsecret](https://github.com/toxicwind/libsecret) — this tool
reimplements and maximalizes `secret-tool`'s D-Bus semantics in Python.

Born from a real bug: a Chromium `os_crypt` key lookup filtered on
`xdg:schema org.freedesktop.Secret.Generic` — a schema Chromium never uses —
and came back empty. `secretsmith` makes that impossible: default search has no
schema filter, and `--schema` resolves through the known-schema registry
(`schemas.json`).

## Install

Deps: `python3`, `dbus-python`, `cryptography` (for the Chromium pipeline).

```bash
# yote launcher (mesh checkout at /home/toxic/sovereign):
ln -sf /home/toxic/sovereign/projects/mesh/secretsmith/bin/secretsmith \
       ~/.local/bin/secretsmith
```

`bin/secretsmith` defaults `DBUS_SESSION_BUS_ADDRESS` to the user's session bus
when unset.

## Usage

```bash
# health: service reachable, default collection unlocked, Chromium entry readable
secretsmith check

# search everything (no schema filter — the original bug is impossible)
secretsmith search --attr application=chromium

# schema-aware search via the registry
secretsmith search --schema chromium
secretsmith search --schema generic --attr foo=bar

# get exactly one item (errors on 0 or >1 matches)
secretsmith get --attr xdg:schema=org.freedesktop.Secret.Generic --show

# store (secret from stdin or --secret-file; never from argv)
echo -n "s3cr3t" | secretsmith set --label "my api key" --attr service=example
secretsmith set --label k --attr service=ex --secret-file /run/key --replace

# delete (two-step unless --yes)
secretsmith delete --attr service=example --yes

# collections
secretsmith collections
secretsmith collection-create ops --alias default
secretsmith lock default / unlock default

# registry
secretsmith schemas

# Chromium/Chrome os_crypt pipeline (the use case that started this)
# NOTE: the raw os_crypt key is never printed -- check/attrs are metadata-only
secretsmith check                        # key metadata: byte count, AES key candidates
secretsmith chromium-logins              # decrypt ~/.config/chromium/Default/Login Data
secretsmith chromium-logins --profile-dir /path/to/profile --show
secretsmith chromium-cookies

# JSON mode for everything (scriptable)
secretsmith --json search --schema chromium
```

## Safety

Secrets are **never printed without `--show`**. Listings show
`<redacted: N bytes>`. Binary secrets print as base64 under `--show`.
`set` reads from stdin/`--secret-file`, never argv (no `ps` leakage).

The Chromium os_crypt key (`secret_is_key` schemas in `schemas.json`) is
**never printed on any path** -- not with `--show`, not as JSON. `get` /
`search --show` on such an item is refused with an error *before* the secret
is even fetched. Decrypt operations (`chromium-logins`, `chromium-cookies`)
consume the key internally and never emit it.

## Schema registry

`schemas.json` maps friendly names to `xdg:schema` values. `chrome` is an
alias of `chromium` (`chrome_libsecret_os_crypt_password_v2`); `generic` is
`org.freedesktop.Secret.Generic` — explicitly documented as *not* what
Chromium uses. Unregistered raw schema strings still work but warn.

## Tests

```bash
python3 -m unittest discover -s tests -v          # unit tests (no keyring needed)
SSM_TEST_KEYRING=1 python3 -m unittest discover -s tests -v   # + live D-Bus integration
```

The integration test creates a throwaway collection, round-trips an item, and
deletes the collection.

## Layout

```text
secretsmith/
├── secretsmith.py   # the CLI (single file)
├── schemas.json     # known-schema registry
├── bin/secretsmith  # launcher (PATH install target)
├── tests/test_secretsmith.py
└── README.md
```

## Compat shim

`compat-chromium-keyring.sh` is the source of the old `/home/toxic/.local/bin/chromium-keyring`
stopgap, now a thin shim over secretsmith (`check` → `secretsmith check`,
`attrs` → `secretsmith search --schema chromium`). The old `key` subcommand was
removed — the raw os_crypt secret is never printed.
One truth lives in secretsmith; the shim exists for muscle memory only.
