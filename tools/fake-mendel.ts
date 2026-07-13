const port = 25099;
const target = "https://daily-cloudcode-pa.sandbox.googleapis.com";
Bun.serve({
  port, hostname: "127.0.0.1",
  async fetch(req) {
    const url = new URL(req.url);
    const real = target + url.pathname + url.search;
    let res = await fetch(real, { method: req.method, headers: req.headers, body: req.method==="GET"?undefined:req.body }).catch(()=>null);
    let body = res ? await res.text() : "{}";
    if (url.pathname.includes("fetchAvailableModels") || url.pathname.includes("loadCodeAssist")) {
        try {
            let j = JSON.parse(body);
            if (Array.isArray(j.models)) {
                j.models.push({ name: "MODEL_PLACEHOLDER_M20", displayName: "M20 Local", id: "MODEL_PLACEHOLDER_M20" });
                j.models.push({ name: "MODEL_PLACEHOLDER_M16", displayName: "M16 Local", id: "MODEL_PLACEHOLDER_M16" });
            }
            if (Array.isArray(j.availableModels)) {
                j.availableModels.push("MODEL_PLACEHOLDER_M20", "MODEL_PLACEHOLDER_M16");
            }
            body = JSON.stringify(j);
        } catch {}
    }
    return new Response(body, { status: res?.status || 200, headers: { "content-type":"application/json" } });
  }
});
