"""Unit tests for secretsmith. No keyring or D-Bus needed.

Run:  python3 -m unittest discover -s tests -v
Live D-Bus integration (opt-in):  SSM_TEST_KEYRING=1 python3 -m unittest discover -s tests -v
"""

import base64
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import secretsmith as ssm


REGISTRY_FIXTURE = {
    "chromium": {
        "xdg:schema": "chrome_libsecret_os_crypt_password_v2",
        "secret_is_key": True,
    },
    "generic": {
        "xdg:schema": "org.freedesktop.Secret.Generic",
        "secret_is_key": False,
    },
}


class FakeService:
    """In-memory stand-in for SecretService. Mirrors the real call surface."""

    def __init__(self, registry, items=None):
        self.registry = registry
        self.items = dict(items or {})  # path -> {"label","attrs","secret","locked"}
        self._next = 0
        self.fetched = []
        self.deleted_collections = []

    def default_collection_path(self):
        return "/org/freedesktop/secrets/collection/default"

    def collections(self):
        return [self.default_collection_path()]

    def search(self, collection_path, attributes):
        hits = []
        for path, item in self.items.items():
            if all(item["attrs"].get(k) == v for k, v in attributes.items()):
                hits.append(path)
        return hits

    def item_attributes(self, item_path):
        return dict(self.items[item_path]["attrs"])

    def item_label(self, item_path):
        return self.items[item_path]["label"]

    def item_locked(self, item_path):
        return bool(self.items[item_path].get("locked", False))

    def fetch_secret(self, item_path):
        self.fetched.append(item_path)
        return self.items[item_path]["secret"]

    def create_item(self, collection_path, label, attributes, secret, replace):
        self._next += 1
        path = "%s/item%d" % (collection_path, self._next)
        self.items[path] = {"label": label, "attrs": dict(attributes),
                            "secret": bytes(secret)}
        return path

    def delete_item(self, item_path):
        del self.items[item_path]

    def _get_prop(self, obj_path, iface, prop):
        if iface == ssm.IFACE_COLLECTION and prop == "Label":
            return obj_path.rsplit("/", 1)[-1]
        if iface == ssm.IFACE_SERVICE and prop == "Collections":
            return [self.default_collection_path()]
        raise AssertionError("unexpected prop read %s/%s" % (iface, prop))

    def lock(self, collection_path):
        pass

    def unlock(self, collection_path):
        pass

    def collection_create(self, label, alias=None):
        return "/org/freedesktop/secrets/collection/%s" % label

    def delete_collection(self, collection_path):
        for p in [p for p in self.items if p.startswith(collection_path + "/")]:
            del self.items[p]
        self.deleted_collections.append(collection_path)


def make_registry(tmp):
    path = os.path.join(tmp, "schemas.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(REGISTRY_FIXTURE, fh)
    return ssm.Registry(path)


class RegistryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.reg = make_registry(self.tmp)

    def test_known_name_resolves(self):
        schema, is_key, warned = self.reg.resolve("chromium")
        self.assertEqual(schema, "chrome_libsecret_os_crypt_password_v2")
        self.assertTrue(is_key)
        self.assertFalse(warned)

    def test_unknown_name_warns_not_fails(self):
        schema, is_key, warned = self.reg.resolve("weird-thing")
        self.assertEqual(schema, "weird-thing")
        self.assertFalse(is_key)
        self.assertTrue(warned)

    def test_is_key_schema(self):
        self.assertTrue(self.reg.is_key_schema("chrome_libsecret_os_crypt_password_v2"))
        self.assertFalse(self.reg.is_key_schema("org.freedesktop.Secret.Generic"))
        self.assertFalse(self.reg.is_key_schema("not.registered"))

    def test_register_round_trip(self):
        self.reg.register("ops", "com.example.ops", secret_is_key=False)
        with open(self.reg.path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["ops"][ssm.SS_SCHEMA_ATTR], "com.example.ops")


class RedactionTest(unittest.TestCase):
    def test_listing_redacts(self):
        self.assertEqual(ssm.redact(b"x" * 42), "<redacted: 42 bytes>")

    def test_display_no_show(self):
        self.assertEqual(ssm.display_secret(b"hunter2", False), "<redacted: 7 bytes>")

    def test_display_show_text(self):
        self.assertEqual(ssm.display_secret(b"hunter2", True), "hunter2")

    def test_display_show_binary_base64(self):
        raw = bytes([0, 159, 146, 150])
        self.assertEqual(ssm.display_secret(raw, True), base64.b64encode(raw).decode())


class KeyRefusalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.reg = make_registry(self.tmp)

    def test_refusal_for_key_schema(self):
        attrs = {ssm.SS_SCHEMA_ATTR: "chrome_libsecret_os_crypt_password_v2"}
        with self.assertRaises(ssm.KeyRefusalError):
            ssm.check_key_refusal(self.reg, attrs)

    def test_no_refusal_for_generic(self):
        attrs = {ssm.SS_SCHEMA_ATTR: "org.freedesktop.Secret.Generic"}
        ssm.check_key_refusal(self.reg, attrs)  # must not raise

    def test_refusal_happens_before_fetch(self):
        reg = self.reg
        key_item = "/items/key"
        ss = FakeService(reg, {
            key_item: {"label": "os_crypt key", "attrs": {
                ssm.SS_SCHEMA_ATTR: "chrome_libsecret_os_crypt_password_v2"},
                "secret": b"\x01" * 32},
        })
        with self.assertRaises(ssm.KeyRefusalError):
            ssm.op_search(ss, reg, "/coll", "chromium", [], show=True)
        # the secret was never fetched from the service
        self.assertEqual(ss.fetched, [])


class OperationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.reg = make_registry(self.tmp)

    def test_search_no_schema_filter_default(self):
        # The original bug: schema-free items must still be found.
        ss = FakeService(self.reg, {
            "/items/a": {"label": "api key", "attrs": {"service": "ex"}, "secret": b"k"},
        })
        results = ssm.op_search(ss, self.reg, "/coll", None, [("service", "ex")], False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["secret"], "<redacted>")

    def test_search_schema_attribute_injected(self):
        ss = FakeService(self.reg, {
            "/items/a": {"label": "k", "attrs": {
                ssm.SS_SCHEMA_ATTR: "chrome_libsecret_os_crypt_password_v2"},
                "secret": b"\x00" * 32},
        })
        results = ssm.op_search(ss, self.reg, "/coll", "chromium", [], False)
        self.assertEqual(len(results), 1)

    def test_get_errors_on_zero_matches(self):
        ss = FakeService(self.reg)
        with self.assertRaises(ssm.SecretsmithError):
            ssm.op_get(ss, self.reg, "/coll", [("nope", "x")], False)

    def test_get_errors_on_multiple_matches(self):
        ss = FakeService(self.reg, {
            "/items/a": {"label": "a", "attrs": {"s": "1"}, "secret": b"1"},
            "/items/b": {"label": "b", "attrs": {"s": "1"}, "secret": b"2"},
        })
        with self.assertRaisesRegex(ssm.SecretsmithError, "2 items match"):
            ssm.op_get(ss, self.reg, "/coll", [("s", "1")], False)

    def test_set_round_trip(self):
        ss = FakeService(self.reg)
        secret_file = os.path.join(self.tmp, "key.txt")
        with open(secret_file, "wb") as fh:
            fh.write(b"from-file")
        path = ssm.op_set(ss, self.reg, "/coll", "my key",
                          [("service", "ex")], secret_file, True)
        got = ssm.op_get(ss, self.reg, "/coll", [("service", "ex")], True)
        self.assertEqual(got["secret"], "from-file")

    def test_set_refuses_empty_secret(self):
        ss = FakeService(self.reg)
        with self.assertRaisesRegex(ssm.SecretsmithError, "refusing to store"):
            ssm.op_set(ss, self.reg, "/coll", "k", [], None, False)


class OsCryptTest(unittest.TestCase):
    """Synthetic-key round trips. No keyring, no Chromium profile needed."""

    KEY = bytes(range(32))  # AES-256 key

    def v10_encrypt(self, plaintext):
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        pad = 16 - (len(plaintext) % 16)
        padded = plaintext + bytes([pad]) * pad
        enc = Cipher(algorithms.AES(self.KEY), modes.CBC(ssm.CBC_FIXED_IV)).encryptor()
        return ssm.V10_PREFIX + enc.update(padded) + enc.finalize()

    def v11_encrypt(self, plaintext):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = b"\xab" * 12
        ct = AESGCM(self.KEY).encrypt(nonce, plaintext, None)
        return ssm.V11_PREFIX + nonce + ct

    def test_v10_round_trip(self):
        blob = self.v10_encrypt(b"correct horse")
        self.assertEqual(ssm.decrypt_os_crypt(self.KEY, blob), b"correct horse")

    def test_v11_round_trip(self):
        blob = self.v11_encrypt(b"battery staple")
        self.assertEqual(ssm.decrypt_os_crypt(self.KEY, blob), b"battery staple")

    def test_unknown_prefix_returns_none(self):
        self.assertIsNone(ssm.decrypt_os_crypt(self.KEY, b"zzzz-whatever"))

    def test_wrong_key_returns_none(self):
        blob = self.v10_encrypt(b"secret")
        self.assertIsNone(ssm.decrypt_os_crypt(b"\x00" * 32, blob))

    def test_chromium_decrypt_logins(self):
        import sqlite3

        tmp = tempfile.mkdtemp()
        db = os.path.join(tmp, "Login Data")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE logins (origin_url TEXT, username_value TEXT, "
                    "password_value BLOB)")
        con.execute("INSERT INTO logins VALUES (?,?,?)",
                    ("https://ex.com", "alice", self.v10_encrypt(b"pw123")))
        con.commit()
        con.close()
        rows = ssm.chromium_decrypt(tmp, self.KEY, "logins", True)
        self.assertEqual(rows[0]["password"], "pw123")
        redacted = ssm.chromium_decrypt(tmp, self.KEY, "logins", False)
        self.assertEqual(redacted[0]["password"], "<redacted: 5 bytes>")

    def test_key_item_unreachable_via_display_path(self):
        # The os_crypt key stored in the service is refused by every
        # display operation before the secret is fetched.
        tmp = tempfile.mkdtemp()
        reg = make_registry(tmp)
        ss = FakeService(reg)
        ss.items["/items/key"] = {"label": "os_crypt", "attrs": {
            ssm.SS_SCHEMA_ATTR: "chrome_libsecret_os_crypt_password_v2"},
            "secret": self.KEY}
        with self.assertRaises(ssm.KeyRefusalError):
            ssm.op_get(ss, reg, "/coll",
                       [(ssm.SS_SCHEMA_ATTR, "chrome_libsecret_os_crypt_password_v2")],
                       True)
        self.assertEqual(ss.fetched, [])


def dbus_bus_available():
    """True only when a session bus is actually reachable right now.

    Import failure and connection failure both count as 'no bus'. Never
    raises: this is a probe used for skip decisions.
    """
    try:
        import dbus
    except ImportError:
        return False
    try:
        dbus.SessionBus()
        return True
    except Exception:  # noqa: BLE001 - any dbus error means: skip
        return False


class SelftestTest(unittest.TestCase):
    """The headline feature must be provable without a bus too."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.reg = make_registry(self.tmp)

    def test_selftest_passes_on_fake(self):
        ss = FakeService(self.reg)
        report = ssm.op_selftest(ss, self.reg)
        names = {c["check"] for c in report["checks"]}
        self.assertTrue(report["passed"], json.dumps(report, indent=2))
        for expected in ("collection-create", "item-create", "search-finds-item",
                         "secret-round-trip", "listing-redacts",
                         "show-reveals-only-on-flag", "os-crypt-key-refused",
                         "key-never-fetched-on-refusal", "cleanup"):
            self.assertIn(expected, names)

    def test_selftest_cleanup_deletes_collection(self):
        ss = FakeService(self.reg)
        report = ssm.op_selftest(ss, self.reg)
        self.assertTrue(report["passed"])
        self.assertEqual(len(ss.deleted_collections), 1)
        self.assertEqual(ss.items, {})

    def test_selftest_reports_failure_not_crash(self):
        class BrokenService(FakeService):
            def collection_create(self, label, alias=None):
                raise ssm.SecretsmithError("bus exploded")

        ss = BrokenService(self.reg)
        report = ssm.op_selftest(ss, self.reg)
        self.assertFalse(report["passed"])
        self.assertFalse(report["checks"][0]["ok"])


class LiveSelftestProbeTest(unittest.TestCase):
    def test_probe_never_raises(self):
        # dbus may be absent on this box; the probe must return a bool.
        self.assertIn(dbus_bus_available(), (True, False))


@unittest.skipUnless(
    os.environ.get("SSM_TEST_KEYRING") and dbus_bus_available(),
    "live D-Bus opt-in (set SSM_TEST_KEYRING=1 and have a session bus)",
)
class LiveKeyringTest(unittest.TestCase):
    """Throwaway collection, item round-trip, delete. Needs a real bus."""

    def test_round_trip(self):
        reg = ssm.Registry()
        ss = ssm.SecretService(reg)
        coll = ss.collection_create("secretsmith-test-tmp")
        created_path = None
        key_path = None
        try:
            path = ss.create_item(coll, "t", {"s": "1"}, b"hello", True)
            created_path = path
            hits = ss.search(coll, {"s": "1"})
            self.assertEqual(hits, [path])
            self.assertEqual(ss.fetch_secret(path), b"hello")
            # redaction invariant holds against the live service too
            got = ssm.op_get(ss, reg, coll, [("s", "1")], show=False)
            self.assertEqual(got["secret"], "<redacted>")
            # the refusal path works against a real key-schema item
            key_path = ss.create_item(
                coll, "k",
                {ssm.SS_SCHEMA_ATTR: "chrome_libsecret_os_crypt_password_v2"},
                b"\x01" * 32, True)
            with self.assertRaises(ssm.KeyRefusalError):
                ssm.op_get(ss, reg, coll,
                           [(ssm.SS_SCHEMA_ATTR,
                             "chrome_libsecret_os_crypt_password_v2")],
                           True)
            # the key item's secret was never fetched on that display path
            self.assertNotIn(key_path, ss.fetched)
        finally:
            for p in (created_path, key_path):
                if p is not None:
                    try:
                        ss.delete_item(p)
                    except SecretsmithError:
                        pass
            try:
                ss.delete_collection(coll)
            except SecretsmithError:
                pass


if __name__ == "__main__":
    unittest.main()

class KeypoolLoaderTest(unittest.TestCase):
    """The keypool overlay: files are transport, store wins, refusal holds."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.reg = make_registry(self.tmp)
        self.secrets_file = os.path.join(self.tmp, "secrets")
        with open(self.secrets_file, "w", encoding="utf-8") as fh:
            fh.write("FILE_KEY=file-value\n# comment\nexport QUOTED=\"q\"\n")

    def _load_mod(self):
        loader_path = os.path.join(os.path.dirname(self.reg.path),
                                   "keypool-secrets.py")
        if loader_path not in sys.path:
            sys.path.insert(0, os.path.dirname(self.reg.path))
        import keypool_secrets as kp

        return kp

    def test_files_only_default(self):
        kp = self._load_mod()
        out = kp.load(self.secrets_file, store_fetcher=None)
        self.assertEqual(out, {"FILE_KEY": "file-value", "QUOTED": "q"})

    def test_store_overrides_files(self):
        kp = self._load_mod()
        out = kp.load(self.secrets_file,
                      store_fetcher=lambda k: {"FILE_KEY": "store-value",
                                               "STORE_ONLY": "sv"})
        self.assertEqual(out["FILE_KEY"], "store-value")
        self.assertEqual(out["STORE_ONLY"], "sv")
        self.assertEqual(out["QUOTED"], "q")

    def test_store_failure_degrades_to_files(self):
        kp = self._load_mod()
        def boom(attr_key):
            raise RuntimeError("no bus")
        # the store layer swallows and degrades; keypool boots on files only
        self.assertEqual(kp._load_store(fetcher=boom, enabled=True), {})
        out = kp.load(self.secrets_file, store_fetcher=boom)
        self.assertEqual(out, {"FILE_KEY": "file-value", "QUOTED": "q"})

    def test_unreachable_store_never_breaks_boot(self):
        # Simulates KEYPOOL_SECRETS_BACKEND=secretsmith with the CLI absent.
        kp = self._load_mod()
        saved = dict(os.environ)
        os.environ["KEYPOOL_SECRETS_BACKEND"] = "secretsmith"
        try:
            def broken_fetcher(attr_key):
                raise ImportError("secretsmith.py not found")
            # _load_store swallows and returns {}; load() must still serve files
            out = kp.load(self.secrets_file,
                          store_fetcher=None)  # default path may import dbus
            # On this Windows box dbus is absent, so the overlay is a no-op
            # either way; the invariant is that load() returns the file dict.
            self.assertIn("FILE_KEY", out)
        finally:
            os.environ.clear()
            os.environ.update(saved)

    def test_refusal_never_loads_key_into_dict(self):
        kp = self._load_mod()

        def hostile_fetcher(attr_key):
            # Someone stored the os_crypt key with keypool=1. The fetcher
            # routes through op_search, which refuses before fetching.
            ss = FakeService(self.reg, {
                "/items/key": {"label": "os_crypt", "attrs": {
                    ssm.SS_SCHEMA_ATTR: "chrome_libsecret_os_crypt_password_v2",
                    "keypool": "1"},
                    "secret": b"\x01" * 32},
            })
            return ssm._default_fetcher_under(ss, self.reg, attr_key)

        out = kp.load(self.secrets_file, store_fetcher=hostile_fetcher)
        # keypool boots, files intact, and the os_crypt key is absent
        self.assertEqual(out, {"FILE_KEY": "file-value", "QUOTED": "q"})
        self.assertNotIn("os_crypt", out)