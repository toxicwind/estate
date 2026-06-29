#!/usr/bin/env bun
/**
 * yote — sovereign Bun app / ghost_unlocked entrypoint
 * Drop your real ghost_unlocked source here or symlink the directory.
 */
import { serve } from "bun";

const PORT = parseInt(Bun.env.YOTE_PORT ?? "25042");

serve({
  port: PORT,
  fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/health")
      return Response.json({ status: "ok", port: PORT, app: "yote-stub" });
    return new Response("yote stub — replace with ghost_unlocked source", { status: 200 });
  },
});
console.log(`[yote] :${PORT}`);
