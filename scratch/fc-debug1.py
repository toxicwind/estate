import io, contextlib, tempfile, sys
sys.path.insert(0, "/home/toxic/fc-ci-fix-2721520964")
from pathlib import Path
from types import SimpleNamespace
import chat
import tests  # noqa: F401 - triggers key provisioning
from tests.test_chat import ChatRegressionTests

tc = ChatRegressionTests()
tc.setUp()
try:
    channel = tc._channel("general")
    chat.cmd_post(tc.root, tc._post_args(sender="bob", to="alice", title="First"))
    chat.cmd_post(tc.root, tc._post_args(sender="bob", to="alice", title="Second"))
    for f in sorted(channel.glob("*.md")):
        print("BEFORE:", f.name)
    first, second = sorted(channel.glob("*.md"))
    first.rename(channel / "tmp-swap.md")
    second.rename(first)
    (channel / "tmp-swap.md").rename(second)
    for f in sorted(channel.glob("*.md")):
        print("AFTER:", f.name)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        chat.cmd_read(tc.root, SimpleNamespace(ephemeral=None, channel="general", agent="alice", all=False, peek=False))
    print(output.getvalue()[:1500])
finally:
    tc.tearDown()
