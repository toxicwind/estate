import * as net from "node:net";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";

/**
 * Direct Socket Task Runner & Egress configuration for Ranch.
 * Establishes OS-level TCP keepalives to prevent middleboxes from dropping
 * long-running reasoning SSE streams.
 */
export interface SocketStreamConfig {
  socketPath?: string;
  tcpPort?: number;
  tcpHost?: string;
  tcpKeepAlive?: boolean;
  tcpKeepAliveInitialDelayMs?: number;
  tcpNoDelay?: boolean;
  maxRingBufferTokens?: number;
}

export const DEFAULT_SOCKET_PATH = fs.existsSync("/run/user/1000")
  ? "/run/user/1000/sovereign-stream-broker.sock"
  : path.join(os.tmpdir(), "sovereign-stream-broker.sock");

export const DEFAULT_SOCKET_STREAM_CONFIG: SocketStreamConfig = {
  socketPath: DEFAULT_SOCKET_PATH,
  tcpPort: 25145,
  tcpHost: "127.0.0.1",
  tcpKeepAlive: true,
  tcpKeepAliveInitialDelayMs: 30000, // TCP_KEEPIDLE 30s
  tcpNoDelay: true,
  maxRingBufferTokens: 32768,
};

/**
 * Append-only ring buffer for preserving validated reasoning tokens
 * across mid-flight network interrupts or middlebox resets.
 */
export class RingTokenBuffer {
  private buffer: string[];
  private maxSize: number;
  private pointer: number = 0;
  private totalAppended: number = 0;

  constructor(maxSize: number = 32768) {
    this.maxSize = maxSize;
    this.buffer = new Array(maxSize);
  }

  public push(token: string): void {
    this.buffer[this.pointer] = token;
    this.pointer = (this.pointer + 1) % this.maxSize;
    this.totalAppended++;
  }

  public getAll(): string[] {
    if (this.totalAppended < this.maxSize) {
      return this.buffer.slice(0, this.totalAppended);
    }
    return [
      ...this.buffer.slice(this.pointer),
      ...this.buffer.slice(0, this.pointer),
    ];
  }

  public getText(): string {
    return this.getAll().join("");
  }

  public clear(): void {
    this.buffer = new Array(this.maxSize);
    this.pointer = 0;
    this.totalAppended = 0;
  }

  public get length(): number {
    return Math.min(this.totalAppended, this.maxSize);
  }
}

/**
 * Direct Socket Stream Client connects to the Stream Broker UNIX socket
 * or TCP port with robust keepalive parameters.
 */
export class DirectSocketStreamClient {
  private config: SocketStreamConfig;
  private socket: net.Socket | null = null;
  private ringBuffer: RingTokenBuffer;

  constructor(config: Partial<SocketStreamConfig> = {}) {
    this.config = { ...DEFAULT_SOCKET_STREAM_CONFIG, ...config };
    this.ringBuffer = new RingTokenBuffer(this.config.maxRingBufferTokens);
  }

  public async connect(): Promise<net.Socket> {
    const { promise, resolve, reject } = Promise.withResolvers<net.Socket>();
    const socket = new net.Socket();

    const connectTarget = this.config.socketPath && fs.existsSync(path.dirname(this.config.socketPath))
      ? { path: this.config.socketPath }
      : { port: this.config.tcpPort ?? 25145, host: this.config.tcpHost ?? "127.0.0.1" };

    socket.connect(connectTarget, () => {
      socket.setKeepAlive(this.config.tcpKeepAlive ?? true, this.config.tcpKeepAliveInitialDelayMs ?? 30000);
      socket.setNoDelay(this.config.tcpNoDelay ?? true);
      this.socket = socket;
      resolve(socket);
    });

    socket.on("error", (err) => {
      reject(err);
    });

    return promise;
  }

  public getRingBuffer(): RingTokenBuffer {
    return this.ringBuffer;
  }

  public buildAssistantContinuation(originalPrompt: string): string {
    const salvaged = this.ringBuffer.getText();
    if (!salvaged) return originalPrompt;
    return `${originalPrompt}\n[ASSISTANT CONTINUATION PREFIX]: ${salvaged}`;
  }

  public close(): void {
    if (this.socket) {
      this.socket.destroy();
      this.socket = null;
    }
  }
}
