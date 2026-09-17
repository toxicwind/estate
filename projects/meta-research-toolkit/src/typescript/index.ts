import { PromptOrchestrator } from "./prompts/orchestrator";
import { MetaClient } from "./api/meta-client";

export { PromptOrchestrator, MetaClient };

if (import.meta.main) {
  const orchestrator = new PromptOrchestrator();
  const strategies = orchestrator.listStrategies();
  console.log(`Loaded ${strategies.length} prompt strategies`);
  for (const s of strategies) {
    console.log(`  - ${s.name} (${s.strategy})`);
  }
}
