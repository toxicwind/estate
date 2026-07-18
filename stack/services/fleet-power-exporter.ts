// fleet-power-exporter.ts — polls Fleet-Bench :25203/api/power and exposes
// Prometheus text metrics at :25208/metrics for Grafana (T13).
function need(n: string) {
  const v = process.env[n];
  if (!v) throw new Error(n + " required");
  return v;
}
const POWER_URL = process.env.FLEET_POWER_URL || `http://127.0.0.1:${need("FLEET_BENCH_PORT")}/api/power`;
const PORT = Number(need("FLEET_POWER_PORT"));
const INTERVAL = Number(Bun.env.FLEET_POWER_INTERVAL ?? 5000);

type Power = {
  temperature: number;
  powerDraw: number;
  fanSpeed: number;
  memoryUsed: number;
  memoryTotal: number;
  gpuUtil: number;
};

let latest: Power | null = null;

async function poll(): Promise<void> {
  try {
    const r = await fetch(POWER_URL);
    if (r.ok) latest = (await r.json()) as Power;
  } catch {
    // keep last good sample
  }
}

await poll();
setInterval(poll, INTERVAL);

function render(m: Power): string {
  return [
    "# HELP fleet_gpu_temperature_celsius GPU core temperature",
    "# TYPE fleet_gpu_temperature_celsius gauge",
    `fleet_gpu_temperature_celsius ${m.temperature}`,
    "# HELP fleet_gpu_power_draw_watts GPU board power draw",
    "# TYPE fleet_gpu_power_draw_watts gauge",
    `fleet_gpu_power_draw_watts ${m.powerDraw}`,
    "# HELP fleet_gpu_fan_speed_percent GPU fan speed",
    "# TYPE fleet_gpu_fan_speed_percent gauge",
    `fleet_gpu_fan_speed_percent ${m.fanSpeed}`,
    "# HELP fleet_gpu_memory_used_mb GPU memory used",
    "# TYPE fleet_gpu_memory_used_mb gauge",
    `fleet_gpu_memory_used_mb ${m.memoryUsed}`,
    "# HELP fleet_gpu_memory_total_mb GPU memory total",
    "# TYPE fleet_gpu_memory_total_mb gauge",
    `fleet_gpu_memory_total_mb ${m.memoryTotal}`,
    "# HELP fleet_gpu_utilization_percent GPU utilization",
    "# TYPE fleet_gpu_utilization_percent gauge",
    `fleet_gpu_utilization_percent ${m.gpuUtil}`,
  ].join("\n") + "\n";
}

Bun.serve({
  port: PORT,
  fetch(req) {
    const path = new URL(req.url).pathname;
    if (path === "/metrics") {
      if (!latest) {
        return new Response("# no sample yet\n", {
          headers: { "content-type": "text/plain; version=0.0.4" },
        });
      }
      return new Response(render(latest), {
        headers: { "content-type": "text/plain; version=0.0.4" },
      });
    }
    return new Response("fleet-power-exporter ok\n");
  },
});

console.log(`[fleet-power-exporter] :${PORT} -> ${POWER_URL}`);
