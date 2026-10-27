# Get started: your first hashline patch

This is a hands-on walkthrough. By the end you'll have wired
`hashline-pi` into a Pi installation, watched the tool refuse a stale
edit, and applied a real multi-file patch. Read this once end-to-end
before dropping into `reference.md` or `how-to.md`.

Estimated time: 15 minutes.

## Prerequisites

- Bun ≥ 1.3 (`bun --version`).
- A Pi installation supplying `@earendil-works/pi-coding-agent` ≥ 0.80.
- A working directory you're comfortable modifying — this tutorial
  creates and deletes files under `/tmp/hashline-tutorial`.

## Step 1 — clone and install

```sh
git clone https://github.com/acoyfellow/hashline-pi.git \
  ~/.tau/agent/extensions/hashline-pi
cd ~/.tau/agent/extensions/hashline-pi
bun install
```

Pi's extension loader discovers this repo via the `pi.extensions`
field in its `package.json`. If your Pi config points at a different
extension search path, either clone the repo there instead or add a
symlink.

## Step 2 — verify the extension is loaded

Start Pi and, from a Pi shell prompt, list registered tools. You
should see `hashline` in the list with the label `Hashline Edit`. If
you don't, `bun install` failed silently or Pi's discovery path
doesn't include the clone directory — check both before continuing.

## Step 3 — prime a workspace

```sh
mkdir -p /tmp/hashline-tutorial
cd /tmp/hashline-tutorial
cat > greeter.ts <<'EOF'
export function greet(name: string): string {
  return "hi, " + name;
}
EOF
```

Point Pi at this directory (the extension jails writes to
`process.cwd()` at init time, so your Pi session's cwd IS your
workspace root — anything outside is refused).

## Step 4 — read, then hashline-edit

Ask the Pi agent to `read greeter.ts`. It returns something like:

```
[greeter.ts#7F3A]
1:export function greet(name: string): string {
2:  return "hi, " + name;
3:}
```

Now ask the agent to update the greeting. The agent authors:

```
[greeter.ts#7F3A]
SWAP 2.=2:
+  return `hello, ${name}!`;
```

`hashline` applies the patch and echoes a fresh tag. Read the file
again to confirm.

## Step 5 — watch a stale tag get refused

Deliberately author a patch using the old tag `7F3A` (the tag has
changed after Step 4):

```
[greeter.ts#7F3A]
SWAP 3.=3:
+// end
```

`hashline` refuses with `stale tag for greeter.ts: patch names #7F3A,
current content hashes to #<new>`. That is the language's whole
raison d'être — a stale anchor never applies. Re-`read` and re-author
against the fresh tag.

## Step 6 — multi-file atomic edit

Create a second file:

```sh
cat > README.md <<'EOF'
# Greeter
EOF
```

Ask the agent to write a patch that touches BOTH files at once:

```
[greeter.ts#<fresh-tag>]
INS.TAIL:
+
+export const DEFAULT_NAME = "world";

[README.md#<fresh-tag>]
INS.TAIL:
+
+See `greeter.ts` for the exported names.
```

Both sections preflight in memory before either commit. If the second
section's tag were stale, neither file would change. This is the
"all-or-nothing at preflight" guarantee — see `docs/explanation.md`
for the exact atomicity boundary (spoiler: it stops being all-or-
nothing once the commit loop starts writing).

## Step 7 — see the jail refuse an escape

Have the agent author (deliberately) a bad patch:

```
[/etc/hosts#0000]
INS.HEAD:
+# owned
```

`hashline` refuses with `path "/etc/hosts" is outside the workspace
root (...): absolute paths outside the root are refused. Re-author
the section header as a path relative to the workspace root; hashline
does not write outside its root.` No filesystem call was made.

The same refusal fires for `[../../etc/hosts#0000]`, for a
`MV /etc/hosts` on a legitimate in-root section, and for a symlink
inside the root that points to `/etc/hosts`. See `test/jail.test.ts`
for the exhaustive matrix.

## Step 8 — clean up

```sh
rm -rf /tmp/hashline-tutorial
```

## Where next

- `docs/how-to.md` — recipes for common editing patterns.
- `docs/reference.md` — the full grammar, header shape, and error
  message glossary.
- `docs/explanation.md` — design notes: tag-based anchoring,
  preflight-vs-commit atomicity, the 4-hex tag collision math, and
  why the shipped extension jails writes while the vendored core seam
  does not.
- `src/vendor/prompt.md` — the tool description string that ships to
  the model. Read this if you're wondering what the LLM sees.
