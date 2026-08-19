// Register llama-server provider in pi-agent
import { registerProvider } from "./registry.js";
import { llamaModels } from "./models.js";
import { llamaChat, llamaComplete, llamaSwap, llamaHealth, llamaProps, llamaTokenize, llamaEmbedding, mesh } from "./llama-server.js";

registerProvider({
  id: "llama-server",
  name: "llama.cpp server",
  models: llamaModels.map(m => ({ id: m.id, name: m.name, contextWindow: m.contextWindow })),
  defaultBaseUrl: "http://127.0.0.1:8080",
  supportsImages: false,
  supportsStreaming: true,
  supportsToolCalls: false,
  complete: llamaComplete,
  chat: llamaChat,
  swap: llamaSwap,
  health: llamaHealth,
  props: llamaProps,
  tokenize: llamaTokenize,
  embedding: llamaEmbedding,
  mesh: mesh,
});
