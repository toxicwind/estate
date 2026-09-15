import { $ } from "bun";
import { SERVER, PORT } from "./fleet_config.ts";
import type { ArchConfig, FullMetrics } from "./fleet_types.ts";

export async function killPort() {
  await $`pkill -9 -f llama-server`.quiet().catch(() => {});
  await $`fuser -k ${PORT}/tcp`.quiet().catch(() => {});
  await Bun.sleep(1200);
}

export function buildServerCmd(
  modelPath: string,
  ctx: number,
  archConfig: ArchConfig,
  probeMetrics?: FullMetrics,
): string[] {
  const cmd = [
    SERVER,
    "-m",
    modelPath,
    "-c",
    String(ctx),
    "-ngl",
    "99",
    "--host",
    "127.0.0.1",
    "--port",
    String(PORT),
    "--no-warmup",
    "--jinja",
  ];

  if (archConfig.flashAttnRecommended) {
    cmd.push("-fa", "1");
  }
  if (archConfig.mlaDefault > 0) {
    cmd.push("-mla", String(archConfig.mlaDefault));
  }
  if (archConfig.cacheTypeK !== "f16") {
    cmd.push("-ctk", archConfig.cacheTypeK);
  }
  if (archConfig.cacheTypeV !== "f16") {
    cmd.push("-ctv", archConfig.cacheTypeV);
  }
  if (archConfig.attnMaxBatch > 0) {
    cmd.push("-amb", String(archConfig.attnMaxBatch));
  }
  if (archConfig.fusedMoe) {
    cmd.push("-fmoe");
  }
  if (archConfig.groupedExpertRouting) {
    cmd.push("-ger");
  }
  if (archConfig.runtimeRepack) {
    cmd.push("-rtr");
  }
  if (archConfig.overrideTensors) {
    for (const ot of archConfig.overrideTensors) {
      cmd.push("-ot", ot);
    }
  }
  for (const ef of archConfig.extraFlags) {
    if (!cmd.includes(ef)) cmd.push(ef);
  }
  if (probeMetrics && !probeMetrics.kvSizeMiB) {
    cmd.push("--cache-ram", "0");
  }

  return cmd;
}
