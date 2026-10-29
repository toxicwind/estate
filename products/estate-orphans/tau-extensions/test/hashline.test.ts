/**
 * Adversarial test suite for the hashline patcher.
 *
 * Every test either exercises a documented invariant or a class of failure
 * that historically breaks LLM-authored patch formats: stale tags,
 * malformed headers, overlap, cross-file atomicity, unicode/CRLF
 * preservation, move/delete semantics, and unsupported block ops.
 *
 * Tests use the in-memory Filesystem/SnapshotStore except where the
 * NodeFilesystem's disk semantics are the point (multi-file atomicity,
 * CRLF/BOM round-trip through the disk, `MV` across directories).
 */
import { describe, expect, test } from 'bun:test';
import * as fs from 'node:fs/promises';
import * as os from 'node:os';
import * as path from 'node:path';
import {
  computeFileHash,
  formatHashlineHeader,
  InMemoryFilesystem,
  InMemorySnapshotStore,
  MismatchError,
  NodeFilesystem,
  Patch,
  Patcher,
} from '../src/vendor/index.ts';

// ─────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────

interface Env {
  fs: InMemoryFilesystem;
  snapshots: InMemorySnapshotStore;
  patcher: Patcher;
}

function makeEnv(files: Record<string, string> = {}): Env {
  const inMemory = new InMemoryFilesystem();
  const snapshots = new InMemorySnapshotStore();
  for (const [p, content] of Object.entries(files)) {
    inMemory.set(p, content);
    snapshots.record(inMemory.canonicalPath(p), content);
  }
  return { fs: inMemory, snapshots, patcher: new Patcher({ fs: inMemory, snapshots }) };
}

function tag(text: string): string {
  return computeFileHash(text);
}

function header(p: string, text: string): string {
  return formatHashlineHeader(p, tag(text));
}

async function mkTempDir(prefix: string): Promise<string> {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), prefix));
  return dir;
}

// ─────────────────────────────────────────────────────────────────────────
// Snapshot tag: what invalidates it, what must not
// ─────────────────────────────────────────────────────────────────────────

describe('snapshot tag stability', () => {
  test('CRLF vs LF: byte-different files mint the same tag', () => {
    expect(tag('a\nb\nc\n')).toEqual(tag('a\r\nb\r\nc\r\n'));
  });

  test('trailing whitespace per line is ignored by the tag', () => {
    expect(tag('a\nb\n')).toEqual(tag('a   \nb\t\n'));
  });

  test('unicode content survives the tag round-trip', () => {
    const body = '// π μ ✓ 日本語 🐘\nconst x = 1;\n';
    expect(tag(body)).toEqual(tag(body));
    expect(tag(body)).not.toEqual(tag(`${body}extra\n`));
  });

  test('empty file hashes to a stable tag', () => {
    expect(tag('')).toMatch(/^[0-9A-F]{4}$/);
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Stale tag rejection: the whole point of hashline
// ─────────────────────────────────────────────────────────────────────────

describe('stale tag rejection', () => {
  test('anchor-scoped edit against a stale tag rejects with MismatchError', async () => {
    const original = 'one\ntwo\nthree\n';
    const env = makeEnv({ 'foo.ts': original });
    // Model authored against an OLDER version of the file that no longer exists.
    const stalePatch = `[foo.ts#0000]\nSWAP 1.=1:\n+ONE\n`;
    // The stale tag is 0000 (invalid), so the patcher should reject.
    await expect(env.patcher.apply(Patch.parse(stalePatch))).rejects.toThrow(MismatchError);
  });

  test('stale tag is recoverable via 3-way merge when the old version is retained', async () => {
    const v1 = 'a\nb\nc\nd\n';
    const env = makeEnv({ 'r.ts': v1 });
    const v1Tag = tag(v1);
    // Apply a first edit to advance the file. The snapshot store now retains
    // both v1 and v2.
    const first = `[r.ts#${v1Tag}]\nSWAP 1.=1:\n+A\n`;
    await env.patcher.apply(Patch.parse(first));
    // Author a follow-up against v1's tag; recovery replays it on the live
    // content.
    const stale = `[r.ts#${v1Tag}]\nSWAP 3.=3:\n+C\n`;
    const result = await env.patcher.apply(Patch.parse(stale));
    expect(env.fs.get('r.ts')).toEqual('A\nb\nC\nd\n');
    expect(result.sections[0].warnings.length).toBeGreaterThan(0);
  });

  test('missing tag on an existing file is rejected up front', async () => {
    const env = makeEnv({ 'x.ts': 'x\n' });
    const noTag = `[x.ts]\nSWAP 1.=1:\n+y\n`;
    await expect(env.patcher.apply(Patch.parse(noTag))).rejects.toThrow(/snapshot tag/i);
  });

  test('head/tail-only edits survive a stale tag with a warning', async () => {
    const env = makeEnv({ 'z.ts': 'orig\n' });
    // Advance the file so the tag drifts.
    const t1 = tag('orig\n');
    await env.patcher.apply(Patch.parse(`[z.ts#${t1}]\nSWAP 1.=1:\n+first\n`));
    // Now author an INS.TAIL: against the OLD tag.
    const patch = `[z.ts#${t1}]\nINS.TAIL:\n+trailer\n`;
    const result = await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('z.ts')).toEqual('first\ntrailer\n');
    expect(result.sections[0].warnings.some((w) => /stale snapshot tag/.test(w))).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Malformed input surfaces a focused error
// ─────────────────────────────────────────────────────────────────────────

describe('malformed input', () => {
  test('missing header raises before touching the FS', async () => {
    const env = makeEnv({ 'x.ts': 'x\n' });
    expect(() => Patch.parse('SWAP 1.=1:\n+y\n')).toThrow(/first non-blank line/i);
    // Still no writes.
    expect(env.fs.get('x.ts')).toEqual('x\n');
  });

  test('unified-diff hunk header is a focused rejection', () => {
    expect(() => Patch.parse('@@ -1,1 +1,1 @@\n hi\n')).toThrow(/unified-diff/i);
  });

  test('apply_patch sentinel is a focused rejection', () => {
    expect(() => Patch.parse('*** Update File:foo.ts\n hi\n')).toThrow();
  });

  test('bare range hunk header is rejected with the suggested verb', async () => {
    const env = makeEnv({ 'a.ts': '1\n2\n3\n' });
    const t = tag('1\n2\n3\n');
    // Missing SWAP/DEL verb.
    const patch = `[a.ts#${t}]\n1.=2:\n+x\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(
      /hunk headers need a verb/i,
    );
  });

  test('DEL with a body rejects', async () => {
    const env = makeEnv({ 'a.ts': 'x\ny\n' });
    const t = tag('x\ny\n');
    const patch = `[a.ts#${t}]\nDEL 1\n+oops\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/DEL/);
  });

  test('range with end < start rejects', async () => {
    const env = makeEnv({ 'a.ts': 'x\ny\n' });
    const t = tag('x\ny\n');
    const patch = `[a.ts#${t}]\nSWAP 2.=1:\n+q\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/ends before it starts/i);
  });

  test('out-of-bounds line rejects', async () => {
    const env = makeEnv({ 'a.ts': 'x\n' });
    const t = tag('x\n');
    const patch = `[a.ts#${t}]\nSWAP 99.=99:\n+q\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/does not exist/i);
  });

  test('two hunks on the same line reject as overlap', async () => {
    const env = makeEnv({ 'a.ts': 'x\ny\nz\n' });
    const t = tag('x\ny\nz\n');
    const patch = `[a.ts#${t}]\nDEL 2\nDEL 2\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/already targeted/i);
  });

  test('conflicting tags for the same file across sections reject', () => {
    const patch = `[a.ts#AAAA]\nSWAP 1.=1:\n+x\n[a.ts#BBBB]\nSWAP 2.=2:\n+y\n`;
    expect(() => Patch.parse(patch)).toThrow(/Conflicting hashline snapshot tags/);
  });

  test('malformed header (garbage after path) rejects strictly', () => {
    expect(() => Patch.parse('[foo.ts#XX]\nSWAP 1.=1:\n+q\n')).toThrow(/Input header must be/i);
  });

  test('unsupported hex length in tag rejects', () => {
    expect(() => Patch.parse('[foo.ts#ABCDEF]\nSWAP 1.=1:\n+q\n')).toThrow(/Input header must be/i);
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Multi-hunk / multi-file atomicity
// ─────────────────────────────────────────────────────────────────────────

describe('multi-hunk & multi-file atomicity', () => {
  test('one bad section aborts the whole patch: no partial writes', async () => {
    const good = 'a\nb\nc\n';
    const other = 'p\nq\nr\n';
    const env = makeEnv({ 'good.ts': good, 'other.ts': other });
    const gTag = tag(good);
    // Section 1 is valid; section 2 references a nonexistent line, which
    // fails in the preflight pass BEFORE any writes.
    const patch = `[good.ts#${gTag}]\nSWAP 1.=1:\n+A\n[other.ts#0000]\nSWAP 99.=99:\n+X\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow();
    // Neither file changed.
    expect(env.fs.get('good.ts')).toEqual(good);
    expect(env.fs.get('other.ts')).toEqual(other);
  });

  test('multiple sections on the same file merge into one batch', async () => {
    const src = '1\n2\n3\n4\n5\n';
    const env = makeEnv({ 'm.ts': src });
    const t = tag(src);
    // Two sections against the same path with the same tag: parser merges
    // them so line numbers all reference the original snapshot.
    const patch = `[m.ts#${t}]\nSWAP 1.=1:\n+ONE\n` + `[m.ts#${t}]\nSWAP 5.=5:\n+FIVE\n`;
    await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('m.ts')).toEqual('ONE\n2\n3\n4\nFIVE\n');
  });

  test('two sections resolve to the same canonical path → reject', async () => {
    const env = makeEnv({ 'dup.ts': 'x\n' });
    const t = tag('x\n');
    // Two sections with different casing/paths that canonicalize to the same
    // file. Under InMemoryFilesystem paths are compared literally, so we use
    // the same literal path with tags that differ; the mergeSamePathSections
    // path catches this at parse time.
    const patch = `[dup.ts#${t}]\nSWAP 1.=1:\n+A\n` + `[dup.ts#${t}]\nSWAP 1.=1:\n+B\n`;
    // Both target line 1 → overlap rejection surfaces on apply.
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow();
  });

  test('cross-file multi-section applies both files when all valid', async () => {
    const env = makeEnv({ 'a.ts': 'x\n', 'b.ts': 'y\n' });
    const patch =
      `[a.ts#${tag('x\n')}]\nSWAP 1.=1:\n+X\n` + `[b.ts#${tag('y\n')}]\nSWAP 1.=1:\n+Y\n`;
    const result = await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('a.ts')).toEqual('X\n');
    expect(env.fs.get('b.ts')).toEqual('Y\n');
    expect(result.sections.map((s) => s.op).sort()).toEqual(['update', 'update']);
  });

  test('no-op section (edit result === input) is rejected in a multi-section batch', async () => {
    const env = makeEnv({ 'a.ts': 'foo\n', 'b.ts': 'bar\n' });
    const tA = tag('foo\n');
    const tB = tag('bar\n');
    // SWAP replacing 'foo' with 'foo' is a no-op.
    const patch = `[a.ts#${tA}]\nSWAP 1.=1:\n+foo\n` + `[b.ts#${tB}]\nSWAP 1.=1:\n+BAR\n`;
    // First section is a no-op — rejected during preflight, before either
    // file lands.
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/no changes/i);
    expect(env.fs.get('a.ts')).toEqual('foo\n');
    expect(env.fs.get('b.ts')).toEqual('bar\n');
  });

  test('preflight surfaces every failure before touching disk', async () => {
    const tmp = await mkTempDir('hashline-atomic-');
    const nodeFs = new NodeFilesystem();
    const snapshots = new InMemorySnapshotStore();
    const patcher = new Patcher({ fs: nodeFs, snapshots });
    const pathA = path.join(tmp, 'a.ts');
    const pathB = path.join(tmp, 'b.ts');
    await fs.writeFile(pathA, 'aaa\n');
    await fs.writeFile(pathB, 'bbb\n');
    snapshots.record(nodeFs.canonicalPath(pathA), 'aaa\n');
    snapshots.record(nodeFs.canonicalPath(pathB), 'bbb\n');
    const tA = tag('aaa\n');
    const patch = `[${pathA}#${tA}]\nSWAP 1.=1:\n+AAA\n` + `[${pathB}#0000]\nSWAP 1.=1:\n+BBB\n`;
    await expect(patcher.apply(Patch.parse(patch))).rejects.toThrow();
    // Both files unchanged.
    expect(await fs.readFile(pathA, 'utf8')).toEqual('aaa\n');
    expect(await fs.readFile(pathB, 'utf8')).toEqual('bbb\n');
    await fs.rm(tmp, { recursive: true });
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Unicode & line-ending preservation
// ─────────────────────────────────────────────────────────────────────────

describe('unicode & CRLF round-trip', () => {
  test('CRLF is detected and restored on write', async () => {
    const tmp = await mkTempDir('hashline-crlf-');
    const nodeFs = new NodeFilesystem();
    const snapshots = new InMemorySnapshotStore();
    const patcher = new Patcher({ fs: nodeFs, snapshots });
    const p = path.join(tmp, 'crlf.txt');
    const original = 'one\r\ntwo\r\nthree\r\n';
    await fs.writeFile(p, original);
    snapshots.record(nodeFs.canonicalPath(p), original);
    // Tag is computed on normalized text; CRLF files hash the same as LF.
    const t = tag('one\ntwo\nthree\n');
    const patch = `[${p}#${t}]\nSWAP 2.=2:\n+TWO\n`;
    await patcher.apply(Patch.parse(patch));
    const after = await fs.readFile(p, 'utf8');
    expect(after).toEqual('one\r\nTWO\r\nthree\r\n');
    await fs.rm(tmp, { recursive: true });
  });

  test('UTF-8 BOM is preserved through a write', async () => {
    const tmp = await mkTempDir('hashline-bom-');
    const nodeFs = new NodeFilesystem();
    const snapshots = new InMemorySnapshotStore();
    const patcher = new Patcher({ fs: nodeFs, snapshots });
    const p = path.join(tmp, 'bom.txt');
    const original = '\uFEFFone\ntwo\n';
    await fs.writeFile(p, original);
    snapshots.record(nodeFs.canonicalPath(p), 'one\ntwo\n'); // BOM stripped
    const t = tag('one\ntwo\n');
    const patch = `[${p}#${t}]\nSWAP 1.=1:\n+ONE\n`;
    await patcher.apply(Patch.parse(patch));
    const after = await fs.readFile(p, 'utf8');
    expect(after.startsWith('\uFEFF')).toBe(true);
    expect(after).toEqual('\uFEFFONE\ntwo\n');
    await fs.rm(tmp, { recursive: true });
  });

  test('non-ASCII payload is passed through byte-identically', async () => {
    const original = 'a\nb\nc\n';
    const env = makeEnv({ 'u.ts': original });
    const t = tag(original);
    const payload = 'π = μ + ✓ // 日本語 🐘';
    const patch = `[u.ts#${t}]\nSWAP 2.=2:\n+${payload}\n`;
    await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('u.ts')).toEqual(`a\n${payload}\nc\n`);
  });

  test('trailing whitespace within a body row is preserved verbatim', async () => {
    const original = 'x\n';
    const env = makeEnv({ 't.ts': original });
    const t = tag(original);
    const patch = `[t.ts#${t}]\nSWAP 1.=1:\n+trailing   \n`;
    await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('t.ts')).toEqual('trailing   \n');
  });
});

// ─────────────────────────────────────────────────────────────────────────
// MV / REM: file-level operations
// ─────────────────────────────────────────────────────────────────────────

describe('MV / REM', () => {
  test('MV rewrites the source path and lands at DEST', async () => {
    const env = makeEnv({ 'from.ts': 'x\ny\n' });
    const t = tag('x\ny\n');
    const patch = `[from.ts#${t}]\nSWAP 1.=1:\n+X\nMV to.ts\n`;
    const result = await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('from.ts')).toBeUndefined();
    expect(env.fs.get('to.ts')).toEqual('X\ny\n');
    expect(result.sections[0].op).toEqual('update');
    expect(result.sections[0].moveDest).toEqual('to.ts');
  });

  test('MV to itself rejects', async () => {
    const env = makeEnv({ 'x.ts': 'x\n' });
    const t = tag('x\n');
    const patch = `[x.ts#${t}]\nSWAP 1.=1:\n+X\nMV x.ts\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/same/i);
  });

  test('REM deletes the file entirely', async () => {
    const env = makeEnv({ 'gone.ts': 'x\ny\n' });
    const t = tag('x\ny\n');
    const patch = `[gone.ts#${t}]\nREM\n`;
    const result = await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('gone.ts')).toBeUndefined();
    expect(result.sections[0].op).toEqual('delete');
  });

  test('REM combined with line edits rejects', async () => {
    const env = makeEnv({ 'a.ts': 'x\n' });
    const t = tag('x\n');
    const patch = `[a.ts#${t}]\nSWAP 1.=1:\n+X\nREM\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/REM/);
  });

  test('MV DEST with a quoted path containing spaces round-trips', async () => {
    const env = makeEnv({ 'from.ts': 'x\n' });
    const t = tag('x\n');
    const patch = `[from.ts#${t}]\nSWAP 1.=1:\n+X\nMV "with space/dest.ts"\n`;
    await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('from.ts')).toBeUndefined();
    expect(env.fs.get('with space/dest.ts')).toEqual('X\n');
  });

  test('REM on a file that does not exist rejects', async () => {
    const env = makeEnv();
    const patch = `[gone.ts#0000]\nREM\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow();
  });

  test('MV DEST path traversal is not blocked by the core FS abstraction', async () => {
    // NodeFilesystem does no jailing; the responsibility for path sandboxing
    // lives with the host. This test documents that: a `MV ../escape.ts`
    // succeeds against NodeFilesystem if the parent directory is writable.
    // Host projects that need a jail must subclass NodeFilesystem and
    // override preflightWrite/canonicalPath.
    const tmp = await mkTempDir('hashline-mv-');
    const inner = path.join(tmp, 'inner');
    await fs.mkdir(inner);
    const source = path.join(inner, 's.ts');
    await fs.writeFile(source, 'z\n');
    const nodeFs = new NodeFilesystem();
    const snapshots = new InMemorySnapshotStore();
    const patcher = new Patcher({ fs: nodeFs, snapshots });
    snapshots.record(nodeFs.canonicalPath(source), 'z\n');
    const t = tag('z\n');
    const escaped = path.join(tmp, 'escape.ts');
    const patch = `[${source}#${t}]\nSWAP 1.=1:\n+Z\nMV ${escaped}\n`;
    await patcher.apply(Patch.parse(patch));
    // The write did land — the FS does not sandbox. Assert that so the
    // contract is explicit; a hosted variant must subclass to prevent it.
    expect(await fs.readFile(escaped, 'utf8')).toEqual('Z\n');
    await fs.rm(tmp, { recursive: true });
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Body-row edge cases
// ─────────────────────────────────────────────────────────────────────────

describe('INS.HEAD / INS.TAIL', () => {
  test('INS.HEAD prepends to the file', async () => {
    const env = makeEnv({ 'a.ts': 'one\ntwo\n' });
    const t = tag('one\ntwo\n');
    const patch = `[a.ts#${t}]\nINS.HEAD:\n+banner\n`;
    await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('a.ts')).toEqual('banner\none\ntwo\n');
  });

  test('INS.TAIL appends before a trailing newline', async () => {
    const env = makeEnv({ 'a.ts': 'one\ntwo\n' });
    const t = tag('one\ntwo\n');
    const patch = `[a.ts#${t}]\nINS.TAIL:\n+trailer\n`;
    await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('a.ts')).toEqual('one\ntwo\ntrailer\n');
  });

  test('INS.HEAD on a file with no tag still requires a tag', async () => {
    const env = makeEnv({ 'a.ts': 'x\n' });
    const patch = `[a.ts]\nINS.HEAD:\n+banner\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/snapshot tag/i);
  });
});

describe('body rows', () => {
  test('a `+` alone inserts a blank line', async () => {
    const env = makeEnv({ 'a.ts': 'x\ny\n' });
    const t = tag('x\ny\n');
    const patch = `[a.ts#${t}]\nINS.POST 1:\n+\n+z\n`;
    await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('a.ts')).toEqual('x\n\nz\ny\n');
  });

  test('a body row starting with `-` needs to be prefixed `+-…`', async () => {
    const env = makeEnv({ 'a.ts': 'x\n' });
    const t = tag('x\n');
    const patch = `[a.ts#${t}]\nSWAP 1.=1:\n+-flag\n`;
    await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('a.ts')).toEqual('-flag\n');
  });

  test('bare `-old` in a body rejects', async () => {
    const env = makeEnv({ 'a.ts': 'x\n' });
    const t = tag('x\n');
    const patch = `[a.ts#${t}]\nSWAP 1.=1:\n-x\n+y\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/rows are not valid/i);
  });

  test('SWAP with an empty body rejects with the DEL suggestion', async () => {
    const env = makeEnv({ 'a.ts': 'x\ny\n' });
    const t = tag('x\ny\n');
    const patch = `[a.ts#${t}]\nSWAP 1.=1:\n\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/needs at least one/i);
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Block ops: parse-time forward compatibility, but no resolver
// ─────────────────────────────────────────────────────────────────────────

describe('unsupported block ops', () => {
  test('SWAP.BLK without a resolver throws with the fallback suggestion', async () => {
    const env = makeEnv({ 'a.ts': 'function f() {\n  return 1;\n}\n' });
    const t = tag('function f() {\n  return 1;\n}\n');
    const patch = `[a.ts#${t}]\nSWAP.BLK 1:\n+function f() { return 2; }\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(
      /SWAP\.BLK|resolver|block/i,
    );
  });

  test('DEL.BLK without a resolver throws', async () => {
    const env = makeEnv({ 'a.ts': 'function f() {\n  return 1;\n}\n' });
    const t = tag('function f() {\n  return 1;\n}\n');
    const patch = `[a.ts#${t}]\nDEL.BLK 1\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow();
  });

  test('INS.BLK.POST without a resolver lowers to plain INS.POST with warning', async () => {
    const env = makeEnv({ 'a.ts': 'a\nb\n' });
    const t = tag('a\nb\n');
    const patch = `[a.ts#${t}]\nINS.BLK.POST 1:\n+X\n`;
    const result = await env.patcher.apply(Patch.parse(patch));
    // Lowered form should apply, with a warning telling the model to verify.
    expect(env.fs.get('a.ts')).toEqual('a\nX\nb\n');
    expect(result.sections[0].warnings.some((w) => /INS\.BLK\.POST/.test(w))).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Anchored-vs-unseen guard
// ─────────────────────────────────────────────────────────────────────────

describe('seen-line guard', () => {
  test('edit anchored on a line the read never displayed rejects', async () => {
    const original = '1\n2\n3\n4\n5\n';
    const env = makeEnv();
    env.fs.set('a.ts', original);
    // Record the tag but claim only lines 1 and 2 were displayed.
    const t = env.snapshots.record(env.fs.canonicalPath('a.ts'), original, [1, 2]);
    const patch = `[a.ts#${t}]\nSWAP 4.=4:\n+FOUR\n`;
    await expect(env.patcher.apply(Patch.parse(patch))).rejects.toThrow(/never displayed/i);
    // File unchanged.
    expect(env.fs.get('a.ts')).toEqual(original);
  });

  test('edit whose anchors are all in the seen set succeeds', async () => {
    const original = '1\n2\n3\n';
    const env = makeEnv();
    env.fs.set('a.ts', original);
    const t = env.snapshots.record(env.fs.canonicalPath('a.ts'), original, [1, 2, 3]);
    const patch = `[a.ts#${t}]\nSWAP 2.=2:\n+TWO\n`;
    await env.patcher.apply(Patch.parse(patch));
    expect(env.fs.get('a.ts')).toEqual('1\nTWO\n3\n');
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Streaming / partial-input helpers stay pure
// ─────────────────────────────────────────────────────────────────────────

describe('parse purity', () => {
  test('parse of a well-formed patch does no I/O', () => {
    const p = Patch.parse(`[a.ts#0000]\nSWAP 1.=1:\n+q\n`);
    expect(p.sections.length).toBe(1);
    expect(p.sections[0].path).toEqual('a.ts');
    expect(p.sections[0].fileHash).toEqual('0000');
  });

  test('applyTo runs edits against an in-memory string without a Patcher', () => {
    const p = Patch.parse(`[a.ts#${tag('a\nb\n')}]\nSWAP 1.=1:\n+A\n`);
    const result = p.sections[0].applyTo('a\nb\n');
    expect(result.text).toEqual('A\nb\n');
    expect(result.firstChangedLine).toEqual(1);
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Formatted headers round-trip
// ─────────────────────────────────────────────────────────────────────────

describe('header formatting', () => {
  test('formatHashlineHeader emits parseable output', () => {
    const h = header('some/file.ts', 'contents\n');
    expect(h).toMatch(/^\[some\/file\.ts#[0-9A-F]{4}\]$/);
    const parsed = Patch.parse(`${h}\nSWAP 1.=1:\n+X\n`);
    expect(parsed.sections[0].path).toEqual('some/file.ts');
  });
});

// ─────────────────────────────────────────────────────────────────────────
// Regression: the unused-warning defect in messages.ts stays fixed
// ─────────────────────────────────────────────────────────────────────────

describe('regression', () => {
  test('bare-hunk-overlap-coalesced warning is exported', async () => {
    // Import through the barrel; the defect was a bare template literal
    // that produced no export. This test locks in the fix.
    const messages = await import('../src/vendor/messages.ts');
    // The export exists as a plain string constant.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const m = messages as unknown as Record<string, string>;
    expect(typeof m.BARE_HUNK_OVERLAP_COALESCED_WARNING).toEqual('string');
    expect(m.BARE_HUNK_OVERLAP_COALESCED_WARNING.length).toBeGreaterThan(0);
  });
});
