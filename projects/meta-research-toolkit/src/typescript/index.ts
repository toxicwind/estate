// Entry point for the meta-research-toolkit TypeScript surface.
import { PromptOrchestrator } from "./prompts/orchestrator";
import { MetaClient } from "./api/meta-client";

export { PromptOrchestrator, MetaClient };
export type { Strategy, StrategyKind } from "./prompts/orchestrator";
export { ChatMessageSchema, ChatRequestSchema } from "./api/meta-client";
export type { ChatMessage, ChatRequest, MetaClientOptions } from "./api/meta-client";
export type { RefusalGeometryReport, LotteryAudit } from "./api/types";

if (import.meta.main) {
  const orchestrator = new PromptOrchestrator();
  const strategies = orchestrator.listStrategies();
  console.log(`Loaded ${strategies.length} prompt strategies`);
  for (const s of strategies) {
    console.log(`  - ${s.name} (${s.strategy})`);
  }
}
