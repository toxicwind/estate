#!/usr/bin/env node
// acp-tcp-bridge — TCP → stdio bridge for ACP (Agent Client Protocol) servers.
//
// P4 headless-TUI policy (2026-09-20): a supervised stdio-ACP server whose
// stdio nobody holds is a liveness lie — pitchfork sees a process but cannot
// observe it, and readiness is faked with pgrep. This bridge makes stdio-only
// ACP servers (e.g. tau's `dist/omp acp`, which has NO --acp-port TCP flag)
// real observable daemons: it listens on TCP <port>, and per TCP connection
// spawns the ACP server with piped stdio, relaying bytes bidirectionally
// until either side closes. ACP is newline-delimited JSON-RPC on a byte
// stream, so a byte-level pipe is a faithful transport; TCP gives us a real
// readiness probe (connect) and real supervision.
//
// Usage: acp-tcp-bridge <port> <cmd> [args...]
//   e.g. acp-tcp-bridge 25111 /home/toxic/sovereign/projects/tau/engine/packages/coding-agent/dist/omp acp
//
// Exit codes: 2 = bad args, 1 = listen failure (EADDRINUSE etc).
// stderr goes to the pitchfork log: one line per listen/connection/teardown.

import net from 'node:net';
import { spawn } from 'node:child_process';

const [portArg, ...cmd] = process.argv.slice(2);
const port = Number(portArg);
if (!Number.isInteger(port) || port <= 0 || port > 65535 || cmd.length === 0) {
  console.error('usage: acp-tcp-bridge <port> <cmd> [args...]');
  process.exit(2);
}

let seq = 0;

const server = net.createServer((sock) => {
  const id = ++seq;
  let child;
  try {
    child = spawn(cmd[0], cmd.slice(1), {
      stdio: ['pipe', 'pipe', 'inherit'], // stderr → pitchfork log
      env: process.env,
      windowsHide: true,
    });
  } catch (e) {
    console.error(`[acp-tcp-bridge] conn #${id}: spawn failed: ${e.message}`);
    sock.destroy();
    return;
  }
  console.error(`[acp-tcp-bridge] conn #${id} open -> pid ${child.pid} (${cmd.join(' ')})`);

  let done = false;
  const teardown = (why) => {
    if (done) return;
    done = true;
    console.error(`[acp-tcp-bridge] conn #${id} closed (${why})`);
    if (!sock.destroyed) sock.destroy();
    if (child.exitCode === null && child.signalCode === null) {
      child.kill('SIGTERM');
      const t = setTimeout(() => {
        try { child.kill('SIGKILL'); } catch { /* already gone */ }
      }, 2000);
      if (typeof t.unref === 'function') t.unref();
    }
  };

  sock.on('error', (e) => teardown(`socket error: ${e.message}`));
  sock.on('close', () => teardown('socket closed'));
  child.on('error', (e) => teardown(`spawn error: ${e.message}`));
  child.on('exit', (code, sig) => teardown(`child exit code=${code} signal=${sig}`));
  child.stdin.on('error', () => {});   // teardown() already runs on close
  child.stdout.on('error', () => {});

  sock.pipe(child.stdin);    // TCP -> server stdin (client EOF ends stdin)
  child.stdout.pipe(sock);   // server stdout -> TCP (server exit ends socket)
});

server.on('error', (e) => {
  console.error(`[acp-tcp-bridge] listen 127.0.0.1:${port} failed: ${e.message}`);
  process.exit(1);
});

server.listen(port, '127.0.0.1', () => {
  console.error(`[acp-tcp-bridge] listening 127.0.0.1:${port} -> ${cmd.join(' ')}`);
});
