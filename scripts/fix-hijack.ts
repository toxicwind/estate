#!/usr/bin/env bun
// fix-hijack.ts — P0 femboy.pp.ua redirect removal via user-level X-Auth-Key auth.
// The cfk_ master key works ONLY as X-Auth-Key + X-Auth-Email (user session level),
// which sees legacy Page Rules (the 1011 blind spot that cfat_ tokens cannot).
import { $ } from "bun";

const MK = process.env.CF_MASTER_KEY ?? (await $`kryptos get CF_API_TOKEN_MASTER`.quiet().text()).split("\n").find(l => l.startsWith("secret: "))?.slice(8).trim();
const EMAIL = process.env.CF_AUTH_EMAIL ?? "toxicwind@gmail.com";
if (!MK) throw new Error("no CF master key");
const API = "https://api.cloudflare.com/client/v4";
const AUTH = { "X-Auth-Email": EMAIL, "X-Auth-Key": MK, "Content-Type": "application/json" };

async function cf<T = any>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${API}${path}`, { ...init, headers: { ...AUTH, ...(init?.headers ?? {}) } });
	const d = await res.json() as any;
	if (!d.success) throw new Error(`${path} -> ${JSON.stringify(d.errors).slice(0, 200)}`);
	return d.result;
}

const zones = await cf<any[]>("/zones?per_page=50");
console.log(`zones: ${zones.length}`);

for (const z of zones) {
	const base = `/zones/${z.id}`;
	// 1. legacy Page Rules (the attacker's 301 lived here)
	try {
		const rules = await cf<any[]>(`${base}/pagerules?status=all`);
		for (const r of rules) {
			const blob = JSON.stringify(r);
			if (/femboy/i.test(blob)) {
				await cf(`${base}/pagerules/${r.id}`, { method: "DELETE" });
				console.log(`${z.name}: DELETED pagerule ${r.id} (${r.targets?.[0]?.constraint?.value})`);
			} else {
				console.log(`${z.name}: pagerule ${r.id} clean (${JSON.stringify(r.actions).slice(0, 80)})`);
			}
		}
		if (!rules.length) console.log(`${z.name}: no pagerules`);
	} catch (e) { console.log(`${z.name}: pagerules ${e.message.slice(0, 120)}`); }

	// 2. rulesets (dynamic redirects)
	try {
		const rsets = await cf<any[]>(`${base}/rulesets`);
		for (const rs of rsets) {
			try {
				const full = await cf<any>(`${base}/rulesets/${rs.id}`);
				const blob = JSON.stringify(full);
				if (/femboy/i.test(blob)) {
					await cf(`${base}/rulesets/${rs.id}`, { method: "DELETE" });
					console.log(`${z.name}: DELETED ruleset ${rs.id} (${rs.phase})`);
				}
			} catch { /* phase rulesets may 403 */ }
		}
	} catch (e) { console.log(`${z.name}: rulesets ${e.message.slice(0, 120)}`); }

	// 3. DNS records pointing at the attacker
	try {
		const recs = await cf<any[]>(`${base}/dns_records?per_page=100`);
		for (const r of recs) {
			if (/femboy|pornhub/i.test(`${r.name} ${r.content}`)) {
				await cf(`${base}/dns_records/${r.id}`, { method: "DELETE" });
				console.log(`${z.name}: DELETED dns ${r.type} ${r.name} -> ${r.content}`);
			}
		}
	} catch (e) { console.log(`${z.name}: dns ${e.message.slice(0, 120)}`); }
}

// 4. edge verification
console.log("\n== edge verify ==");
for (const z of zones) {
	if (z.name === "arlockworks.com") continue;
	const p = Bun.spawnSync(["curl", "-sI", "--max-time", "10", `https://${z.name}`]);
	const out = p.stdout.toString();
	const loc = out.match(/^location:\s*(\S+)/mi)?.[1] ?? "(none)";
	const code = out.match(/^HTTP\/[\d.]+\s+(\d+)/m)?.[1] ?? "???";
	console.log(`${z.name}: ${code} location=${loc} ${/femboy/i.test(loc) ? "STILL HIJACKED" : "OK"}`);
}
