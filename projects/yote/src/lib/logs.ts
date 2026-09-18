import { Glob } from "bun"
const LD=process.env.YOTE_LOG_DIR||"./logs"
export async function tailLog(n:string,l=50){const p=n.includes("/")?n:`${LD}/${n}.log`;const f=Bun.file(p);if(!(await f.exists()))return[];const t=await f.text();return t.trim().split("\n").slice(-l)}
export function listLogs(){try{const g=new Glob("**/*.log");return Array.from(g.scanSync(LD)).map(f=>`${LD}/${f}`)}catch{return[]}}
