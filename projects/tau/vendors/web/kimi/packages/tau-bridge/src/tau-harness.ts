/**
 * TauHarness — replaces KimiHarness using tau's oh-my-pi engine
 * 
 * This is a drop-in replacement that uses:
 * - @oh-my-pi/pi-ai for provider management
 * - @oh-my-pi/pi-coding-agent for session/agent management
 * - @oh-my-pi/pi-tui for TUI components
 */

import {
  ErrorCodes,
  KimiError,
  ImageLimits,
  type ExperimentalFeatureState,
} from '@moonshot-ai/agent-core';

import type { KimiAuthFacade } from '@moonshot-ai/kimi-code-sdk';
import type {
  AuthenticateMcpServerOptions,
  ConfigDiagnostics,
  CreateSessionOptions,
  ExportSessionInput,
  ExportSessionResult,
  ForkSessionInput,
  GetConfigOptions,
  KimiConfig,
  KimiConfigPatch,
  KimiHostIdentity,
  ListSessionsOptions,
  McpServerConfig,
  McpTestResult,
  RenameSessionInput,
  ResumeSessionInput,
  ReloadSessionInput,
  SessionSummary,
  SkillSummary,
  TelemetryClient,
  TelemetryContextPatch,
  TelemetryProperties,
  TestMcpServerOptions,
} from '@moonshot-ai/kimi-code-sdk';

import { createAgentSession, CreateAgentSessionOptions, CreateAgentSessionResult, AgentSession } from '@oh-my-pi/pi-coding-agent';
import { Settings, ModelRegistry } from '@oh-my-pi/pi-coding-agent';
import { getBundledModel, getBundledProviders } from '@oh-my-pi/pi-catalog/models';
import type { Model, Effort } from '@oh-my-pi/pi-catalog';
import { discoverAuthStorage } from '@oh-my-pi/pi-coding-agent';
import { logger } from '@oh-my-pi/pi-utils';
import { EventBus } from '@oh-my-pi/pi-coding-agent/utils/event-bus';
import { join } from 'node:path';
import { getModelDbPath } from '@oh-my-pi/pi-utils';

export interface TauHarnessRuntimeOptions {
  readonly identity?: KimiHostIdentity;
  readonly uiMode?: string;
  readonly homeDir: string;
  readonly configPath: string;
  readonly auth: KimiAuthFacade;
  readonly telemetry: TelemetryClient;
  readonly ensureConfigFile: () => Promise<void>;
  readonly onClose: () => void | Promise<void>;
  readonly sessionStartedProperties?: TelemetryProperties;
  readonly imageLimits?: ImageLimits;
}

export class TauHarness {
  private readonly options: TauHarnessRuntimeOptions;
  private settings: Settings | null = null;
  private modelRegistry: ModelRegistry | null = null;
  private eventBus: EventBus;
  private closed = false;

  constructor(options: TauHarnessRuntimeOptions) {
    this.options = options;
    this.eventBus = new EventBus();
  }

  async initialize(): Promise<void> {
    if (this.settings) return;

    const { homeDir } = this.options;
    
    this.settings = await Settings.init({ cwd: homeDir, agentDir: homeDir });
    
    const authStorage = await discoverAuthStorage(homeDir);
    this.modelRegistry = new ModelRegistry(authStorage, join(homeDir, 'models.yml'), {
      settings: this.settings,
      cacheDbPath: getModelDbPath(homeDir),
    });

    await this.modelRegistry.hydrateCredentialScopedModelCaches();
    this.modelRegistry.refreshInBackground();
  }

  getSettings(): Settings {
    if (!this.settings) {
      throw new KimiError('TauHarness not initialized', ErrorCodes.NOT_INITIALIZED);
    }
    return this.settings;
  }

  getModelRegistry(): ModelRegistry {
    if (!this.modelRegistry) {
      throw new KimiError('TauHarness not initialized', ErrorCodes.NOT_INITIALIZED);
    }
    return this.modelRegistry;
  }

  getEventBus(): EventBus {
    return this.eventBus;
  }

  async createSession(options: CreateSessionOptions): Promise<Session> {
    await this.initialize();

    const { model, modelPattern, thinkingLevel, continueSession, cwd, agentDir, ...restOptions } = options;

    let resolvedModel: Model | undefined;
    if (model) {
      resolvedModel = model;
    } else if (modelPattern) {
      const [provider, ...modelParts] = modelPattern.split('/');
      resolvedModel = getBundledModel(provider as any, modelParts.join('/'));
    }

    const tauOptions: CreateAgentSessionOptions = {
      cwd: cwd ?? this.options.homeDir,
      agentDir: agentDir ?? this.options.homeDir,
      model: resolvedModel,
      thinkingLevel: thinkingLevel as Effort | undefined,
      continueSession,
      settings: this.settings ?? undefined,
      eventBus: this.eventBus,
      ...restOptions,
    };

    const result = await createAgentSession(tauOptions);
    
    return new TauSessionAdapter(result.session, result);
  }

  async getConfig(_options: GetConfigOptions): Promise<KimiConfig> {
    await this.initialize();
    return {
      defaultModel: this.settings?.get('model') ?? 'anthropic/claude-opus-4-5',
      modelAliases: {},
      thinkingLevel: 'high',
    } as KimiConfig;
  }

  async updateConfig(_patch: KimiConfigPatch): Promise<KimiConfig> {
    await this.initialize();
    return this.getConfig({} as GetConfigOptions);
  }

  async listSessions(_options: ListSessionsOptions): Promise<SessionSummary[]> {
    return [];
  }

  async renameSession(_input: RenameSessionInput): Promise<void> {
  }

  async exportSession(_input: ExportSessionInput): Promise<ExportSessionResult> {
    throw new KimiError('Not implemented', ErrorCodes.NOT_IMPLEMENTED);
  }

  async forkSession(_input: ForkSessionInput): Promise<Session> {
    throw new KimiError('Not implemented', ErrorCodes.NOT_IMPLEMENTED);
  }

  async resumeSession(_input: ResumeSessionInput): Promise<Session> {
    throw new KimiError('Not implemented', ErrorCodes.NOT_IMPLEMENTED);
  }

  async reloadSession(_input: ReloadSessionInput): Promise<Session> {
    throw new KimiError('Not implemented', ErrorCodes.NOT_IMPLEMENTED);
  }

  async authenticateMcpServer(_options: AuthenticateMcpServerOptions): Promise<void> {
    throw new KimiError('Not implemented', ErrorCodes.NOT_IMPLEMENTED);
  }

  async testMcpServer(_options: TestMcpServerOptions): Promise<McpTestResult> {
    throw new KimiError('Not implemented', ErrorCodes.NOT_IMPLEMENTED);
  }

  getExperimentalFeatures(): ReadonlyMap<string, ExperimentalFeatureState> {
    return new Map();
  }

  async getConfigDiagnostics(): Promise<ConfigDiagnostics> {
    return { issues: [] };
  }

  async close(): Promise<void> {
    if (this.closed) return;
    this.closed = true;
    await this.options.onClose();
  }

  isClosed(): boolean {
    return this.closed;
  }
}

/**
 * Adapter to make tau's AgentSession compatible with kimi-code's Session interface
 */
export class TauSessionAdapter {
  private session: AgentSession;
  private result: CreateAgentSessionResult;

  constructor(session: AgentSession, result: CreateAgentSessionResult) {
    this.session = session;
    this.result = result;
  }

  get id(): string {
    return this.session.id;
  }

  get status(): string {
    return this.session.status;
  }

  async prompt(message: string, options?: { signal?: AbortSignal }): Promise<void> {
    await this.session.prompt(message, options);
  }

  async close(): Promise<void> {
    await this.session.dispose();
  }

  get model(): Model | undefined {
    return this.session.model;
  }

  get cwd(): string {
    return this.session.cwd;
  }

  get agentDir(): string {
    return this.session.agentDir;
  }

  get transcript(): any[] {
    return this.session.transcript;
  }

  get tools(): any[] {
    return this.session.tools;
  }

  get skills(): any[] {
    return this.session.skills;
  }

  get eventBus(): EventBus {
    return this.session.eventBus;
  }

  async sendInput(input: string): Promise<void> {
    await this.session.prompt(input);
  }

  async waitForIdle(): Promise<void> {
    await this.session.waitForIdle();
  }

  abort(signal?: AbortSignal): void {
    this.session.abort(signal?.reason);
  }

  dispose(): Promise<void> {
    return this.session.dispose();
  }
}

/**
 * Factory function to create TauHarness (mirrors createKimiHarness)
 */
export async function createTauHarness(options: TauHarnessRuntimeOptions): Promise<TauHarness> {
  const harness = new TauHarness(options);
  await harness.initialize();
  return harness;
}

export type { CreateSessionOptions, KimiConfig, KimiConfigPatch, SessionSummary, TelemetryClient, TelemetryProperties, KimiHostIdentity };