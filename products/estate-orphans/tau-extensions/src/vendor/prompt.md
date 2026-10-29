Your patch language names lines to replace, delete, or insert at, then lists the new content. Rule of thumb: a header ending in `:` is followed by `+` body rows; `DEL` has no body.

<headers>
Every file section starts with `[PATH#TAG]`. `TAG` = 4-hex snapshot tag from your latest `read`/`search`, REQUIRED on every section — no hashless form. Create new files with `write`; hashline only edits existing files.
</headers>

<ops>
`SWAP N.=M:` — replace original lines N.=M with the body rows below. INCLUSIVE — line M is consumed too.
`DEL N.=M` — delete original lines N.=M. No body.
`INS.PRE N:` — insert the body rows immediately before line N.
`INS.POST N:` — insert the body rows immediately after line N.
`INS.HEAD:` / `INS.TAIL:` — insert the body rows at the very start / end of the file.
`REM` — delete the whole file named by the section header. No body, no line ops.
`MV DEST` — move/rename the section file to `DEST` (a path, quoted when it contains spaces). Line edits above `MV` land on the source first, then the final content is written at `DEST`.
Single line: `SWAP N.=N:` / `DEL N`. The range is the ORIGINAL lines you touch; body length is irrelevant (replacing 1 line with 10 is still `SWAP N.=N:`).

**Block ops are not supported in this v1 extension.** The parser accepts them for forward compatibility but no tree-sitter resolver is wired:
`SWAP.BLK N:` — **REJECTED at apply time.** Use `SWAP N.=M:` with the concrete opening and closing line numbers.
`DEL.BLK N` — **REJECTED at apply time.** Use `DEL N.=M` with the concrete range.
`INS.BLK.POST N:` — **LOWERS to plain `INS.POST N:` with a warning.** The insert still lands at line N + 1; verify against your latest `read` that this is where you wanted the payload.
Do NOT reach for block ops to save typing a range; the extension will refuse two of the three, and the third silently changes semantics from "after the block's END" to "after line N".
</ops>

<body-rows>
Body rows appear only under a `:` header. Every body row is `+TEXT` — add a literal line `TEXT`, verbatim (leading whitespace kept); `+` alone adds a blank line. No other row kind. NEVER write `-old` or a bare/context line. To keep a line, leave it out of every range. To insert a literal line starting with `-` or `+`, prefix it: `+-x`, `++x`.
</body-rows>

<rules>
- Line numbers + `[PATH#TAG]` header come from your latest `read`/`search` (`LINE:TEXT` rows).
- Numbers refer to the ORIGINAL file; never shift as hunks apply.
- They die with the call: every applied edit mints a fresh `#TAG` and renumbers — anchor the next edit on the edit response or a fresh `read`.
- Touch only lines your latest `read`/`search` literally displayed as `LINE:TEXT`; the tag certifies the snapshot, not your memory. A hunk anchored on a line you never displayed is REJECTED — re-`read` first. Seeing a line ≠ it holds the code you mean; confirm numbers map to the construct you intend, especially far from your read window.
- Elided regions are UNSEEN: `…`/`..` markers and a collapsed `N-M:` summary row (only boundary lines N and M shown) hide their interior. NEVER place or span a hunk inside one — `read` the range first.
- Never start or end a range mid-expression or mid-block.
- Indent body rows exactly for the depth they should live at.
- On a stale-tag rejection or any surprising result: STOP and re-`read` before further edits.
- One hunk per range; body = final content, never an old/new pair.
- Ranges cover ONLY lines whose content changes. Never widen over unchanged lines — a stale wide range shreds everything it spans.
- Whole construct → figure out its opening and closing line numbers from your latest `read`, then use `SWAP N.=M:` / `DEL N.=M` with those concrete numbers. Block ops (`SWAP.BLK`/`DEL.BLK`) are refused; `INS.BLK.POST` silently lowers to `INS.POST N:` (payload lands at line N+1, not after any block).
- Non-adjacent changes = separate hunks; untouched lines stay out of every range.
- Pure additions use `INS.PRE` / `INS.POST` / `INS.HEAD` / `INS.TAIL`, never a widened `SWAP` — retyped keepers are exactly what gets dropped. (A multi-line `SWAP` whose body restates the line just past the range is auto-dropped as an off-by-one keeper with a warning — issue the payload for the range only; never lean on the repair.)
- NEVER format/restyle code with this tool; run the project formatter instead.
</rules>

<example>
Original (the exact shape `read` returns):
```
[greet.py#A1B2]
1:def greet(name):
2:    msg = "Hello, " + name
3:    print(msg)
4:greet("world")
```

Insert a guard after line 1:
```
[greet.py#A1B2]
INS.POST 1:
+    if not name: name = "stranger"
```

Replace line 2 with two lines:
```
[greet.py#A1B2]
SWAP 2.=2:
+    greeting = "Hi"
+    msg = f"{greeting}, {name}"
```

Delete line 3:
```
[greet.py#A1B2]
DEL 3
```

Delete the whole file:
```
[greet.py#A1B2]
REM
```

Rename or move the file:
```
[greet.py#A1B2]
MV greet_v2.py
```

Move after editing:
```
[greet.py#A1B2]
SWAP 1.=3:
+def greet(name):
+    print(f"Hi, {name}")
MV lib/greet.py
```

Add a header and trailer:
```
[greet.py#A1B2]
INS.HEAD:
+# generated header
INS.TAIL:
+greet("everyone")
```

Replace the whole `greet` function — use the concrete opening/closing lines from your `read` (here 1..=3 covers the `def` header through `print(msg)`; line 4 is a separate statement and stays):
```
[greet.py#A1B2]
SWAP 1.=3:
+def greet(name):
+    print(f"Hello, {name}")
```
</example>

<anti-patterns>
# WRONG — empty `SWAP` to delete. RIGHT: DEL 4
SWAP 4.=4:

# WRONG — range describes post-edit size. RIGHT: SWAP 1.=1: (body length is irrelevant)
SWAP 1.=2:
+def greet(name):

# WRONG — `-` rows / bare context lines do not exist. The range deletes; the body is only the new content.
SWAP 3.=3:
    msg = "Hello, " + name
-   print(msg)
+   return msg
# RIGHT
SWAP 3.=3:
+   return msg

# WRONG — a pure insertion done as a widened `SWAP`: you want to add one line after 2,
# but you replace 2.=4, retype the keepers, and drop one (here line 4, `greet("world")`).
SWAP 2.=4:
+    msg = "Hello, " + name
+    extra = compute(name)
+    print(msg)
# RIGHT — touch nothing you keep; the new line is the whole body.
INS.POST 2:
+    extra = compute(name)

# WRONG — using `SWAP.BLK`/`DEL.BLK` in this v1 extension. They are REJECTED. RIGHT: use plain SWAP/DEL with the concrete opening.=closing line numbers from your read.
SWAP.BLK 1:
+def greet(name): pass
# RIGHT — read told you the block ends at line 3.
SWAP 1.=3:
+def greet(name): pass

# WRONG — `INS.BLK.POST N:` anchored on a closing delimiter / last visible line. RIGHT: plain `INS.POST M:`. Note that in this v1 extension `INS.BLK.POST` silently lowers to `INS.POST` anyway (payload at N+1, not after any block), so use `INS.POST` directly.
INS.BLK.POST 3:
+after()
# RIGHT
INS.POST 3:
+after()
</anti-patterns>

<critical>
If you remember nothing else:
1. RE-GROUND AFTER EVERY EDIT. Every apply mints a fresh `#TAG` and renumbers — take the next edit's numbers from the edit response or a fresh `read`. Stale tag or surprise? STOP, re-`read`.
2. RANGES ARE TIGHT. Cover only lines that change; a stale wide range shreds everything it spans. Whole construct → `SWAP.BLK N`.
3. THE BODY IS THE FINAL CONTENT. Only `+TEXT` rows; never `-old`/context lines. The range does the deleting.
</critical>
