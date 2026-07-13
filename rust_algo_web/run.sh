cd /home/toxic/sovereign/rust_algo_web

cat > Cargo.toml <<'CT'
[package]
name = "sovereign_web"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full"] }
axum = { version = "0.7", features = ["ws"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tower-http = { version = "0.6", features = ["fs","cors"] }
tower = "0.4"
reqwest = { version = "0.12", features = ["json","rustls-tls"] }
dotenvy = "0.15"
notify = "6"
toml = "0.8"
CT

cat > frontend/src/views/Spec.tsx <<'TSX'
import {useEffect,useState} from 'react';import {api} from '../lib/api';
export default function Spec(){
  const [loras,setL]=useState<any[]>([]);
  const [prompt,setP]=useState('');
  const [res,setR]=useState<any>(null);
  useEffect(()=>{api('/api/loras').then(setL)},[]);
  return <div>
    <div className="brutal" style={{marginBottom:12}}><h2 style={{fontWeight:900}}>SPEC — BEELLAMA ROUTER</h2></div>
    <div style={{display:'flex',gap:8,marginBottom:12}}>
      <textarea value={prompt} onChange={e=>setP((e.target as HTMLTextAreaElement).value)} style={{flex:1,border:'4px solid #000',padding:10}} rows={3}/>
      <button className="brutal-btn" onClick={async()=>{const r=await api('/api/route',{method:'POST',body:JSON.stringify({prompt})});setR(r)}}>DISTILL</button>
    </div>
    {res&&<div className="residue">{JSON.stringify(res)}</div>}
    <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(300px,1fr))',gap:12}}>
      {loras.map((l:any)=><div key={l.id} className="brutal"><b>{l.name}</b><div>{l.id}</div></div>)}
    </div>
  </div>
}
TSX

cat > frontend/src/views/Architecture.tsx <<'TSX'
import {useEffect,useState} from 'react';import {api} from '../lib/api';
export default function Arch(){
  const [cfg,setCfg]=useState<any>({ports:{}});
  useEffect(()=>{api('/api/config').then(setCfg)},[]);
  return <div><pre className="brutal">{JSON.stringify(cfg,null,2)}</pre></div>
}
TSX

# verify fix applied
grep -n "const \[loras" frontend/src/views/Spec.tsx
head -3 Cargo.toml

# build
cd frontend && bun run build && cd .. && cargo run