export const api=(p:string,o?:any)=>fetch(p,{headers:{'Content-Type':'application/json'},...o}).then(r=>r.json());
