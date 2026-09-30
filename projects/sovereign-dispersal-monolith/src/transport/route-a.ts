// Route A fastest-wins cancel-rest
// gator 8.45.176.206 LIVE 80/443/53 / dev 76.223.54.146 LIVE / cdn,sandbox FAIL / 8.8.8.8 proof LIVE
export type Endpoint = { name: string; host: string; ip: string; ports: number[]; expect: "LIVE" | "FAIL" };
export const ROUTE_A_ENDPOINTS: Endpoint[] = [
  { name: "gator.volces.com", host: "gator.volces.com", ip: "8.45.176.206", ports: [80, 443, 53], expect: "LIVE" },
  { name: "cdn FAIL",          host: "cdn.volces.com",   ip: "",             ports: [80, 443],     expect: "FAIL" },
  { name: "development.team",  host: "development.team", ip: "76.223.54.146",ports: [80, 443, 53], expect: "LIVE" },
  { name: "sandbox.team FAIL", host: "sandbox.team",     ip: "",             ports: [80, 443],     expect: "FAIL" },
  { name: "8.8.8.8 proof",     host: "8.8.8.8",          ip: "8.8.8.8",      ports: [80, 53],      expect: "LIVE" },
];
export type Win = { endpoint: string; ip: string; port: number; ms: number };

export async function fastestWinsCancelRest(endpoints = ROUTE_A_ENDPOINTS, timeoutMs = 3000): Promise<Win> {
  const timeoutCtrl = new AbortController();
  const timeout = setTimeout(() => timeoutCtrl.abort(), timeoutMs);
  const ctrls: AbortController[] = [];
  const tasks = endpoints.flatMap(ep => ep.ports.map(port => {
    const ctrl = new AbortController();
    ctrls.push(ctrl);
    const combined = typeof (AbortSignal as any).any === "function"
      ? (AbortSignal as any).any([ctrl.signal, timeoutCtrl.signal])
      : ctrl.signal;
    return probe(ep, port, combined);
  }));
  try {
    const win = await Promise.any(tasks as any);
    for (const c of ctrls) c.abort();
    return win;
  } finally {
    clearTimeout(timeout);
    timeoutCtrl.abort();
  }
}

async function probe(ep: Endpoint, port: number, signal: AbortSignal): Promise<Win> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) return reject(new Error("aborted"));
    let settled = false;
    const onAbort = () => { if (settled) return; settled = true; reject(new Error("aborted")); };
    signal.addEventListener("abort", onAbort);
    const t = Date.now();
    const target = ep.ip || ep.host;
    Bun.connect({
      hostname: target, port,
      socket: {
        open(socket) {
          if (settled) return; settled = true;
          signal.removeEventListener("abort", onAbort);
          resolve({ endpoint: ep.name, ip: target, port, ms: Date.now() - t });
          socket.end();
        },
        error() {
          if (settled) return; settled = true;
          signal.removeEventListener("abort", onAbort);
          reject(new Error("fail " + ep.name + ":" + port));
        },
        data() {},
      } as any,
    }).catch(() => {
      if (settled) return; settled = true;
      signal.removeEventListener("abort", onAbort);
      reject(new Error("fail " + ep.name + ":" + port));
    });
  });
}

export const DNS_FIX_CONTENT = "nameserver 8.8.8.8\nnameserver 1.1.1.1\nnameserver 8.8.4.4\n";

export async function verifyLive() {
  const live: Win[] = [];
  const failed: string[] = [];
  let dnsPoisoned = false;
  try {
    const r = await Bun.file("/etc/resolv.conf").text();
    dnsPoisoned = r.includes("fd00::1") && r.includes("192.168.0.1");
  } catch {}
  for (const ep of ROUTE_A_ENDPOINTS) {
    for (const port of ep.ports) {
      try {
        const w = await probe(ep, port, new AbortController().signal);
        if (ep.expect === "LIVE") live.push(w);
      } catch {
        if (ep.expect === "FAIL") failed.push(ep.name + ":" + port);
      }
    }
  }
  return { live, failed, dnsPoisoned };
}

if (import.meta.main) {
  console.log(await verifyLive());
  console.log("fastest:", await fastestWinsCancelRest());
}

