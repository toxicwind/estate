#!/usr/bin/env bun
// fix-nvidia-inkling.ts — patches settings.json per AGENTS §5 hardpoint.
// Removes custom_headers.Authorization (stripped by Zed) and sets api_key
// via the <PROVIDER_ID>_API_KEY env convention.
import { readFileSync, writeFileSync } from "node:fs";
import json5 from "json5";

const P = "/home/toxic/.config/zed/settings.json";
const j = json5.parse(readFileSync(P, "utf8"));
const p = j.language_models?.openai_compatible?.["nvidia-inkling"];
if (!p) { console.error("nvidia-inkling provider not found"); process.exit(1); }

delete p.custom_headers;
p.api_key = "${NVIDIA_INKLING_API_KEY}";

writeFileSync(P, JSON.stringify(j, null, 2) + "\n");
console.log("patched: custom_headers removed, api_key=${NVIDIA_INKLING_API_KEY}");
