import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import type { ExtensionAPI } from 'tau';
import { Type } from 'typebox';
import {
  InMemorySnapshotStore,
  Patch,
  Patcher,
  type PatchSectionResult,
} from '../../src/vendor/index.ts';
import { JailEscapeError, JailedNodeFilesystem } from './jail.ts';

const PROMPT_PATH = fileURLToPath(new URL('../../src/vendor/prompt.md', import.meta.url));
const HASHLINE_PROMPT = readFileSync(PROMPT_PATH, 'utf8');

const BLOCK_OP_WARNING =
  'block ops (SWAP.BLK/DEL.BLK) are not supported in v1 — no tree-sitter resolver is wired. SWAP.BLK and DEL.BLK hard-fail; INS.BLK.POST lowers to plain INS.POST with a warning. Re-author with concrete line ranges (SWAP N.=M / DEL N / INS.POST N).';

/**
 * Detect that the *patch structure itself* uses a block op — i.e. a line
 * whose first non-whitespace token is `SWAP.BLK`, `DEL.BLK`, or
 * `INS.BLK.POST`, and which is NOT a body row (body rows start with `+`).
 *
 * A raw substring test (`/SWAP\.BLK|.../.test(patch)`) matched body-text
 * mentions like `+// see SWAP.BLK docs`, producing spurious warnings on
 * every patch whose payload merely discussed block ops. This walks each
 * line, skips body rows (`+…`), and reports true only for a real op
 * header.
 */
function patchUsesBlockOps(patch: string): boolean {
  for (const rawLine of patch.split(/\r?\n/)) {
    const line = rawLine.trimStart();
    if (line.length === 0) continue;
    if (line.startsWith('+')) continue; // Body row.
    if (line.startsWith('[')) continue; // Section header.
    // A header line here is an op line. Check the first token.
    const firstToken = line.split(/[\s]/, 1)[0] ?? '';
    if (firstToken === 'SWAP.BLK' || firstToken === 'DEL.BLK' || firstToken === 'INS.BLK.POST') {
      return true;
    }
  }
  return false;
}

function summarizeSection(result: PatchSectionResult): string {
  const lines = [`[${result.header}] ${result.op}`];
  if (result.firstChangedLine !== undefined)
    lines.push(`  first changed line: ${result.firstChangedLine}`);
  if (result.moveDest) lines.push(`  moved to: ${result.moveDest}`);
  for (const warning of result.warnings) lines.push(`  warning: ${warning}`);
  return lines.join('\n');
}

function errorResponse(text: string, details: Record<string, unknown>) {
  return { content: [{ type: 'text' as const, text }], details };
}

/**
 * Options for `createHashlineExtension`. Kept minimal on purpose; the
 * only knob is the workspace root, which defaults to `process.cwd()` at
 * extension-init time.
 */
export interface HashlineExtensionOptions {
  /** Workspace root. Every path the model authors is jailed under this
   * root; writes outside are refused with `JailEscapeError`. */
  workspaceRoot?: string;
}

/**
 * Factory for the Pi extension. Exposed so tests can construct a patcher
 * wired against a specific root without spinning up the full Pi runtime.
 */
export function createHashlineExtension(options: HashlineExtensionOptions = {}) {
  const root = options.workspaceRoot ?? process.cwd();
  const jailedFs = new JailedNodeFilesystem(root);
  const snapshots = new InMemorySnapshotStore();
  const patcher = new Patcher({ fs: jailedFs, snapshots });
  return { fs: jailedFs, snapshots, patcher, root };
}

export default async function (pi: ExtensionAPI) {
  const { fs: jailedFs, snapshots, patcher, root } = createHashlineExtension();

  pi.registerTool({
    name: 'hashline',
    label: 'Hashline Edit',
    description: HASHLINE_PROMPT,
    parameters: Type.Object({
      patch: Type.String({
        description: 'A hashline patch: one or more [PATH#TAG] sections',
      }),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
      let patch: Patch;
      try {
        patch = Patch.parse(params.patch);
      } catch (error) {
        return errorResponse(`hashline parse error: ${(error as Error).message}`, {
          error: (error as Error).message,
        });
      }

      // v1 stale-anchor safety net: mint the current tag for every
      // in-jail section path before applying so a section anchored on
      // stale content is rejected with a clear "re-read" message instead
      // of silently drifting through recovery.
      //
      // Reject jail escapes here too, before we ever read anything, so:
      //   - the snapshot store is not polluted with tags for
      //     out-of-jail paths (privacy: an embedder's own tracker never
      //     sees a filename the model authored but the jail refused);
      //   - the error message names the exact section that was refused.
      for (const section of patch.sections) {
        let canonical: string;
        try {
          canonical = jailedFs.canonicalPath(section.path);
        } catch (error) {
          if (error instanceof JailEscapeError) {
            return errorResponse(`hashline refused section [${section.path}]: ${error.message}`, {
              error: 'jail_escape',
              path: section.path,
              root,
            });
          }
          throw error;
        }

        let currentText: string;
        try {
          currentText = await jailedFs.readText(section.path);
        } catch {
          // New file (create) — no current snapshot to mint; the
          // patcher itself validates whether a tag was required.
          continue;
        }
        const currentTag = snapshots.record(canonical, currentText);
        if (section.fileHash !== undefined && section.fileHash !== currentTag) {
          return errorResponse(
            `hashline stale tag for ${section.path}: patch names #${section.fileHash}, current content hashes to #${currentTag}. Re-read the file and rebuild the patch against its current content.`,
            {
              error: 'stale_tag',
              path: section.path,
              expected: currentTag,
              got: section.fileHash,
            },
          );
        }
      }

      const usesBlockOps = patchUsesBlockOps(params.patch);

      try {
        const result = await patcher.apply(patch);
        const summary = result.sections.map(summarizeSection).join('\n\n');
        const warnings = usesBlockOps ? `\n\nwarning: ${BLOCK_OP_WARNING}` : '';
        return {
          content: [{ type: 'text' as const, text: `${summary}${warnings}` }],
          details: { sections: result.sections },
        };
      } catch (error) {
        if (error instanceof JailEscapeError) {
          return errorResponse(`hashline refused write: ${error.message}`, {
            error: 'jail_escape',
            path: error.authoredPath,
            resolved: error.resolvedPath,
            root,
          });
        }
        return errorResponse(`hashline apply error: ${(error as Error).message}`, {
          error: (error as Error).message,
        });
      }
    },
  });
}
