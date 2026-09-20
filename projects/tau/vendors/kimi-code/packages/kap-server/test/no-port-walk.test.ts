import { describe, expect, it } from 'vitest';
import pino from 'pino';

import { listenWithPortRetry } from '../src/start';

function silentLogger() {
  return pino({ level: 'silent' });
}

function addrInUse(): NodeJS.ErrnoException {
  const err = new Error('listen EADDRINUSE') as NodeJS.ErrnoException;
  err.code = 'EADDRINUSE';
  return err;
}

describe('listenWithPortRetry --no-port-walk (SSOT fail-fast)', () => {
  it('throws immediately on EADDRINUSE when failFast is set — no port+1 walk', async () => {
    const attempts: number[] = [];
    await expect(
      listenWithPortRetry({
        listen: async (_host, port) => {
          attempts.push(port);
          throw addrInUse();
        },
        host: '127.0.0.1',
        port: 5000,
        logger: silentLogger(),
        failFast: true,
      }),
    ).rejects.toThrow(/refusing to bind 127\.0\.0\.1:5000.*no port-walk/);
    // Exactly one attempt: the requested port. Never touches 5001.
    expect(attempts).toEqual([5000]);
  });

  it('preserves the default walk when failFast is unset', async () => {
    const attempts: number[] = [];
    const result = await listenWithPortRetry({
      listen: async (_host, port) => {
        attempts.push(port);
        if (port < 5001) throw addrInUse();
        return `http://127.0.0.1:${String(port)}`;
      },
      host: '127.0.0.1',
      port: 5000,
      logger: silentLogger(),
    });

    expect(result.port).toBe(5001);
    expect(attempts).toEqual([5000, 5001]);
  });

  it('binds the requested port when free, even with failFast', async () => {
    const result = await listenWithPortRetry({
      listen: async (_host, port) => `http://127.0.0.1:${String(port)}`,
      host: '127.0.0.1',
      port: 5000,
      logger: silentLogger(),
      failFast: true,
    });

    expect(result.port).toBe(5000);
  });
});
