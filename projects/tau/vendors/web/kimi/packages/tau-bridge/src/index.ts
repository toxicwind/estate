/**
 * Tau Bridge — connects kimi-code to tau (oh-my-pi) engine
 * 
 * This replaces kimi-code's internal agent-core with tau's:
 * - pi-ai (provider registry + model resolution + auth)
 * - pi-coding-agent (session management + tools + SDK)
 * - pi-tui (TUI components)
 * - pi-utils (logging, dirs, process management)
 */

// Export tau bridge adapters
export * from "./tau-harness";
export * from "./prompt-harness";

// Re-export kimi-code SDK types for compatibility
export type {
  KimiConfig,
  ModelAlias,
  Session,
  SessionSummary,
  SessionStatus,
  Event,
  SkillSummary,
  TelemetryClient,
  TelemetryProperties,
  KimiHostIdentity,
  KimiAuthFacade,
  CreateSessionOptions,
  ListSessionsOptions,
  GetConfigOptions,
  ConfigDiagnostics,
  PromptInput,
  ApprovalHandler,
  QuestionHandler,
  Unsubscribe,
  KimiConfigPatch,
  KimiError,
  ErrorCodes,
  ImageLimits,
  TelemetryContextPatch,
} from "@moonshot-ai/kimi-code-sdk";

// Re-export tau engine types (explicit to avoid conflicts)
export type {
  Settings,
  AgentSession,
  CreateAgentSessionOptions,
  CreateAgentSessionResult,
  Model,
  Effort,
  ProviderSessionState,
  AgentState,
  PromptOptions,
} from "@oh-my-pi/pi-coding-agent";

import type { Model, Effort } from "@oh-my-pi/pi-catalog";
import { getBundledModel, getBundledProviders } from "@oh-my-pi/pi-catalog/models";
import { createAgentSession, CreateAgentSessionOptions, CreateAgentSessionResult } from "@oh-my-pi/pi-coding-agent";
import { Settings, ModelRegistry } from "@oh-my-pi/pi-coding-agent";
import { discoverAuthStorage } from "@oh-my-pi/pi-coding-agent";
import { logger } from "@oh-my-pi/pi-utils";
import { EventBus } from "@oh-my-pi/pi-coding-agent/utils/event-bus";
import type { KimiConfig, TelemetryClient, KimiHostIdentity } from "@moonshot-ai/kimi-code-sdk";

/**
 * Creates a Kimi-compatible session using tau's AgentSession
 */
export interface TauSessionOptions {
  cwd?: string;
  agentDir?: string;
  model?: Model;
  modelPattern?: string;
  thinkingLevel?: Effort;
  continueSession?: boolean;
  sessionManager?: any;
  settings?: Settings;
  eventBus?: any;
  workspaceTree?: any;
  contextFiles?: string[];
  promptTemplates?: any;
  slashCommands?: any;
  skills?: any;
  additionalExtensionPaths?: string[];
  extensionRoots?: any;
  getApiKey?: (provider: string) => Promise<string | undefined>;
  systemPrompt?: string[];
  tools?: any[];
}

/**
 * Adapter to make tau's AgentSession work as a Kimi session
 */
export class TauKimiSessionAdapter {
  private session: Awaited<ReturnType<typeof createAgentSession>>["session"];
  private result: CreateAgentSessionResult;

  constructor(session: Awaited<ReturnType<typeof createAgentSession>>["session"], result: CreateAgentSessionResult) {
    this.session = session;
    this.result = result;
  }

  get id(): string {
    return this.session.sessionId;
  }

  get status(): string {
    const state = this.session.state;
    return state === "running" ? "streaming" : state === "idle" ? "idle" : "error";
  }

  async prompt(message: string, options?: { signal?: AbortSignal }): Promise<void> {
    await this.session.prompt(message, options as any);
  }

  async close(): Promise<void> {
    await this.session.dispose();
  }
}

/**
 * Creates a session using tau engine (replaces KimiHarness.createSession)
 */
export async function createTauKimiSession(
  options: TauSessionOptions & {
    config: KimiConfig;
    auth: any;
    telemetry: TelemetryClient;
    identity?: KimiHostIdentity;
    homeDir: string;
    configPath: string;
    onClose: () => void | Promise<void>;
    imageLimits?: any;
  }
): Promise<TauKimiSessionAdapter> {
  const cwd = options.cwd ?? options.homeDir;
  const agentDir = options.agentDir ?? options.homeDir;

  let model = options.model;
  if (!model && options.modelPattern) {
    const [provider, ...modelParts] = options.modelPattern.split('/');
    model = getBundledModel(provider as any, modelParts.join('/'));
  }

  const tauOptions: CreateAgentSessionOptions = {
    cwd,
    agentDir,
    model,
    thinkingLevel: options.thinkingLevel,
    continueSession: options.continueSession,
    sessionManager: options.sessionManager,
    settings: options.settings,
    eventBus: options.eventBus,
    workspaceTree: options.workspaceTree,
    contextFiles: options.contextFiles,
    promptTemplates: options.promptTemplates,
    slashCommands: options.slashCommands,
    skills: options.skills,
    additionalExtensionPaths: options.additionalExtensionPaths,
    extensionRoots: options.extensionRoots,
    getApiKey: options.getApiKey,
    systemPrompt: options.systemPrompt,
    tools: options.tools,
  };

  const result = await createAgentSession(tauOptions);
  return new TauKimiSessionAdapter(result.session, result);
}

/**
 * Apply provider from models.dev catalog using tau's pi-ai registry
 */
export async function applyTauCatalogProvider(
  config: KimiConfig,
  providerId: string,
  modelId: string,
  options: { thinkingLevel?: Effort; effort?: Effort } = {}
): Promise<{ defaultModel: string }> {
  const model = getBundledModel(providerId as any, modelId);
  config.defaultModel = `${providerId}/${modelId}`;
  config.modelAliases ??= {};
  config.modelAliases[modelId] = { provider: providerId, model: modelId };
  
  if (options.thinkingLevel) {
    config.thinkingLevel = options.thinkingLevel;
  }
  
  return { defaultModel: config.defaultModel };
}

/**
 * Initialize tau engine for kimi-code
 */
export async function initializeTauEngine(
  homeDir: string,
  configPath: string
): Promise<{ settings: Settings; modelRegistry: any }> {
  const settings = await Settings.init({ cwd: homeDir, agentDir: homeDir });
  const { discoverAuthStorage } = await import("@oh-my-pi/pi-coding-agent");
  const { ModelRegistry } = await import("@oh-my-pi/pi-coding-agent");
  const { join } = await import("node:path");
  const { getModelDbPath } = await import("@oh-my-pi/pi-utils");

  const authStorage = await discoverAuthStorage(homeDir);
  const modelRegistry = new ModelRegistry(authStorage, join(homeDir, "models.yml"), {
    settings,
    cacheDbPath: getModelDbPath(homeDir),
  });

  await modelRegistry.hydrateCredentialScopedModelCaches();
  modelRegistry.refreshInBackground();

  return { settings, modelRegistry };
}

/**
 * Convert tau model to kimi model alias format
 */
export function tauModelToKimiAlias(model: Model): { provider: string; model: string } {
  return {
    provider: model.provider,
    model: model.id,
  };
}

/**
 * Get available providers from tau's registry
 */
export async function getTauProviders(): Promise<string[]> {
  return getBundledProviders();
}