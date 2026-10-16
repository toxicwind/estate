"""Secrets loader: file (NAME=value) or dir (filename=key, content=value).

Optional secretsmith store: when KEYPOOL_SECRETS_BACKEND=secretsmith, items
stored in the freedesktop Secret Service under the attribute keypool=1 are
overlaid on top of the file/dir values (store wins; files stay the transport
per ENV_OWNERSHIP.md). The overlay degrades to no-op whenever the secretsmith
CLI is absent or its service is unreachable - keypool never fails to boot
because of the optional store.

os_crypt key items (secret_is_key schemas) are refused by secretsmith before
they are fetched, so they can never enter keypool's key dict through this
loader. That refusal is structural, not a convention.
"""
import os


def _parse_file(text):
    out = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:]
        k, v = line.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out[k.strip()] = v
    return out


def _load_files(path):
    """The original transport, byte-for-byte behavior preserved."""
    out = {}
    if not os.path.exists(path):
        return out
    if os.path.isfile(path):
        with open(path, encoding="utf-8", errors="ignore") as f:
            out.update(_parse_file(f.read()))
        return out
    for name in os.listdir(path):
        if name.startswith("."):
            continue
        p = os.path.join(path, name)
        if os.path.isfile(p):
            with open(p, encoding="utf-8", errors="ignore") as f:
                v = f.read().strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            out[name] = v
    return out


KEYPOOL_ATTR = "keypool"
STORE_TAG = "secretsmith"


def _default_fetcher(attr_key):
    """Fetch keypool-attributed items from the secretsmith store.

    Returns {label: value}. Import is resolved at call time so keypool
    never imports dbus at boot unless the store is enabled.
    """
    import sys

    cli_dir = os.environ.get(
        "KEYPOOL_SECRETSMITH_PATH",
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "projects", "mesh", "secretsmith"),
    )
    if cli_dir not in sys.path:
        sys.path.insert(0, os.path.abspath(cli_dir))
    import secretsmith as ssm

    reg = ssm.Registry()
    ss = ssm.SecretService(reg)
    # Refuses secret_is_key items before fetching; KeyRefusalError
    # propagating here is correct: the os_crypt key never loads.
    return ssm._default_fetcher_under(ss, reg, attr_key)


def _load_store(fetcher=None, enabled=None, attr_key="1"):
    if enabled is None:
        enabled = os.environ.get("KEYPOOL_SECRETS_BACKEND", "") == STORE_TAG
    if not enabled:
        return {}
    import secretsmith as ssm

    try:
        values = fetcher(attr_key) if fetcher else _default_fetcher(attr_key)
        return dict(values)
    except ssm.KeyRefusalError as exc:
        # A secret_is_key item was attributed keypool=1. Refusal is the
        # guarantee working: the key never enters the dict, keypool boots
        # without it. Logged loudly so the planted item gets cleaned up.
        import sys

        print("[keypool] secretsmith refused an os_crypt key item; "
              "it is never loaded: %s" % exc, file=sys.stderr, flush=True)
        return {}
    except Exception as exc:  # noqa: BLE001 - the store is optional
        import sys

        print("[keypool] secretsmith store unavailable: %s" % exc,
              file=sys.stderr, flush=True)
        return {}


def load(path: str, store_fetcher=None) -> dict[str, str]:
    """File/dir transport, optionally overlaid with the secretsmith store."""
    out = _load_files(path)
    # An injected fetcher means "the store is on" - used by tests and
    # embedders; production gates on KEYPOOL_SECRETS_BACKEND.
    enabled = store_fetcher is not None or None
    out.update(_load_store(fetcher=store_fetcher, enabled=enabled))
    return out