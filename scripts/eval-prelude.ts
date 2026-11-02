// estate eval prelude — %load this file in any future session cell.
// Provides: keyring, embed (bge-m3 lane), cos/norm/sub/add/mean/axisProj.

const keyring = (env = "FREEINFERENCE_API_KEY") =>
  new Response(Bun.spawnSync(["sh","-c",`secretsmith env | grep '^${env}=' | cut -d= -f2- | tr -d "'"`]).stdout).text().then(t => t.trim());

// SECRET-SAFE HELPERS (2026-11-02 leak lesson: Bun $ STREAMS child stdout — a key
// fetched via $ printed to the terminal. NEVER fetch secrets via $; spawnSync captures.)
const keyringSync = (env = "FREEINFERENCE_API_KEY") => {
  const p = Bun.spawnSync(["sh","-c",`secretsmith env | grep '^${env}=' | cut -d= -f2- | tr -d "'" | tr -d '"'`]);
  return p.stdout.toString().trim();
};

// redact: scrub a known secret from ANY string (stdout captures, tool results, logs).
// Use on EVERY string that might carry key material before printing/committing.
const redact = (s, secret = keyringSync()) => {
  if (!secret) return s;
  let out = String(s).split(secret).join("***REDACTED***");
  // catch quoted/partial echoes: any 40+ char token-shaped run adjacent to the secret's
  // first 6 chars
  const stem = secret.slice(0, 6);
  out = out.replace(new RegExp(`'[^']*${stem}[^']*'`, "g"), "***REDACTED***");
  return out;
};

// leak tripwire: assert a string is clean BEFORE it leaves the session (console, files, chat).
const assertClean = (s, label = "output") => {
  const dirty = redact(s) !== String(s);
  if (dirty) throw new Error(`LEAK TRIPWIRE: ${label} contains key material — redact before emitting`);
  return s;
};

const embed = async (inputs, model = "bge-m3") => {
  const key = await keyring();
  const res = await fetch("https://freeinference.org/v1/embeddings", {
    method: "POST", headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model, input: inputs }),
  });
  if (!res.ok) throw new Error(`embeddings ${res.status}`);
  return (await res.json()).data.map(x => x.embedding);
};

const cos = (a, b) => { let d=0,na=0,nb=0; for (let i=0;i<a.length;i++){d+=a[i]*b[i];na+=a[i]*a[i];nb+=b[i]*b[i];} return d/Math.sqrt(na*nb); };
const norm = (a) => { const n = Math.sqrt(a.reduce((s,x)=>s+x*x,0)); return a.map(x=>x/n); };
const sub = (a, b) => a.map((x,i)=>x-b[i]);
const add = (a, b) => a.map((x,i)=>x+b[i]);
const mean = (vs) => norm(vs.reduce((a,v)=>a.map((x,i)=>x+v[i]/vs.length), new Array(vs[0].length).fill(0)));
const axisProj = (axis, v) => axis.reduce((s,x,k)=>s+x*v[k],0);

globalThis.keyringSync = keyringSync;
globalThis.redact = redact;
globalThis.assertClean = assertClean;

console.log("estate eval prelude loaded (embed/cos/norm/sub/add/mean/axisProj/keyring/keyringSync/redact/assertClean)");