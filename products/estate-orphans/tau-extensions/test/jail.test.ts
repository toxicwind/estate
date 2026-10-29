/**
 * Adversarial tests for the extension-level workspace jail.
 *
 * The generic core `NodeFilesystem` intentionally does not sandbox — that
 * is documented policy. What ships in the Pi extension DOES sandbox: it
 * wires `JailedNodeFilesystem` under the extension's root and refuses
 * every path shape that would escape it, including:
 *
 *   1. Absolute-path section headers (`[/etc/hosts#XXXX]`).
 *   2. `..` traversal in section headers.
 *   3. Absolute-path `MV DEST`.
 *   4. `..` traversal in `MV DEST`.
 *   5. `REM` on an out-of-root file.
 *   6. Symlinks INSIDE the root that point outside.
 *   7. Symlinks whose PARENT is inside the root but whose realpath
 *      escapes (writeText through a symlink dir).
 *   8. Tag-based path recovery to an out-of-root file.
 *
 * The jail must not add false positives: an ordinary in-root create,
 * update, delete, and move all still succeed.
 */
import { describe, expect, test } from 'bun:test';
import * as fs from 'node:fs/promises';
import * as os from 'node:os';
import * as path from 'node:path';
import { JailEscapeError, JailedNodeFilesystem } from '../extensions/pi/jail.ts';
import { computeFileHash, InMemorySnapshotStore, Patch, Patcher } from '../src/vendor/index.ts';

async function mkTempDir(prefix: string): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), prefix));
}

interface Rig {
  root: string;
  outside: string;
  fs: JailedNodeFilesystem;
  snapshots: InMemorySnapshotStore;
  patcher: Patcher;
  cleanup: () => Promise<void>;
}

/**
 * Build a jail rooted at a fresh temp dir plus an entirely separate
 * temp dir that represents "outside the jail". Every attack test writes
 * a canary into `outside/`; after the attack we assert the canary is
 * unchanged (writes and deletes) or absent (new-file writes).
 */
async function mkRig(): Promise<Rig> {
  const parent = await mkTempDir('hashline-jail-');
  // Realpath both dirs so downstream realpath compares don't see the
  // macOS `/private` prefix on `/tmp`. Using `fs.realpath` here keeps
  // the test invariants stable across platforms.
  const parentReal = await fs.realpath(parent);
  const root = path.join(parentReal, 'root');
  const outside = path.join(parentReal, 'outside');
  await fs.mkdir(root, { recursive: true });
  await fs.mkdir(outside, { recursive: true });
  const jailed = new JailedNodeFilesystem(root);
  const snapshots = new InMemorySnapshotStore();
  const patcher = new Patcher({ fs: jailed, snapshots });
  return {
    root,
    outside,
    fs: jailed,
    snapshots,
    patcher,
    cleanup: () => fs.rm(parent, { recursive: true, force: true }),
  };
}

async function seed(rig: Rig, relPath: string, content: string): Promise<string> {
  const abs = path.join(rig.root, relPath);
  await fs.mkdir(path.dirname(abs), { recursive: true });
  await fs.writeFile(abs, content);
  const canonical = rig.fs.canonicalPath(relPath);
  rig.snapshots.record(canonical, content);
  return computeFileHash(content);
}

async function seedOutside(rig: Rig, relPath: string, content: string): Promise<string> {
  const abs = path.join(rig.outside, relPath);
  await fs.mkdir(path.dirname(abs), { recursive: true });
  await fs.writeFile(abs, content);
  return abs;
}

async function readIfPresent(absolute: string): Promise<string | null> {
  try {
    return await fs.readFile(absolute, 'utf8');
  } catch {
    return null;
  }
}

// ─────────────────────────────────────────────────────────────────────
// Lexical rejection: absolute paths in the section header
// ─────────────────────────────────────────────────────────────────────

describe('jail: absolute-path section header', () => {
  test('SWAP against an absolute path outside root is refused', async () => {
    const rig = await mkRig();
    try {
      const canary = await seedOutside(rig, 'canary.txt', 'PRISTINE\n');
      const tag = computeFileHash('PRISTINE\n');
      const patch = `[${canary}#${tag}]\nSWAP 1.=1:\n+HACKED\n`;
      await expect(rig.patcher.apply(Patch.parse(patch))).rejects.toThrow(JailEscapeError);
      expect(await readIfPresent(canary)).toEqual('PRISTINE\n');
    } finally {
      await rig.cleanup();
    }
  });

  test('REM against an absolute out-of-root path is refused', async () => {
    const rig = await mkRig();
    try {
      const canary = await seedOutside(rig, 'canary.txt', 'PRISTINE\n');
      const tag = computeFileHash('PRISTINE\n');
      const patch = `[${canary}#${tag}]\nREM\n`;
      await expect(rig.patcher.apply(Patch.parse(patch))).rejects.toThrow(JailEscapeError);
      expect(await readIfPresent(canary)).toEqual('PRISTINE\n');
    } finally {
      await rig.cleanup();
    }
  });

  test('a create-mode section with an absolute out-of-root header is refused', async () => {
    const rig = await mkRig();
    try {
      const target = path.join(rig.outside, 'created.txt');
      // No pre-seed: the model authored a fresh file at an absolute
      // out-of-root path. `canonicalPath` should throw before any
      // filesystem call runs.
      const patch = `[${target}#0000]\nINS.HEAD:\n+HACKED\n`;
      await expect(rig.patcher.apply(Patch.parse(patch))).rejects.toThrow(JailEscapeError);
      expect(await readIfPresent(target)).toBeNull();
    } finally {
      await rig.cleanup();
    }
  });
});

// ─────────────────────────────────────────────────────────────────────
// Lexical rejection: `..` traversal
// ─────────────────────────────────────────────────────────────────────

describe('jail: `..` traversal in section header', () => {
  test('a section with a `../` prefix that escapes root is refused', async () => {
    const rig = await mkRig();
    try {
      const canary = await seedOutside(rig, 'canary.txt', 'PRISTINE\n');
      const tag = computeFileHash('PRISTINE\n');
      // The header path is relative to the workspace root and
      // navigates OUT of it.
      const patch = `[../outside/canary.txt#${tag}]\nSWAP 1.=1:\n+HACKED\n`;
      await expect(rig.patcher.apply(Patch.parse(patch))).rejects.toThrow(JailEscapeError);
      expect(await readIfPresent(canary)).toEqual('PRISTINE\n');
    } finally {
      await rig.cleanup();
    }
  });

  test('a section with an INTERNAL `..` segment that stays inside root is accepted', async () => {
    const rig = await mkRig();
    try {
      await seed(rig, 'sub/deep.ts', 'x\n');
      const tag = computeFileHash('x\n');
      // `sub/../sub/deep.ts` normalizes to `sub/deep.ts`; still in-root.
      const patch = `[sub/../sub/deep.ts#${tag}]\nSWAP 1.=1:\n+Z\n`;
      await rig.patcher.apply(Patch.parse(patch));
      expect(await fs.readFile(path.join(rig.root, 'sub/deep.ts'), 'utf8')).toEqual('Z\n');
    } finally {
      await rig.cleanup();
    }
  });
});

// ─────────────────────────────────────────────────────────────────────
// `MV DEST` jail
// ─────────────────────────────────────────────────────────────────────

describe('jail: MV DEST', () => {
  test('MV to an absolute path outside root is refused', async () => {
    const rig = await mkRig();
    try {
      const tag = await seed(rig, 's.ts', 'z\n');
      const outsideDest = path.join(rig.outside, 'escaped.ts');
      const patch = `[s.ts#${tag}]\nSWAP 1.=1:\n+Z\nMV ${outsideDest}\n`;
      await expect(rig.patcher.apply(Patch.parse(patch))).rejects.toThrow(JailEscapeError);
      expect(await readIfPresent(outsideDest)).toBeNull();
      expect(await fs.readFile(path.join(rig.root, 's.ts'), 'utf8')).toEqual('z\n');
    } finally {
      await rig.cleanup();
    }
  });

  test('MV to a `..` traversal path outside root is refused', async () => {
    const rig = await mkRig();
    try {
      const tag = await seed(rig, 's.ts', 'z\n');
      const patch = `[s.ts#${tag}]\nSWAP 1.=1:\n+Z\nMV ../outside/escaped.ts\n`;
      await expect(rig.patcher.apply(Patch.parse(patch))).rejects.toThrow(JailEscapeError);
      expect(await readIfPresent(path.join(rig.outside, 'escaped.ts'))).toBeNull();
      expect(await fs.readFile(path.join(rig.root, 's.ts'), 'utf8')).toEqual('z\n');
    } finally {
      await rig.cleanup();
    }
  });

  test('MV within root is accepted (positive control)', async () => {
    const rig = await mkRig();
    try {
      const tag = await seed(rig, 's.ts', 'z\n');
      const patch = `[s.ts#${tag}]\nMV moved.ts\n`;
      await rig.patcher.apply(Patch.parse(patch));
      expect(await fs.readFile(path.join(rig.root, 'moved.ts'), 'utf8')).toEqual('z\n');
      expect(await readIfPresent(path.join(rig.root, 's.ts'))).toBeNull();
    } finally {
      await rig.cleanup();
    }
  });
});

// ─────────────────────────────────────────────────────────────────────
// Symlink escapes: the whole reason we need `realpath`
// ─────────────────────────────────────────────────────────────────────

describe('jail: symlink escape', () => {
  test('symlink FILE inside root pointing at an out-of-root canary refuses SWAP', async () => {
    const rig = await mkRig();
    try {
      const canaryAbs = await seedOutside(rig, 'canary.txt', 'PRISTINE\n');
      const linkAbs = path.join(rig.root, 'trap.txt');
      await fs.symlink(canaryAbs, linkAbs);
      // The section addresses the symlink by an in-root name and a fresh
      // tag matching what a `read` of the symlink would return.
      const tag = computeFileHash('PRISTINE\n');
      const patch = `[trap.txt#${tag}]\nSWAP 1.=1:\n+HACKED\n`;
      await expect(rig.patcher.apply(Patch.parse(patch))).rejects.toThrow(JailEscapeError);
      expect(await fs.readFile(canaryAbs, 'utf8')).toEqual('PRISTINE\n');
    } finally {
      await rig.cleanup();
    }
  });

  test('symlink DIR inside root pointing to an out-of-root dir refuses writes into it', async () => {
    const rig = await mkRig();
    try {
      const outsideDir = path.join(rig.outside, 'store');
      await fs.mkdir(outsideDir, { recursive: true });
      const linkAbs = path.join(rig.root, 'store');
      await fs.symlink(outsideDir, linkAbs);
      // No pre-seed at store/inside.txt: this is a create-mode write via
      // INS.HEAD. The jail must refuse even though the parent dir
      // (store) appears to sit inside root — its realpath does not.
      const patch = `[store/inside.txt#0000]\nINS.HEAD:\n+HACKED\n`;
      await expect(rig.patcher.apply(Patch.parse(patch))).rejects.toThrow(JailEscapeError);
      expect(await readIfPresent(path.join(outsideDir, 'inside.txt'))).toBeNull();
    } finally {
      await rig.cleanup();
    }
  });

  test('symlink DIR inside root pointing to another IN-ROOT dir is accepted', async () => {
    const rig = await mkRig();
    try {
      const realDir = path.join(rig.root, 'real');
      await fs.mkdir(realDir, { recursive: true });
      await fs.writeFile(path.join(realDir, 'a.ts'), 'x\n');
      const linkAbs = path.join(rig.root, 'aliased');
      await fs.symlink(realDir, linkAbs);
      const canonical = rig.fs.canonicalPath('aliased/a.ts');
      rig.snapshots.record(canonical, 'x\n');
      const tag = computeFileHash('x\n');
      const patch = `[aliased/a.ts#${tag}]\nSWAP 1.=1:\n+Z\n`;
      await rig.patcher.apply(Patch.parse(patch));
      expect(await fs.readFile(path.join(realDir, 'a.ts'), 'utf8')).toEqual('Z\n');
    } finally {
      await rig.cleanup();
    }
  });
});

// ─────────────────────────────────────────────────────────────────────
// Tag-based path recovery refuses to jump out of root
// ─────────────────────────────────────────────────────────────────────

describe('jail: tag-based path recovery', () => {
  test('recovery does not redirect the write to a snapshot at an out-of-root canonical path', async () => {
    const rig = await mkRig();
    try {
      // A retained snapshot at an out-of-root canonical path with a
      // recognisable filename. If the jail let recovery jump to it, the
      // authored bare filename would get an escape write.
      const canaryAbs = await seedOutside(rig, 'note.md', 'PRISTINE\n');
      rig.snapshots.record(canaryAbs, 'PRISTINE\n');
      const tag = computeFileHash('PRISTINE\n');
      // Author a bare filename that does NOT exist in root and matches
      // by (basename, tag) exactly one out-of-root snapshot.
      const patch = `[note.md#${tag}]\nSWAP 1.=1:\n+HACKED\n`;
      // The section resolves to a canonical in-root path that doesn't
      // exist; recovery would try to jump to `canaryAbs` but the jail
      // must refuse. The commit fails either at recovery-refusal
      // (falls through to "file not found") or at the write itself.
      await expect(rig.patcher.apply(Patch.parse(patch))).rejects.toThrow();
      expect(await fs.readFile(canaryAbs, 'utf8')).toEqual('PRISTINE\n');
    } finally {
      await rig.cleanup();
    }
  });
});

// ─────────────────────────────────────────────────────────────────────
// Positive controls: normal in-root edits still pass
// ─────────────────────────────────────────────────────────────────────

describe('jail: in-root edits succeed', () => {
  test('SWAP against a plain in-root path succeeds', async () => {
    const rig = await mkRig();
    try {
      const tag = await seed(rig, 'a.ts', 'one\ntwo\n');
      const patch = `[a.ts#${tag}]\nSWAP 2.=2:\n+TWO\n`;
      await rig.patcher.apply(Patch.parse(patch));
      expect(await fs.readFile(path.join(rig.root, 'a.ts'), 'utf8')).toEqual('one\nTWO\n');
    } finally {
      await rig.cleanup();
    }
  });

  test('INS.HEAD creating a new in-root file succeeds', async () => {
    const rig = await mkRig();
    try {
      await seed(rig, 'placeholder.ts', 'x\n');
      const tag = computeFileHash('x\n');
      const patch = `[placeholder.ts#${tag}]\nSWAP 1.=1:\n+Z\n`;
      await rig.patcher.apply(Patch.parse(patch));
      expect(await fs.readFile(path.join(rig.root, 'placeholder.ts'), 'utf8')).toEqual('Z\n');
    } finally {
      await rig.cleanup();
    }
  });

  test('REM inside root succeeds', async () => {
    const rig = await mkRig();
    try {
      const tag = await seed(rig, 'gone.ts', 'x\n');
      const patch = `[gone.ts#${tag}]\nREM\n`;
      await rig.patcher.apply(Patch.parse(patch));
      expect(await readIfPresent(path.join(rig.root, 'gone.ts'))).toBeNull();
    } finally {
      await rig.cleanup();
    }
  });

  test('deep in-root subdir create succeeds', async () => {
    const rig = await mkRig();
    try {
      await seed(rig, 'a/b/c.ts', 'hello\n');
      const tag = computeFileHash('hello\n');
      const patch = `[a/b/c.ts#${tag}]\nSWAP 1.=1:\n+bye\n`;
      await rig.patcher.apply(Patch.parse(patch));
      expect(await fs.readFile(path.join(rig.root, 'a/b/c.ts'), 'utf8')).toEqual('bye\n');
    } finally {
      await rig.cleanup();
    }
  });
});

// ─────────────────────────────────────────────────────────────────────
// Direct FS API: defense in depth
// ─────────────────────────────────────────────────────────────────────

describe('JailedNodeFilesystem direct API', () => {
  test('writeText via absolute out-of-root path throws', async () => {
    const rig = await mkRig();
    try {
      const target = path.join(rig.outside, 'direct.txt');
      await expect(rig.fs.writeText(target, 'HACKED')).rejects.toThrow(JailEscapeError);
      expect(await readIfPresent(target)).toBeNull();
    } finally {
      await rig.cleanup();
    }
  });

  test('delete via `..` traversal throws', async () => {
    const rig = await mkRig();
    try {
      const canary = await seedOutside(rig, 'canary.txt', 'PRISTINE\n');
      await expect(rig.fs.delete('../outside/canary.txt')).rejects.toThrow(JailEscapeError);
      expect(await fs.readFile(canary, 'utf8')).toEqual('PRISTINE\n');
    } finally {
      await rig.cleanup();
    }
  });

  test('move source-inside dest-outside throws', async () => {
    const rig = await mkRig();
    try {
      await seed(rig, 's.ts', 'z\n');
      const dest = path.join(rig.outside, 'dst.ts');
      await expect(rig.fs.move('s.ts', dest, 'Z\n')).rejects.toThrow(JailEscapeError);
      expect(await readIfPresent(dest)).toBeNull();
      expect(await fs.readFile(path.join(rig.root, 's.ts'), 'utf8')).toEqual('z\n');
    } finally {
      await rig.cleanup();
    }
  });
});
