/** @type {string | null} */
let stickyTargetId = null;

/** Models that failed this turn (rate-limit exhaustion or overflow). */
/** @type {Set<string>} */
let turnFailedIds = new Set();

export function getStickyTarget() {
	return stickyTargetId;
}

/** @param {string | null} modelId */
export function setStickyTarget(modelId) {
	stickyTargetId = modelId;
}

export function resetRouterState() {
	stickyTargetId = null;
	turnFailedIds = new Set();
}

export function resetTurnFailures() {
	turnFailedIds = new Set();
}

/** @param {string} modelId */
export function markTurnFailure(modelId) {
	turnFailedIds.add(modelId);
}

export function getTurnFailures() {
	return turnFailedIds;
}
