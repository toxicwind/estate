/**
 * Workspace jail for the shipped Pi extension.
 *
 * The generic core `NodeFilesystem` intentionally does no path sandboxing —
 * that's a per-host policy decision (see `src/vendor/fs.ts` header). This
 * module is the host-level policy: every path the model authors (in
 * section headers, in `MV DEST`, in `REM` targets, in tag-based path
 * recovery) is resolved against a fixed root and rejected if the
 * resolved path — including any symlink target — escapes that root.
 *
 * The jail is enforced at three checkpoints:
 *
 * 1. `canonicalPath` — every caller-supplied path becomes an absolute path
 *    inside the root or a `JailEscapeError`.
 * 2. `preflightWrite` — before any batched commit lands on disk, the
 *    patcher calls this per-target; we re-check with the file's own
 *    realpath (or its parent's realpath, if the file does not yet exist)
 *    to catch symlink escapes that a pure lexical resolve would miss.
 * 3. `allowTagPathRecovery` — a section whose authored path doesn't
 *    exist can be redirected to the file its tag matches. We refuse the
 *    redirect whenever the resolved destination is outside the root.
 *
 * The jail is intentionally strict: absolute paths in section headers,
 * `..` segments that escape the root, and symlinks that point outside the
 * root all fail loud with `JailEscapeError`. There is no "soft" mode.
 */
import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import {
  NodeFilesystem,
  type PreflightWriteOptions,
  type WriteResult,
} from '../../src/vendor/index.ts';

/**
 * Thrown when a caller-supplied path resolves outside the workspace root.
 * The message names the offending authored path and the resolved location
 * so the model can correct the section header and re-issue.
 */
export class JailEscapeError extends Error {
  readonly code = 'EJAILESCAPE';
  readonly authoredPath: string;
  readonly resolvedPath: string;

  constructor(authoredPath: string, resolvedPath: string, root: string, reason: string) {
    super(
      `path "${authoredPath}" is outside the workspace root (${root}): ${reason}. Re-author the section header as a path relative to the workspace root; hashline does not write outside its root.`,
    );
    this.name = 'JailEscapeError';
    this.authoredPath = authoredPath;
    this.resolvedPath = resolvedPath;
  }
}

function normalizedRoot(root: string): string {
  // Use path.resolve so a relative root (rare, but supported) becomes
  // absolute against the current cwd exactly once, at construction time.
  return path.resolve(root);
}

/**
 * Return the deepest existing ancestor of `absolute`. Used to resolve the
 * realpath of a file that does not yet exist: we cannot call `realpath`
 * on a non-existent path, but we can realpath the closest existing parent
 * and then re-attach the missing tail. If the tail is entirely lexical
 * (no symlinks), the composed absolute path is safe to compare against
 * the root.
 */
async function deepestExistingAncestor(
  absolute: string,
): Promise<{ ancestor: string; tail: string }> {
  let current = absolute;
  const tailParts: string[] = [];
  // Walk up until we find something that exists or hit the filesystem root.
  // At worst we bail at `/` (or `C:\` on Windows), which always exists.
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      await fs.access(current);
      return { ancestor: current, tail: tailParts.join(path.sep) };
    } catch {
      const parent = path.dirname(current);
      if (parent === current) {
        // We hit the volume root. The realpath check has to fall back to
        // the lexical form; that's still safe because a non-existent path
        // cannot smuggle a symlink escape it doesn't yet contain.
        return { ancestor: current, tail: tailParts.join(path.sep) };
      }
      tailParts.unshift(path.basename(current));
      current = parent;
    }
  }
}

async function realpathThroughAncestor(absolute: string): Promise<string> {
  try {
    return await fs.realpath(absolute);
  } catch {
    const { ancestor, tail } = await deepestExistingAncestor(absolute);
    let realAncestor: string;
    try {
      realAncestor = await fs.realpath(ancestor);
    } catch {
      realAncestor = ancestor;
    }
    return tail ? path.join(realAncestor, tail) : realAncestor;
  }
}

/**
 * Return true iff `child` is `root` or a strict descendant of `root` on
 * the same volume, using a path-segment-aware comparison. String-prefix
 * checks are unsafe: `/tmp/root-evil` starts with `/tmp/root` but is not
 * inside `/tmp/root`.
 */
function isPathWithin(root: string, child: string): boolean {
  const relative = path.relative(root, child);
  if (relative === '') return true;
  if (relative.startsWith('..')) return false;
  if (path.isAbsolute(relative)) return false;
  return true;
}

/**
 * Lexical resolution + rejection. Called on every path handed to the
 * jailed FS, including the recovery-store canonical paths that the
 * patcher round-trips through `canonicalPath`. Rules:
 *
 * - Empty path → resolves to root.
 * - Absolute path INSIDE root → accepted (identity, up to realpath).
 *   The patcher's snapshot-store recovery pass round-trips already
 *   canonical paths through here.
 * - Absolute path OUTSIDE root → rejected. Section headers cannot name
 *   `/etc/hosts` or any other out-of-root absolute target.
 * - Relative path that resolves inside root → accepted.
 * - Relative path with `..` that escapes root → rejected.
 */
function lexicalRejection(
  authored: string,
  root: string,
): { resolved: string; error?: JailEscapeError } {
  if (authored.length === 0) {
    return { resolved: root };
  }
  const resolved = path.isAbsolute(authored)
    ? path.resolve(authored)
    : path.resolve(root, authored);
  if (!isPathWithin(root, resolved)) {
    const reason = path.isAbsolute(authored)
      ? 'absolute paths outside the root are refused'
      : '`..` traversal escaped the root';
    return {
      resolved,
      error: new JailEscapeError(authored, resolved, root, reason),
    };
  }
  return { resolved };
}

/**
 * `NodeFilesystem` subclass that pins every read/write to `root` and
 * refuses paths that resolve outside it, whether the escape is lexical
 * (absolute path, `..` traversal) or symbolic (a symlink pointing out).
 *
 * Constructed by `extensions/pi/index.ts` with `root = process.cwd()`.
 */
export class JailedNodeFilesystem extends NodeFilesystem {
  readonly root: string;
  #realRoot: string | null = null;

  constructor(root: string) {
    super();
    this.root = normalizedRoot(root);
  }

  async #resolveRealRoot(): Promise<string> {
    if (this.#realRoot !== null) return this.#realRoot;
    try {
      this.#realRoot = await fs.realpath(this.root);
    } catch {
      this.#realRoot = this.root;
    }
    return this.#realRoot;
  }

  /**
   * Lexical resolution + rejection. Also used by the extension itself to
   * reject absolute-path section headers before the patcher runs. Symlink
   * escapes are caught in `preflightWrite` because they require an async
   * `realpath`.
   */
  canonicalPath(authoredPath: string): string {
    const { resolved, error } = lexicalRejection(authoredPath, this.root);
    if (error) throw error;
    return resolved;
  }

  /**
   * Async, symlink-aware jail check. Runs on the batch's canonical path
   * before commit for every write op (create, update, delete, move
   * destination). Reject if the realpath of the target — or of its
   * closest existing parent, for a to-be-created path — lands outside
   * the realpath of the root.
   */
  async preflightWrite(
    authoredOrCanonical: string,
    options?: PreflightWriteOptions,
  ): Promise<void> {
    const canonical = this.canonicalPath(authoredOrCanonical);
    const realRoot = await this.#resolveRealRoot();
    const realTarget = await realpathThroughAncestor(canonical);
    if (!isPathWithin(realRoot, realTarget)) {
      throw new JailEscapeError(
        authoredOrCanonical,
        realTarget,
        realRoot,
        'symlink or realpath resolves outside the root',
      );
    }
    if (options?.fileOp?.kind === 'move') {
      const dest = this.canonicalPath(options.fileOp.dest);
      const realDest = await realpathThroughAncestor(dest);
      if (!isPathWithin(realRoot, realDest)) {
        throw new JailEscapeError(
          options.fileOp.dest,
          realDest,
          realRoot,
          'symlink or realpath resolves outside the root',
        );
      }
    }
  }

  /**
   * Refuse tag-based path recovery to targets outside the jail. The
   * patcher will fall back to the "file not found" error, which is the
   * right thing: the model authored a path we cannot serve, and we do
   * not silently redirect the write to some other location.
   */
  allowTagPathRecovery(_authoredPath: string, resolvedPath: string): boolean {
    return isPathWithin(this.root, path.resolve(resolvedPath));
  }

  /**
   * Belt-and-braces guards for the direct write / delete / move APIs.
   *
   * Two invariants:
   *
   * 1. Every path is re-jailed here (defense in depth) — the patcher
   *    calls `preflightWrite` before the batch commits, but a bare
   *    `writeText` call bypasses that if a caller wires this FS into a
   *    different applier.
   * 2. The actual Node FS call uses the resolved absolute path, not the
   *    raw authored path. Node resolves relative paths against
   *    `process.cwd()`, which may drift from `this.root` (e.g. a batch
   *    that started in one dir and had cwd changed mid-run). Using the
   *    canonical absolute path from `this.root` closes that race.
   */
  async writeText(authoredPath: string, content: string): Promise<WriteResult> {
    const canonical = this.canonicalPath(authoredPath);
    await this.preflightWrite(authoredPath);
    return super.writeText(canonical, content);
  }

  async delete(authoredPath: string): Promise<void> {
    const canonical = this.canonicalPath(authoredPath);
    await this.preflightWrite(authoredPath);
    return super.delete(canonical);
  }

  async move(from: string, to: string, content?: string): Promise<void> {
    const canonicalFrom = this.canonicalPath(from);
    const canonicalTo = this.canonicalPath(to);
    await this.preflightWrite(from);
    await this.preflightWrite(to);
    return super.move(canonicalFrom, canonicalTo, content);
  }

  async readText(authoredPath: string): Promise<string> {
    const canonical = this.canonicalPath(authoredPath);
    return super.readText(canonical);
  }

  async readBinary(authoredPath: string): Promise<Uint8Array> {
    const canonical = this.canonicalPath(authoredPath);
    return super.readBinary(canonical);
  }

  async exists(authoredPath: string): Promise<boolean> {
    try {
      const canonical = this.canonicalPath(authoredPath);
      return super.exists(canonical);
    } catch {
      // A jail-escaping path does not "exist" from the extension's POV.
      return false;
    }
  }
}
