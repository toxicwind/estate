// @sovereign/template — service skeleton.
// Copy to services/<name>/, set package.json sovereign.port/portEnv/daemon,
// add <NAME>_PORT to config/ports.env, wire pitchfork.toml, then implement.
//
// Conventions (non-negotiable):
// - Port comes from process.env[<PORT_ENV>] — never hardcoded. Fail fast if unset.
// - Bind 127.0.0.1 only. Public exposure goes through mesh-front, never the service.
// - /health returns 200 + JSON. pitchfork/health checks depend on it.
// - Event-driven: no setInterval polling loops. Wake on requests, inotify, WS.
// - Graceful shutdown on SIGTERM/SIGINT (pitchfork restarts must be clean).

const PORT_ENV = "TEMPLATE_PORT";
const SERVICE = "template";

function requiredPort(): number {
  const raw = process.env[PORT_ENV];
  if (!raw) {
    console.error(`FATAL ${SERVICE}: ${PORT_ENV} is not set (ports come from config/ports.env, never hardcoded)`);
    process.exit(1);
  }
  const port = Number(raw);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    console.error(`FATAL ${SERVICE}: ${PORT_ENV}=${raw} is not a valid port`);
    process.exit(1);
  }
  return port;
}

const port = requiredPort();

const server = Bun.serve({
  port,
  hostname: "127.0.0.1",
  fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/health") {
      return Response.json({ ok: true, service: SERVICE, port });
    }
    return new Response("not found", { status: 404 });
  },
});

console.log(`${SERVICE} listening on 127.0.0.1:${port} (pid ${process.pid})`);

function shutdown(signal: string) {
  console.log(`${SERVICE}: ${signal}, draining`);
  server.stop(true);
  process.exit(0);
}
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
