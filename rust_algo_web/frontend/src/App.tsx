import {HashRouter,Routes,Route,NavLink} from 'react-router-dom';import Command from './views/Command';import Arch from './views/Architecture';import Fleet from './views/Fleet';import Spec from './views/Spec';import {useEffect} from 'react';
export default function App(){
 return <HashRouter><div style={{maxWidth:1600,margin:'0 auto',padding:16}}>
  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',borderBottom:'4px solid #000',paddingBottom:12,marginBottom:12}}><div style={{fontFamily:'Times New Roman',fontWeight:900,fontSize:28}}>EFFUSION<span style={{fontStyle:'italic',fontWeight:400}}>LABS</span><span style={{fontFamily:'Courier New',fontSize:11,marginLeft:8,border:'3px solid #000',padding:'2px 6px'}}>OS</span></div><nav style={{display:'flex',gap:6}}><NavLink to="/" className={({isActive})=>isActive?'chip on':'chip'}>COMMAND</NavLink><NavLink to="/arch" className={({isActive})=>isActive?'chip on':'chip'}>ARCH</NavLink><NavLink to="/fleet" className={({isActive})=>isActive?'chip on':'chip'}>FLEET</NavLink><NavLink to="/spec" className={({isActive})=>isActive?'chip on':'chip'}>SPEC</NavLink></nav></div>
  <Routes><Route path="/" element={<Command/>}/><Route path="/arch" element={<Arch/>}/><Route path="/fleet" element={<Fleet/>}/><Route path="/spec" element={<Spec/>}/></Routes>
 </div></HashRouter>
}
