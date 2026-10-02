# hashline patch contract — mandatory for agents

`hashline` is a **hash-anchored** editor (`/home/toxic/.local/bin/hashline`, static ELF,
version bumped 2026-09-26). Every op is anchored to an `N:hh` xxh32 content hash from
`hashline read`, not to a bare line number.

## The failure this doc exists to stop

A bare line range (`SWAP 641..674:`) resolves by **position**. If any earlier op in the
same patch adds or removes lines, every later op in that patch is off by the drift — and
hashline applies it *silently*, shredding valid code. Observed three times in one session
(2026-10-02) on `config/keypools.yaml`, `services/keypool/src/server.ts`, and
`ranch/flock/proxy/src/providers.rs` — each time a `keys.push(...)` block or a YAML
`keys:` list was truncated mid-literal, surfacing only as a parser error or a Rust build
failure much later.

## Rules

1. **Always carry the hash.** `SWAP 641:3f2a..674:9b1c:`, never `SWAP 641..674:`.
   Copy the anchors straight out of `hashline read` output.
2. **One op per patch call** unless every op after the first is hash-anchored. A single
   multi-op patch is fine when every target is hash-anchored; drift cannot then occur.
3. **Re-read before every patch.** `hashline read <file> | sed -n 'A,Bp'`. Never patch
   from an anchor captured before an intervening write.
4. **`--emit-anchors`** (or `HASHLINE_RETURN_ANCHORS=1`) appends a fresh
   `[file#HASH]` block after the summary so the next patch needs no re-read. Use it for
   sequential edits to the same file.
5. **`--dry-run`** before anything that touches generated code or a file you have already
   patched this session.
6. **Hashes are content-derived, so re-anchoring after your own edit is not optional.**
   Editing line 400 renumbers 401+. Stale anchors on *unmodified* lines still resolve.

## Why positional ranges exist at all

They are a convenience for one-shot patches on a file you just read and are not touching
again. Every corruption this session came from using that convenience in a multi-op patch
on a file already modified earlier in the same session.

## Verifying a patch landed

hashline prints `OK file#HASH edits=N changed=M` plus the changed lines (`~N:hh` for
modified, `-N` for deleted, `+N:hh` for inserted). If the count of `~` lines does not
match the size of the body you sent, the range was wrong — repair immediately with a
`hashline read` and a corrective patch. Do not proceed to the next edit.

## Known-good invocation

```bash
export HASHLINE_NO_UPDATE_CHECK=1
hashline read services/keypool/src/server.ts | sed -n '241,300p'
hashline patch services/keypool/src/server.ts - <<'EOF'
*** Begin Patch
SWAP 253:c0a..258:35c:
+  const eap = pool.protocol === "gemini-interactions";
EOF
```
