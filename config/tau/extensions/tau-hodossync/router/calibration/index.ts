// Calibration system — sync LLM classifier with confusion-matrix learning

export type {
	SessionCalibration,
	GlobalCalibrationSnapshot,
	TraceRecord,
	CalibrationConfig,
	TierIndex,
} from "./types.ts";

export {
	initSessionCalibration,
	updateCalibrationMatrix,
	applyCalibratedTier,
	computeAgreementRate,
	computeMismatchRate,
	tierToIndex,
	indexToTier,
} from "./session.ts";

export {
	loadGlobalCalibration,
	mergeSessionIntoGlobal,
	saveGlobalSnapshot,
	resetGlobalCalibration,
	cancelPendingSave,
} from "./global.ts";

export {
	openTraceFile,
	appendTraceRecord,
	truncatePrompt,
} from "./trace.ts";
