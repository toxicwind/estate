import { RigClient } from "../../lib/rig_api";

const RIG_URL = process.env.RIG_URL || "http://127.0.0.1:25103";
const client = new RigClient(RIG_URL, process.env.RIG_API_KEY);

export async function handleMessage(
  message: string,
  agent = "coyote",
): Promise<string> {
  try {
    return await client.chat(agent, message);
  } catch (err) {
    console.error(`[Rig Plugin] Error: ${err}`);
    return `[Rig Error: ${err}]`;
  }
}

if (import.meta.main) {
  console.log(`[Rig Plugin] Initialized. URL: ${RIG_URL}`);
}
