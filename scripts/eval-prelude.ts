// estate eval prelude — %load this file in any future session cell.
// Provides: keyring, embed (bge-m3 lane), cos/norm/sub/add/mean/axisProj.

const keyring = (env = "FREEINFERENCE_API_KEY") =>
  new Response(Bun.spawnSync(["sh","-c",`secretsmith env | grep '^${env}=' | cut -d= -f2- | tr -d "'"`]).stdout).text().then(t => t.trim());

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

console.log("estate eval prelude loaded (embed/cos/norm/sub/add/mean/axisProj/keyring)");