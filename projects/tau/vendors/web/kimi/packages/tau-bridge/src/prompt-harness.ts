/**
 * PromptHarness adapter — implements kimi-code's PromptHarness interface using tau engine
 * This enables `kimi -p` (print mode) to use tau's AgentSession
 */

import {
  ErrorCodes,
  KimiError,
  type TelemetryProperties,
} from '@moonshot-ai/agent-core';
import type {
  KimiAuthFacade,
  CreateSessionOptions,
  SessionStatus,
  SessionSummary,
  ListSessionsOptions,
  ConfigDiagnostics,
  GetConfigOptions,
  PromptInput,
  ApprovalHandler,
  QuestionHandler,
  Unsubscribe,
  KimiConfig,
  KimiHostIdentity,
  Event,
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

export interface PromptHarnessRuntimeOptions {
  readonly identity?: KimiHostIdentity;
  readonly uiMode?: string;
  readonly homeDir: string;
  readonly configPath: string;
  readonly auth: KimiAuthFacade;
  readonly telemetry: {
    track(event: string, properties?: TelemetryProperties): void;
    withContext: any;
    setContext: any;
  };
  readonly ensureConfigFile: () => Promise<void>;
  readonly onClose: () => void | Promise<void>;
  readonly sessionStartedProperties?: TelemetryProperties;
  readonly skillDirs?: string[];
}

export class TauPromptHarness {
  private readonly options: PromptHarnessRuntimeOptions;
  private settings: Settings | null = null;
  private modelRegistry: ModelRegistry | null = null;
  private eventBus: EventBus;
  private closed = false;

  constructor(options: PromptHarnessRuntimeOptions) {
    this.options = options;
    this.eventBus = new EventBus();
  }

  get homeDir(): string {
    return this.options.homeDir;
  }

  get auth(): KimiAuthFacade {
    return this.options.auth;
  }

  track(event: string, properties?: TelemetryProperties): void {
    this.options.telemetry.track(event, properties);
  }

  async ensureConfigFile(): Promise<void> {
    await this.initialize();
  }

  async getConfig(): Promise<Pick<KimiConfig, 'defaultModel' | 'telemetry'>> {
    await this.initialize();
    const defaultModel = this.settings?.get('model') ?? 'anthropic/claude-opus-4-5';
    return { defaultModel, telemetry: undefined };
  }

  async getConfigDiagnostics(): Promise<ConfigDiagnostics> {
    await this.initialize();
    return { issues: [] };
  }

  async listSessions(_options: ListSessionsOptions): Promise<readonly SessionSummary[]> {
    await this.initialize();
    return [];
  }

  async createSession(options: CreateSessionOptions): Promise<TauPromptSessionAdapter> {
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
    return new TauPromptSessionAdapter(result.session, result);
  }

  async resumeSession(_input: any): Promise<TauPromptSessionAdapter> {
    return this.createSession({});
  }

  async close(): Promise<void> {
    if (this.closed) return;
    this.closed = true;
    await this.options.onClose();
  }

  private async initialize(): Promise<void> {
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
}

/**
 * Adapter to make tau's AgentSession compatible with kimi-code's PromptSession interface
 */
export class TauPromptSessionAdapter {
  private session: AgentSession;
  private result: CreateAgentSessionResult;
  private status: SessionStatus = 'idle';
  private approvalHandler: ApprovalHandler | undefined;
  private questionHandler: QuestionHandler | undefined;
  private eventListeners: Set<(event: Event) => void> = new Set();

  constructor(session: AgentSession, result: CreateAgentSessionResult) {
    this.session = session;
    this.result = result;
  }

  get id(): string {
    return this.session.id;
  }

  get workDir(): string {
    return this.session.cwd;
  }

  async getStatus(): Promise<SessionStatus> {
    return this.status;
  }

  async setModel(model: string): Promise<void> {
    const [provider, ...modelParts] = model.split('/');
    this.session.model = getBundledModel(provider as any, modelParts.join('/'));
  }

  async setPermission(_mode: 'yolo' | 'manual' | 'auto'): Promise<void> {
  }

  setApprovalHandler(handler: ApprovalHandler | undefined): void {
    this.approvalHandler = handler;
  }

  setQuestionHandler(handler: QuestionHandler | undefined): void {
    this.questionHandler = handler;
  }

  onEvent(listener: (event: Event) => void): Unsubscribe {
    this.eventListeners.add(listener);
    return () => this.eventListeners.delete(listener);
  }

  private emitEvent(event: Event): void {
    for (const listener of this.eventListeners) {
      try {
        listener(event);
      } catch (e) {
        logger.error('Event listener error', { error: e });
      }
    }
  }

  async prompt(input: string | PromptInput): Promise<void> {
    const message = typeof input === 'string' ? input : input.map(p => p.type === 'text' ? p.text : '').join('');
    this.status = 'streaming';
    this.emitEvent({ type: 'turn.started', turnId: Date.now() } as Event);
    
    try {
      await this.session.prompt(message);
      this.status = 'idle';
      this.emitEvent({ type: 'turn.ended', turnId: Date.now() } as Event);
    } catch (e) {
      this.status = 'error';
      this.emitEvent({ type: 'turn.ended', turnId: Date.now(), error: String(e) } as Event);
      throw e;
    }
  }

  async waitForBackgroundTasksOnPrint(): Promise<void> {
    await this.session.waitForIdle();
  }

  async handlePrintMainTurnCompleted(): Promise<'finish' | 'continue'> {
    return 'finish';
  }

  async createGoal(_input: any): Promise<any> {
    throw new KimiError('Not implemented', ErrorCodes.NOT_IMPLEMENTED);
  }

  async getGoal(): Promise<any> {
    throw new KimiError('Not implemented', ErrorCodes.NOT_IMPLEMENTED);
  }

  async getCronTasks(): Promise<any> {
    return { tasks: [] };
  }

  async close(): Promise<void> {
    await this.session.dispose();
  }
}

/**
 * Factory function to create TauPromptHarness
 */
export async function createTauPromptHarness(options: PromptHarnessRuntimeOptions): Promise<TauPromptHarness> {
  const harness = new TauPromptHarness(options);
  await harness.initialize();
  return harness;
}