import {useEffect,useState} from 'react';import {api} from '../lib/api';
export default function Arch(){
  const [cfg,setCfg]=useState<any>({ports:{}});
  useEffect(()=>{api('/api/config').then(setCfg)},[]);
  return <div><pre className="brutal">{JSON.stringify(cfg,null,2)}</pre></div>
}
