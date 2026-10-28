/** @type {((model: any, context: any, options: any) => any) | null} */
let retryWrappedStream = null;

/** @param {(model: any, context: any, options: any) => any} fn */
export function setRetryWrappedStream(fn) {
	retryWrappedStream = fn;
}

export function getRetryWrappedStream() {
	return retryWrappedStream;
}
