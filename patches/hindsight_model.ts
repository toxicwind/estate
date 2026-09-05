// ============================================================================
// Live Hotfix: hindsight.llm_model
// Author: sovereign
// Reason: Resolves the local model for Hindsight reflection on port 25100
// ============================================================================

export const TARGET = "hindsight.llm_model";
export const VERSION = "2.0.0";
export const AUTHOR = "sovereign";
export const REASON = "Upgrades Hindsight reflection engine to Qwen 3.5 9B 64K Flash (119 tok/s)";
export const ENABLED = true;

export const impl = "beellama/qwen-flash-64k";
