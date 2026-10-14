/** Serialize NVIDIA API calls per provider+model to avoid parallel 429 storms. */

/** @type {Map<string, Promise<void>>} */
const tails = new Map();

/**
 * Run `fn` after any prior in-flight work for the same key completes.
 * Holds the slot until `fn` settles (including retry backoffs).
 *
 * @template T
 * @param {string} key
 * @param {() => Promise<T>} fn
 * @returns {Promise<T>}
 */
export async function withNvidiaRequestQueue(key, fn) {
	const prev = tails.get(key) ?? Promise.resolve();
	let release;
	const gate = new Promise((resolve) => {
		release = resolve;
	});
	tails.set(
		key,
		prev.then(() => gate),
	);
	await prev;
	try {
		return await fn();
	} finally {
		release();
		if (tails.get(key) === gate) {
			tails.delete(key);
		}
	}
}

/** @param {{ provider?: string; id?: string }} model */
export function nvidiaQueueKey(model) {
	return `${model?.provider ?? "nvidia"}:${model?.id ?? "<model>"}`;
}

/** @param {string} [key] */
export function resetNvidiaRequestQueue(key) {
	if (key) {
		tails.delete(key);
	} else {
		tails.clear();
	}
}
