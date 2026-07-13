export function VesselCard({name,port,online,ms}:{name:string,port:number,online:boolean,ms:number}){
 return <div className="brutal" style={{minWidth:280}}>
  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}><span style={{fontFamily:'Courier New',fontWeight:900}}>VESSEL {port}</span><span className={`chip ${online?'on':'off'}`}>{online?'EFFUSING ●':'DORMANT ○'}</span></div>
  <div style={{fontSize:28,fontWeight:900,textTransform:'uppercase',marginTop:8}}>{name}</div>
  <div className="residue" style={{marginTop:8}}>VALVE :{port}<br/>FLOW {ms}ms<br/>STATE {online?'OPEN':'CLOGGED'}</div>
  <div style={{display:'flex',gap:8,marginTop:10}}><button className="brutal-btn">{online?'QUENCH':'IGNITE'}</button><button className="brutal-btn" style={{background:'var(--eff-yellow)'}}>RESIDUE</button></div>
 </div>
}
