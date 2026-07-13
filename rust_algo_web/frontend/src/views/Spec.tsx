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
