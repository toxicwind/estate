#!/usr/bin/env bun
// tools/pollinations-proxy/tester.ts — maximal tester for Pollinations free via herd
const POLL = process.env.POLL_BASE ?? "https://gen.pollinations.ai/v1";
const HERD = (process.env.HERD_BASE ?? "http://127.0.0.1:25100/v1").replace(/\/$/, "");
const herdFromArg = Bun.argv.find(a => a.startsWith("--herd="))?.split("=")[1];
const HERD_BASE = herdFromArg ? herdFromArg.replace(/\/$/, "") : HERD;
type Probe = { name: string; ok: boolean; detail: string; http?: number };
const results: Probe[] = [];
async function probe(name: string, fn: () => Promise<{ http: number; body: any }>, expect: (j:any, http:number)=>{ok:boolean, detail:string}) {
  try {
    const { http, body } = await fn();
    const { ok, detail } = expect(body, http);
    results.push({ name, ok, detail: `[HTTP ${http}] ${detail}`, http });
    console.log(`${ok ? "✅" : "❌"} ${name}: HTTP ${http} — ${detail}`);
    return ok;
  } catch (e:any) {
    results.push({ name, ok: false, detail: `EXC ${e.message.slice(0,300)}` });
    console.log(`❌ ${name}: EXC ${e.message.slice(0,300)}`);
    return false;
  }
}
async function fetchJSON(url:string, init:RequestInit) {
  const r = await fetch(url, init);
  const text = await r.text();
  let body:any; try { body = JSON.parse(text); } catch { body = { _raw: text.slice(0,1200) }; }
  return { http: r.status, body, headers: r.headers };
}
await probe("T1 direct Pollinations openai (no auth) — expect 200", async () => {
  return await fetchJSON(`${POLL}/chat/completions`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: "openai", messages: [{ role:"user", content:"hi in 5 words" }], max_tokens: 20 }),
  });
}, (j, http) => {
  const c = j.choices?.[0]?.message?.content;
  if (http===200 && c) return { ok:true, detail:`OK "${c.slice(0,80).replace(/\n/g,' ')}" model=${j.model??"?"}` };
  return { ok:false, detail: `want 200+content got ${JSON.stringify(j).slice(0,400)}` };
});
await probe("T2 direct Pollinations openai/gpt-oss-20b — expect 401", async () => {
  return await fetchJSON(`${POLL}/chat/completions`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: "openai/gpt-oss-20b", messages: [{ role:"user", content:"hi" }], max_tokens: 10 }),
  });
}, (j, http) => {
  if (http===401) return { ok:true, detail:`correctly 401: ${j.error?.message?.slice(0,120)??JSON.stringify(j).slice(0,200)}` };
  return { ok:false, detail:`want 401 got ${http} ${JSON.stringify(j).slice(0,400)}` };
});
await probe("T3 direct Pollinations streaming", async () => {
  const r = await fetch(`${POLL}/chat/completions`, {
    method: "POST", headers: { "Content-Type":"application/json" },
    body: JSON.stringify({ model:"openai", messages:[{role:"user",content:"hi"}], max_tokens:20, stream:true }),
  });
  const text = await r.text();
  return { http: r.status, body: { _raw: text.slice(0,800) } };
}, (j, http) => {
  if (http===200 && (j as any)._raw?.includes("data:")) return { ok:true, detail:`SSE ok` };
  return { ok:false, detail:`want 200 SSE got ${JSON.stringify(j).slice(0,400)}` };
});
const herdProbes = async () => {
  await probe("T9 herd /v1/models includes openai peer", async () => {
    const a = await fetchJSON(`${HERD_BASE}/models`, { headers:{} });
    if (a.http===404) return await fetchJSON(`${HERD_BASE.replace(/\/v1$/,"")}/v1/models`, { headers:{} });
    return a;
  }, (j, http) => {
    const ids = (j.data||[]).map((m:any)=>m.id) as string[];
    if (http===200 && ids.includes("openai")) return { ok:true, detail:`found openai in ${ids.length} models` };
    if (http===200) return { ok:false, detail:`200 but openai missing — ids: ${ids.slice(0,15).join(",")}` };
    return { ok:false, detail:`want 200 with openai got ${http} ${JSON.stringify(j).slice(0,500)}` };
  });
  await probe("T4 herd openai no-auth — expect 200 after hotfix", async () => {
    return await fetchJSON(`${HERD_BASE}/chat/completions`, {
      method:"POST", headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ model:"openai", messages:[{role:"user",content:"hi in 5 words"}], max_tokens:20 }),
    });
  }, (j,http)=>{
    const c=j.choices?.[0]?.message?.content;
    if (http===200 && c) return { ok:true, detail:`OK "${c.slice(0,80).replace(/\n/g,' ')}"` };
    return { ok:false, detail:`want 200 got ${http} ${JSON.stringify(j).slice(0,600)}` };
  });
  await probe("T5 herd openai WITH dummy Bearer (auth-strip P1) — expect 200 after patch", async () => {
    return await fetchJSON(`${HERD_BASE}/chat/completions`, {
      method:"POST", headers:{ "Content-Type":"application/json", "Authorization":"Bearer dummy-should-be-stripped" },
      body: JSON.stringify({ model:"openai", messages:[{role:"user",content:"hi in 5 words"}], max_tokens:20 }),
    });
  }, (j,http)=>{
    const c=j.choices?.[0]?.message?.content;
    if (http===200 && c) return { ok:true, detail:`OK strip works "${c.slice(0,80).replace(/\n/g,' ')}"` };
    if (http===401) return { ok:false, detail:`401 — auth not stripped (patch missing) ${JSON.stringify(j).slice(0,400)}` };
    return { ok:false, detail:`want 200 got ${http} ${JSON.stringify(j).slice(0,600)}` };
  });
  await probe("T6 herd openai streaming", async () => {
    const r = await fetch(`${HERD_BASE}/chat/completions`, {
      method:"POST", headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ model:"openai", messages:[{role:"user",content:"hi"}], max_tokens:20, stream:true }),
    });
    const text = await r.text();
    return { http: r.status, body:{ _raw:text.slice(0,800) } };
  }, (j,http)=>{
    if (http===200 && (j as any)._raw?.includes("data:")) return { ok:true, detail:`SSE ok` };
    return { ok:false, detail:`want 200 SSE got ${http} ${JSON.stringify(j).slice(0,400)}` };
  });
  await probe("T7 herd unknown model — expect 4xx", async () => {
    return await fetchJSON(`${HERD_BASE}/chat/completions`, {
      method:"POST", headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ model:"nope-xyz-999", messages:[{role:"user",content:"hi"}], max_tokens:5 }),
    });
  }, (j,http)=>{
    if (http>=400 && http<500) return { ok:true, detail:`correctly ${http} ${JSON.stringify(j).slice(0,300)}` };
    return { ok:false, detail:`want 4xx got ${http} ${JSON.stringify(j).slice(0,400)}` };
  });
  console.log("\n--- T8 rate-limit probe (3 rapid openai) ---");
  for (let i=1;i<=3;i++) {
    await probe(`T8.${i} rapid openai #${i}`, async () => {
      return await fetchJSON(`${HERD_BASE}/chat/completions`, {
        method:"POST", headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ model:"openai", messages:[{role:"user",content:`hi #${i}`}], max_tokens:5 }),
      });
    }, (j,http)=>{
      const c=j.choices?.[0]?.message?.content;
      if (http===200 && c) return { ok:true, detail:`OK` };
      if (http===429) return { ok:true, detail:`429 rate-limited (expected after burst)` };
      return { ok:false, detail:`got ${http} ${JSON.stringify(j).slice(0,400)}` };
    });
  }
};
await herdProbes();
const CF_ACCT = process.env.CLOUDFLARE_ACCOUNT_ID ?? "2d5e60dbc717af626a1eb04177aa2225";
const CF_GW = process.env.CLOUDFLARE_GATEWAY_ID ?? "default";
const CF_TOKEN = process.env.CLOUDFLARE_API_TOKEN ?? process.env.CF_API_TOKEN ?? "";
if (CF_TOKEN) {
  await probe("T10 CF gateway custom-pollinations-free (if provisioned)", async () => {
    return await fetchJSON(`https://gateway.ai.cloudflare.com/v1/${CF_ACCT}/${CF_GW}/custom-pollinations-free/v1/chat/completions`, {
      method:"POST", headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ model:"openai", messages:[{role:"user",content:"hi"}], max_tokens:10 }),
    });
  }, (j,http)=>{
    if (http===200) return { ok:true, detail:`CF gateway works` };
    return { ok:false, detail:`CF gateway not yet provisioned — got ${http} ${JSON.stringify(j).slice(0,500)} (skip)` };
  });
} else {
  console.log("⏭️  T10 skipped — no CLOUDFLARE_API_TOKEN");
}
console.log("\n=== SUMMARY ===");
for (const r of results) console.log(`${r.ok?"✅":"❌"} ${r.name} — ${r.detail}`);
const failCount = results.filter(r=>!r.ok && !r.name.includes("T10") && !r.name.includes("T2") && !r.name.includes("T8") ).length;
console.log(`\nfailCount (mandatory) = ${failCount}`);
if (failCount>0) { console.log(`\n❌ ${failCount} mandatory probe(s) failed`); process.exit(1); }
else { console.log(`\n✅ Tester passed`); await Bun.write(`tools/pollinations-proxy/.out/tester-results.json`, JSON.stringify(results, null, 2)); console.log(`Wrote tools/pollinations-proxy/.out/tester-results.json`); }
