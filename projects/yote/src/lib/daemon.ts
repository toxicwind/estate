import { mkdirSync, statSync, renameSync, readdirSync, createReadStream, createWriteStream } from "fs"
import { join, resolve, dirname } from "path"
import { fileURLToPath } from "url"
import { createGzip } from "zlib"
import { checkHealth } from "./health"
const __f=fileURLToPath(import.meta.url)
const __d=dirname(__f)
const PR=resolve(__d,"../..")
const LD=join(PR,"logs")
const MX=10*1024*1024
let lh:Record<string,boolean>={}
let ivs:ReturnType<typeof setInterval>[]=[]
let tk=0
const lg={info:(m:string)=>console.log(`[${new Date().toISOString()}] [daemon] ${m}`),warn:(m:string)=>console.warn(`[${new Date().toISOString()}] [daemon] WARN ${m}`),error:(m:string)=>console.error(`[${new Date().toISOString()}] [daemon] ERROR ${m}`)}
async function hc(){try{const h:any=await checkHealth();const ch=Object.keys(h).some(k=>h[k]!==lh[k]);if(ch||!Object.keys(lh).length){lg.info(`health ${Object.entries(h).map(([k,v]:any)=>`${k}=${v?"up":"down"}`).join(" ")}`);lh=h}}catch(e:any){lg.error(`health ${e.message??e}`)}}
function rot(){try{mkdirSync(LD,{recursive:true});for(const f of readdirSync(LD)){if(!f.endsWith(".log"))continue;const p=join(LD,f);try{const st=statSync(p);if(st.size>MX){const r=`${p}.${Date.now()}`;renameSync(p,r);const gz=`${r}.gz`;const inp=createReadStream(r);const out=createWriteStream(gz);const zip=createGzip();inp.pipe(zip).pipe(out);out.on("finish",()=>{try{require("fs").unlinkSync(r)}catch{}});lg.warn(`rot ${f} ${Math.round(st.size/1024/1024)}MB -> ${gz.split("/").pop()}`)}}catch{}}}catch(e:any){lg.error(`rot ${e.message??e}`)}}
async function ka(o?:any){if(!o)return;try{await o["client"]?.getMe();lg.info("tg keep ok")}catch(e:any){lg.warn(`tg ka ${e.message??e}`)}}
function tick(){tk++;lg.info(`tick ${tk} up ${Math.floor(process.uptime())}s`)}
export function startDaemon(o?:any){lg.info("started");mkdirSync(LD,{recursive:true});ivs.push(setInterval(()=>{hc().catch(()=>{})},60000));ivs.push(setInterval(()=>{rot()},300000));ivs.push(setInterval(()=>{ka(o).catch(()=>{})},600000));ivs.push(setInterval(()=>{tick()},60000));hc().catch(()=>{})}
export function stopDaemon(){for(const i of ivs)clearInterval(i);ivs=[];lg.info("stopped")}
if(import.meta.main){startDaemon()}
