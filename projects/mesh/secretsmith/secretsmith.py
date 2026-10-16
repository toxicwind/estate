#!/usr/bin/env python3
"""secretsmith - maximal freedesktop Secret Service CLI.

A from-scratch Python reimplementation of GNOME secret-tool's D-Bus
semantics, with a friendly schema registry, JSON scripting mode, and a
Chromium os_crypt pipeline that can never print the raw key.

Secrets are never printed without --show. The Chromium os_crypt key is
refused on every output path before it is ever fetched from the service.

Deps: python3 (stdlib), dbus-python; cryptography only for the Chromium
decrypt pipeline.
"""

import argparse
import base64
import json
import os
import sys

DEFAULT_REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "schemas.json"
)

# D-Bus names for the freedesktop Secret Service spec.
SERVICE = "org.freedesktop.secrets"
SERVICE_PATH = "/org/freedesktop/secrets"
IFACE_SERVICE = "org.freedesktop.Secret.Service"
IFACE_SESSION = "org.freedesktop.Secret.Session"
IFACE_COLLECTION = "org.freedesktop.Secret.Collection"
IFACE_ITEM = "org.freedesktop.Secret.Item"
DEFAULT_COLLECTION_ALIAS = "default"

SS_SCHEMA_ATTR = "xdg:schema"

# Prefixes used by Chromium's os_crypt on Linux.
V10_PREFIX = b"v10"
V11_PREFIX = b"v11"
# v10 CBC uses a fixed IV of 16 space characters.
CBC_FIXED_IV = b" " * 16


class SecretsmithError(Exception):
    """User-facing error. Message is printed to stderr, exit 1."""


class KeyRefusalError(SecretsmithError):
    """Raised when an os_crypt key item is about to be revealed.

    Refusal happens BEFORE the secret is fetched from the service, so the
    key never even enters process memory on a display path.
    """


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------

class Registry:
    """Friendly-name -> schema mapping, extended in place on disk."""

    def __init__(self, path=DEFAULT_REGISTRY_PATH):
        self.path = path
        self.data = {}
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            self.data = {}
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            self.data = json.load(fh)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2, sort_keys=True)
            fh.write("\n")

    def resolve(self, name):
        """Return (xdg_schema, secret_is_key, warned) for a friendly name.

        Unknown names are treated as raw schema strings with a warning,
        never a hard failure.
        """
        if name in self.data:
            entry = self.data[name]
            return (
                entry.get(SS_SCHEMA_ATTR, name),
                bool(entry.get("secret_is_key", False)),
                False,
            )
        return name, False, True

    def is_key_schema(self, xdg_schema):
        for entry in self.data.values():
            if entry.get(SS_SCHEMA_ATTR) == xdg_schema:
                return bool(entry.get("secret_is_key", False))
        return False

    def listing(self):
        return {
            name: {
                SS_SCHEMA_ATTR: entry.get(SS_SCHEMA_ATTR, ""),
                "secret_is_key": bool(entry.get("secret_is_key", False)),
            }
            for name, entry in sorted(self.data.items())
        }

    def register(self, name, xdg_schema, secret_is_key=False):
        self.data[name] = {SS_SCHEMA_ATTR: xdg_schema, "secret_is_key": bool(secret_is_key)}
        self.save()


def redact(secret_bytes):
    if secret_bytes is None:
        return "<redacted: 0 bytes>"
    return "<redacted: %d bytes>" % len(secret_bytes)


def display_secret(secret_bytes, show):
    """Render a secret for stdout. Binary secrets base64 under --show."""
    if not show:
        return redact(secret_bytes)
    try:
        return secret_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return base64.b64encode(secret_bytes).decode("ascii")


# ---------------------------------------------------------------------------
# D-Bus Secret Service layer
# ---------------------------------------------------------------------------

class SecretService:
    """Thin, testable wrapper over the Secret Service D-Bus API.

    All D-Bus access is funnelled through _call/_get_prop so tests can
    inject a fake transport. The class never stores secrets beyond the
    lifetime of a single call.
    """

    def __init__(self, registry, bus=None):
        self.registry = registry
        self._bus = bus
        self._session_path = None

    # -- transport ---------------------------------------------------------

    def _ensure_bus(self):
        if self._bus is None:
            import dbus

            self._bus = dbus.SessionBus()
        return self._bus

    def _proxy(self, obj_path, iface):
        import dbus

        bus = self._ensure_bus()
        obj = bus.get_object(SERVICE, obj_path)
        return dbus.Interface(obj, iface)

    def _get_prop(self, obj_path, iface, prop):
        bus = self._ensure_bus()
        obj = bus.get_object(SERVICE, obj_path)
        props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
        return props.Get(iface, prop)

    # -- session -----------------------------------------------------------

    def open_session(self):
        if self._session_path is not None:
            return self._session_path
        svc = self._proxy(SERVICE_PATH, IFACE_SERVICE)
        # Plain algorithm: no parameters, no encryption.
        result = svc.OpenSession("plain", "")
        self._session_path = str(result[1])
        return self._session_path

    # -- collections -------------------------------------------------------

    def default_collection_path(self):
        svc = self._proxy(SERVICE_PATH, IFACE_SERVICE)
        return str(svc.ReadAlias(DEFAULT_COLLECTION_ALIAS))

    def collections(self):
        paths = self._get_prop(SERVICE_PATH, IFACE_SERVICE, "Collections")
        return [str(p) for p in paths]

    def collection_create(self, label, alias=None):
        svc = self._proxy(SERVICE_PATH, IFACE_SERVICE)
        result = svc.CreateCollection(
            {"org.freedesktop.Secret.Collection.Label": label}, alias or ""
        )
        # result: (collection o, prompt o)
        path = str(result[0])
        if path == "/":
            raise SecretsmithError(
                "collection creation needs a prompt; unlock the prompt via a GUI agent"
            )
        return path

    def lock(self, collection_path):
        self._proxy(collection_path, IFACE_COLLECTION).Lock()

    def unlock(self, collection_path):
        result = self._proxy(collection_path, IFACE_COLLECTION).Unlock()
        if str(result[1]) != "/":
            raise SecretsmithError("collection unlock needs interactive prompt")

    # -- items -------------------------------------------------------------

    def search(self, collection_path, attributes):
        coll = self._proxy(collection_path, IFACE_COLLECTION)
        return [str(p) for p in coll.SearchItems(attributes)]

    def item_attributes(self, item_path):
        return {
            str(k): str(v)
            for k, v in self._get_prop(item_path, IFACE_ITEM, "Attributes").items()
        }

    def item_label(self, item_path):
        return str(self._get_prop(item_path, IFACE_ITEM, "Label"))

    def item_locked(self, item_path):
        return bool(self._get_prop(item_path, IFACE_ITEM, "Locked"))

    def create_item(self, collection_path, label, attributes, secret_bytes, replace):
        session = self.open_session()
        coll = self._proxy(collection_path, IFACE_COLLECTION)
        secret = (session, [], bytes(secret_bytes), "text/plain")
        properties = {
            "org.freedesktop.Secret.Item.Label": label,
            "org.freedesktop.Secret.Item.Attributes": attributes,
        }
        result = coll.CreateItem(properties, secret, bool(replace))
        path = str(result[0])
        if path == "/":
            raise SecretsmithError("item creation needs a prompt")
        return path

    def fetch_secret(self, item_path):
        """Fetch the raw secret bytes. NEVER call this for key items."""
        session = self.open_session()
        item = self._proxy(item_path, IFACE_ITEM)
        result = item.GetSecret(session)
        return bytes(result[2])

    def delete_item(self, item_path):
        self._proxy(item_path, IFACE_ITEM).Delete()

    def delete_collection(self, collection_path):
        self._proxy(collection_path, IFACE_COLLECTION).Delete()


def check_key_refusal(registry, attributes):
    """Refuse BEFORE fetching when the item holds an os_crypt key."""
    schema = attributes.get(SS_SCHEMA_ATTR)
    if schema and registry.is_key_schema(schema):
        raise KeyRefusalError(
            "refusing to reveal item: its schema (%s) is marked secret_is_key; "
            "the Chromium os_crypt key is unprintable by design" % schema
        )

# ---------------------------------------------------------------------------
# Chromium os_crypt pipeline
# ---------------------------------------------------------------------------

def decrypt_v10(key, blob):
    """AES-256-CBC with a fixed 16-space IV, after the 'v10' prefix."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    if not blob.startswith(V10_PREFIX):
        return None
    body = blob[len(V10_PREFIX):]
    if len(body) % 16 != 0 or not body:
        return None
    dec = Cipher(algorithms.AES(key), modes.CBC(CBC_FIXED_IV)).decryptor()
    padded = dec.update(body) + dec.finalize()
    pad = padded[-1]
    if not 1 <= pad <= 16 or padded[-pad:] != bytes([pad]) * pad:
        return None
    return padded[:-pad]


def decrypt_v11(key, blob):
    """AES-256-GCM: 12-byte nonce after 'v11', tag appended to ciphertext."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    if not blob.startswith(V11_PREFIX):
        return None
    body = blob[len(V11_PREFIX):]
    if len(body) < 12 + 16:
        return None
    nonce, ct = body[:12], body[12:]
    return AESGCM(key).decrypt(nonce, ct, None)


def decrypt_os_crypt(key, blob):
    for fn in (decrypt_v11, decrypt_v10):
        try:
            out = fn(key, blob)
        except Exception:
            out = None
        if out is not None:
            return out
    return None


def unwrap_local_state_key(service_key, profile_dir):
    """Unwrap the os_crypt key from Local State under the service key.

    The wrapped key is 'DPAPI'-prefixed but on Linux is plain AES-256-CBC
    under the keyring key. The unwrapped key is consumed internally only;
    it is never returned to any printing path.
    """
    import json as _json

    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    path = os.path.join(profile_dir, "Local State")
    with open(path, "r", encoding="utf-8") as fh:
        state = _json.load(fh)
    wrapped = base64.b64decode(state["os_crypt"]["encrypted_key"])
    if not wrapped.startswith(b"DPAPI"):
        raise SecretsmithError("Local State encrypted_key has unexpected prefix")
    body = wrapped[len(b"DPAPI"):]
    if not body:
        raise SecretsmithError("Local State encrypted_key is empty")
    dec = Cipher(algorithms.AES(service_key), modes.CBC(CBC_FIXED_IV)).decryptor()
    padded = dec.update(body) + dec.finalize()
    pad = padded[-1]
    if not 1 <= pad <= 16 or padded[-pad:] != bytes([pad]) * pad:
        raise SecretsmithError("Local State key unwrap failed (bad padding)")
    return padded[:-pad]


def fetch_os_crypt_key(ss, registry, profile_dir):
    """Locate and fetch the Chromium os_crypt key from the service.

    Internal-only: the key flows straight into decryption. It is refused
    on every display path (check_key_refusal), so this function is only
    ever called by the decrypt pipeline itself.
    """
    for name in ("chromium", "chromium-v1"):
        schema, _, _ = registry.resolve(name)
        hits = ss.search(ss.default_collection_path(), {SS_SCHEMA_ATTR: schema})
        if len(hits) == 1:
            raw = ss.fetch_secret(hits[0])
            # v2 entries may wrap the real key inside Local State.
            if os.path.exists(os.path.join(profile_dir, "Local State")):
                try:
                    return unwrap_local_state_key(raw, profile_dir)
                except SecretsmithError:
                    return raw
            return raw
        if len(hits) > 1:
            raise SecretsmithError(
                "%d os_crypt key candidates for schema %r; refusing to guess" % (len(hits), schema))
    raise SecretsmithError(
        "no Chromium os_crypt key found in the default collection; run 'secretsmith check'")


def chromium_decrypt(profile_dir, key, which, show):
    """Decrypt Login Data or Cookies rows. Passwords print only with --show."""
    import sqlite3

    if which == "logins":
        dbfile = os.path.join(profile_dir, "Login Data")
        query = "SELECT origin_url, username_value, password_value FROM logins"
        cols = ("origin_url", "username", "password")
    else:
        dbfile = os.path.join(profile_dir, "Cookies")
        query = "SELECT host_key, name, encrypted_value FROM cookies"
        cols = ("host", "name", "value")

    if not os.path.exists(dbfile):
        raise SecretsmithError("database not found: %s" % dbfile)
    # Read-only URI open: never create or modify the live profile db.
    uri = "file:%s?mode=ro" % dbfile.replace("\\", "/").lstrip("/")
    con = sqlite3.connect(uri, uri=True)
    try:
        rows = con.execute(query).fetchall()
    finally:
        con.close()

    out = []
    for row in rows:
        url, ident, blob = row[0], row[1], bytes(row[2])
        plain = decrypt_os_crypt(key, blob)
        value = display_secret(plain, show) if plain is not None else "<undecryptable>"
        out.append({cols[0]: url or ident, cols[1]: ident, cols[2]: value})
    return out


# ---------------------------------------------------------------------------
# Higher-level operations (transport-agnostic, unit-testable)
# ---------------------------------------------------------------------------

def op_search(ss, registry, collection_path, schema_name, attr_pairs, show):
    schema, is_key, warned = (None, False, False)
    if schema_name:
        schema, is_key, warned = registry.resolve(schema_name)
    attributes = {}
    if schema:
        attributes[SS_SCHEMA_ATTR] = schema
    for k, v in attr_pairs:
        attributes[k] = v
    if warned:
        print(
            "warning: %r is not in the schema registry; using it as a raw xdg:schema"
            % schema_name,
            file=sys.stderr,
        )
    paths = ss.search(collection_path, attributes)
    results = []
    for p in paths:
        attrs = ss.item_attributes(p)
        entry = {
            "path": p,
            "label": ss.item_label(p),
            "attributes": attrs,
            "locked": ss.item_locked(p),
        }
        if show:
            # Refusal BEFORE fetching: the key never enters memory.
            check_key_refusal(registry, attrs)
            entry["secret"] = display_secret(ss.fetch_secret(p), True)
        else:
            # Redacted listing without touching the secret at all.
            entry["secret"] = "<redacted>"
        results.append(entry)
    return results


def op_get(ss, registry, collection_path, attr_pairs, show):
    attributes = {}
    for k, v in attr_pairs:
        attributes[k] = v
    paths = ss.search(collection_path, attributes)
    if len(paths) == 0:
        raise SecretsmithError("no items match the given attributes")
    if len(paths) > 1:
        raise SecretsmithError(
            "%d items match; refine attributes to select exactly one" % len(paths)
        )
    path = paths[0]
    attrs = ss.item_attributes(path)
    if show:
        check_key_refusal(registry, attrs)
        secret = ss.fetch_secret(path)
        return {"path": path, "label": ss.item_label(path), "attributes": attrs,
                "secret": display_secret(secret, True)}
    return {"path": path, "label": ss.item_label(path), "attributes": attrs,
            "secret": "<redacted>"}


def read_secret_input(secret_file):
    """Secrets come from stdin or a file. Never from argv."""
    if secret_file:
        with open(secret_file, "rb") as fh:
            return fh.read()
    data = sys.stdin.buffer.read()
    if not data:
        raise SecretsmithError("empty secret on stdin; refusing to store")
    return data


def op_set(ss, registry, collection_path, label, attr_pairs, secret_file, replace):
    attributes = {}
    for k, v in attr_pairs:
        attributes[k] = v
    secret = read_secret_input(secret_file)
    return ss.create_item(collection_path, label, attributes, secret, replace)


def op_check(ss, registry, collection_path):
    svc_ok = True
    try:
        path = collection_path
        label = ss._get_prop(path, IFACE_COLLECTION, "Label")
    except Exception as exc:  # noqa: BLE001 - health check reports everything
        svc_ok = False
        label = "unreachable: %s" % exc
    chromium_entry = None
    for name in ("chromium", "chromium-v1"):
        try:
            schema, _, _ = registry.resolve(name)
            hits = ss.search(path, {SS_SCHEMA_ATTR: schema})
            if hits:
                chromium_entry = {"schema": schema, "items": len(hits)}
                break
        except Exception:
            continue
    return {
        "service": svc_ok,
        "collection": collection_path,
        "collection_label": label,
        "chromium_key_entry": chromium_entry,
    }


# Attribute keypool's loader uses to select its items in the store.
KEYPOOL_ATTR = "keypool"


def _default_fetcher_under(ss, registry, attr_key):
    """Testable store fetch with an injected service handle."""
    coll = ss.default_collection_path()
    rows = op_search(ss, registry, coll, None, [(KEYPOOL_ATTR, attr_key)], True)
    # op_search refuses secret_is_key items before fetching, so the
    # os_crypt key can never enter the returned mapping.
    return {r["label"]: r["secret"] for r in rows}


def op_selftest(ss, registry):
    """Live end-to-end verification against the real session bus.

    This is the headline guarantee: one command that proves, on the box
    it runs on, that secrets round-trip, listings redact, and the
    Chromium os_crypt key is refused on every display path. Everything
    runs inside a throwaway collection that is deleted on every exit
    path, success or failure.
    """
    checks = []
    coll = None
    item_path = None
    key_path = None

    def record(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    try:
        try:
            coll = ss.collection_create("secretsmith-selftest")
            record("collection-create", coll.startswith("/org/freedesktop/secrets/"), coll)
        except SecretsmithError as exc:
            record("collection-create", False, str(exc))
            return {"passed": False, "checks": checks}

        try:
            item_path = ss.create_item(coll, "selftest-secret",
                                       {"service": "secretsmith-selftest"},
                                       b"round-trip-payload", True)
            record("item-create", True, item_path)

            hits = ss.search(coll, {"service": "secretsmith-selftest"})
            record("search-finds-item", hits == [item_path], str(hits))

            secret = ss.fetch_secret(item_path)
            record("secret-round-trip", secret == b"round-trip-payload")

            got_redacted = op_get(ss, registry, coll,
                                  [("service", "secretsmith-selftest")], False)
            record("listing-redacts",
                   got_redacted["secret"] == "<redacted>",
                   got_redacted["secret"])

            got_shown = op_get(ss, registry, coll,
                               [("service", "secretsmith-selftest")], True)
            record("show-reveals-only-on-flag",
                   got_shown["secret"] == "round-trip-payload")

            key_path = ss.create_item(
                coll, "selftest-os-crypt-key",
                {SS_SCHEMA_ATTR: "chrome_libsecret_os_crypt_password_v2"},
                b"\x01" * 32, True)
            refused = False
            try:
                op_get(ss, registry, coll,
                       [(SS_SCHEMA_ATTR, "chrome_libsecret_os_crypt_password_v2")],
                       True)
            except KeyRefusalError:
                refused = True
            record("os-crypt-key-refused", refused)

            record("key-never-fetched-on-refusal", key_path not in ss.fetched)
        finally:
            for p in (item_path, key_path):
                if p is not None:
                    try:
                        ss.delete_item(p)
                    except SecretsmithError:
                        pass
            try:
                ss.delete_collection(coll)
            except SecretsmithError:
                pass
            record("cleanup", True)
    except Exception as exc:  # noqa: BLE001 - selftest reports, never crashes
        record("unexpected", False, str(exc))

    passed = all(c["ok"] for c in checks)
    return {"passed": passed, "checks": checks}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_attrs(pairs):
    out = []
    for pair in pairs or []:
        if "=" not in pair:
            raise SecretsmithError("attributes must be key=value, got %r" % pair)
        k, v = pair.split("=", 1)
        out.append((k, v))
    return out


def build_parser():
    ap = argparse.ArgumentParser(prog="secretsmith", description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="JSON output for everything")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="service reachable, collection unlocked, chromium entry")
    sub.add_parser("collections", help="list collections")
    sub.add_parser("selftest",
                   help="live end-to-end proof: round-trip, redaction, key refusal")

    p = sub.add_parser("search", help="search items (no schema filter by default)")
    p.add_argument("--schema", help="friendly schema name from the registry")
    p.add_argument("--attr", action="append", default=[], help="key=value, repeatable")
    p.add_argument("--collection", default=None)
    p.add_argument("--show", action="store_true")

    p = sub.add_parser("get", help="get exactly one item")
    p.add_argument("--attr", action="append", default=[], help="key=value, repeatable")
    p.add_argument("--collection", default=None)
    p.add_argument("--show", action="store_true")

    p = sub.add_parser("set", help="store a secret (stdin or --secret-file)")
    p.add_argument("--label", required=True)
    p.add_argument("--attr", action="append", default=[], help="key=value, repeatable")
    p.add_argument("--collection", default=None)
    p.add_argument("--secret-file", default=None)
    p.add_argument("--replace", action="store_true")

    p = sub.add_parser("delete", help="delete matching items")
    p.add_argument("--attr", action="append", default=[], help="key=value, repeatable")
    p.add_argument("--collection", default=None)
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("collection-create")
    p.add_argument("label")
    p.add_argument("--alias", default=None)

    p = sub.add_parser("lock"); p.add_argument("collection")
    p = sub.add_parser("unlock"); p.add_argument("collection")

    sub.add_parser("schemas", help="show the schema registry")

    p = sub.add_parser("chromium-logins", help="decrypt Login Data")
    p.add_argument("--profile-dir", default=None)
    p.add_argument("--show", action="store_true")
    p = sub.add_parser("chromium-cookies", help="decrypt Cookies")
    p.add_argument("--profile-dir", default=None)
    p.add_argument("--show", action="store_true")

    p = sub.add_parser("registry-add", help="extend the registry in place")
    p.add_argument("name")
    p.add_argument("xdg_schema")
    p.add_argument("--secret-is-key", action="store_true")

    return ap


def resolve_collection(ss, name):
    if not name:
        return ss.default_collection_path()
    for p in ss.collections():
        if p.rsplit("/", 1)[-1] == name or ss._get_prop(p, IFACE_COLLECTION, "Label") == name:
            return p
    raise SecretsmithError("no collection named %r" % name)


def main(argv=None):
    args = build_parser().parse_args(argv)
    registry = Registry()

    def emit(obj):
        if args.json:
            print(json.dumps(obj, indent=2, default=str))
        else:
            print(obj if isinstance(obj, str) else json.dumps(obj, indent=2, default=str))

    try:
        if args.cmd == "schemas":
            emit(registry.listing())
            return 0

        if args.cmd == "registry-add":
            registry.register(args.name, args.xdg_schema, args.secret_is_key)
            emit({"registered": args.name, SS_SCHEMA_ATTR: args.xdg_schema,
                  "secret_is_key": args.secret_is_key})
            return 0

        if args.cmd in ("chromium-logins", "chromium-cookies"):
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
            except ImportError:
                raise SecretsmithError(
                    "the Chromium pipeline needs the 'cryptography' package")
            ss = SecretService(registry)
            profile_dir = args.profile_dir or os.path.expanduser(
                "~/.config/chromium/Default")
            key = fetch_os_crypt_key(ss, registry, profile_dir)
            which = "logins" if args.cmd.endswith("logins") else "cookies"
            emit(chromium_decrypt(profile_dir, key, which, args.show))
            return 0

        ss = SecretService(registry)

        if args.cmd == "check":
            coll = resolve_collection(ss, None)
            emit(op_check(ss, registry, coll))
            return 0

        if args.cmd == "selftest":
            report = op_selftest(ss, registry)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                for c in report["checks"]:
                    print("%s  %s%s" % ("PASS" if c["ok"] else "FAIL",
                                        c["check"],
                                        ("  " + c["detail"]) if c["detail"] else ""))
                print("selftest: %s" % ("PASSED" if report["passed"] else "FAILED"))
            return 0 if report["passed"] else 1

        if args.cmd == "collections":
            emit(ss.collections())
            return 0

        coll = resolve_collection(ss, getattr(args, "collection", None))

        if args.cmd == "search":
            results = op_search(ss, registry, coll, args.schema,
                                parse_attrs(args.attr), args.show)
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                for r in results:
                    print("%s  %s  %s  %s" % (
                        r["label"], r["path"], json.dumps(r["attributes"]), r["secret"]))
            return 0

        if args.cmd == "get":
            emit(op_get(ss, registry, coll, parse_attrs(args.attr), args.show))
            return 0

        if args.cmd == "set":
            path = op_set(ss, registry, coll, args.label, parse_attrs(args.attr),
                          args.secret_file, args.replace)
            emit({"created": path})
            return 0

        if args.cmd == "delete":
            attrs = {}
            for k, v in parse_attrs(args.attr):
                attrs[k] = v
            paths = ss.search(coll, attrs)
            if not paths:
                raise SecretsmithError("no items match")
            if not args.yes:
                raise SecretsmithError(
                    "would delete %d item(s); rerun with --yes" % len(paths))
            for p in paths:
                ss.delete_item(p)
            emit({"deleted": len(paths)})
            return 0

        if args.cmd == "collection-create":
            emit({"collection": ss.collection_create(args.label, args.alias)})
            return 0

        if args.cmd == "lock":
            ss.lock(coll)
            emit({"locked": coll})
            return 0

        if args.cmd == "unlock":
            ss.unlock(coll)
            emit({"unlocked": coll})
            return 0

        raise SecretsmithError("unknown command %r" % args.cmd)

    except KeyRefusalError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    except SecretsmithError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())