#!/usr/bin/env bun
// @ts-nocheck
// fix.ts - Antigravity IDE /opt/antigravity-ide/Antigravity-IDE fix
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { execSync } from "node:child_process";

const HOME = os.homedir();
const log = (m:string)=>console.log(`[fix] ${m}`);
const ok = (m:string)=>console.log(`[ok] ${m}`);
const warn = (m:string)=>console.log(`[warn] ${m}`);
const exists = (p:string)=>{ try{return fs.existsSync(p)}catch{return false} };
const tryExec = (cmd:string)=>{ try{return execSync(cmd,{stdio:"pipe"}).toString()}catch{return""} };

// 1. Bun EADDRINUSE /tmp/530gsvetyh3.sock - oven.bun-vscode-0.0.32
log("1/5 kill stale bun socket");
tryExec("fuser -k /tmp/530gsvetyh3.sock 2>/dev/null; lsof -t /tmp/530gsvetyh3.sock 2>/dev/null | xargs -r kill -9 2>/dev/null; true");
try{ fs.unlinkSync("/tmp/530gsvetyh3.sock"); ok("unlinked socket"); }catch{}

// 2. autoActivationType workspace error
log("2/5 clean workspace settings");
function cleanJson(p:string){
  if(!exists(p)) return;
  try{
    const j = JSON.parse(fs.readFileSync(p,"utf8"));
    let ch=false;
    for(const k of ["autoActivationType","python-envs.terminal.autoActivationType"]) if(k in j){ delete j[k]; ch=true; }
    if(j.python?.terminal?.autoActivationType){ delete j.python.terminal.autoActivationType; ch=true; }
    if(ch){ fs.writeFileSync(p, JSON.stringify(j,null,2)+"\n"); ok(`cleaned ${p}`); }
  }catch{}
}
let cur = process.cwd();
for(let i=0;i<6;i++){ cleanJson(path.join(cur,".vscode","settings.json")); const up=path.dirname(cur); if(up===cur) break; cur=up; }

// 3. PET restart loop
log("3/5 clean PET cache");
tryExec("pkill -9 -f 'python-envs|pet.server|ms-python.vscode-python-envs' 2>/dev/null; true");
for(const b of [path.join(HOME,".config","Antigravity IDE"), path.join(HOME,".config","Antigravity"), path.join(HOME,".antigravity-ide")]){
  for(const rel of ["User/globalStorage/ms-python.python","User/globalStorage/ms-python.vscode-python-envs","User/globalStorage/ms-python.vscode-pylance","CachedData"]){
    const p = path.join(b,rel);
    try{ fs.rmSync(p,{recursive:true,force:true}); }catch{}
  }
}

// 4. CRITICAL: language_server exited code 2 - unknown flags -plan_model -requested_model
log("4/5 patch language_server_linux_x64");
const explicitBins = [
  "/opt/antigravity-ide/Antigravity-IDE/resources/app/extensions/antigravity/bin/language_server_linux_x64",
  "/opt/antigravity-ide/resources/app/extensions/antigravity/bin/language_server_linux_x64",
];
const discovered = tryExec(`find /opt/antigravity-ide -type f -name "language_server_linux_x64" 2>/dev/null`).split("\n").filter(Boolean);
const allBins = [...new Set([...explicitBins, ...discovered])];

if(allBins.length===0) warn("no binary found, check tree output");
for(const bin of allBins){
  if(!exists(bin)) continue;
  try{
    const head = fs.readFileSync(bin,"utf8").slice(0,120);
    if(head.startsWith("#!") && head.includes("language_server_linux_x64.real")){ ok(`already shimmed ${bin}`); continue; }
  }catch{}
  const real = bin + ".real";
  log(`shimming ${bin}`);
  const wrapper = `#!/usr/bin/env bash
set -e
SELF="$0"
DIR="$(dirname "$(readlink -f "$SELF" 2>/dev/null || realpath "$SELF" 2>/dev/null || echo "$SELF")")"
REAL="$DIR/language_server_linux_x64.real"
[ -x "$REAL" ] || REAL="${real}"
args=()
skip=0
for a in "$@"; do
  if [ "$skip" = "1" ]; then skip=0; continue; fi
  case "$a" in
    -plan_model|--plan_model|-requested_model|--requested_model) skip=1; continue;;
    -plan_model=*|--plan_model=*|-requested_model=*|--requested_model=*) continue;;
  esac
  args+=("$a")
done
exec "$REAL" "\${args[@]}"
`;
  try{
    if(!exists(real)) fs.renameSync(bin, real);
    fs.writeFileSync(bin, wrapper, {mode:0o755});
    tryExec(`chmod +x "${bin}" "${real}"`);
    ok(`patched ${bin}`);
  }catch(e:any){
    warn(`need sudo for ${bin}: ${e.message}`);
    const tmp = `/tmp/antigravity-wrapper-${Date.now()}.sh`;
    fs.writeFileSync(tmp, wrapper, {mode:0o755});
    tryExec(`sudo mv "${bin}" "${real}" 2>/dev/null; sudo cp "${tmp}" "${bin}" && sudo chmod +x "${bin}" "${real}" && rm "${tmp}"`);
    ok(`patched with sudo ${bin}`);
  }
}

// 5. patch extension.js launcher as backup
log("5/5 patch extension.js launcher");
const extJs = "/opt/antigravity-ide/Antigravity-IDE/resources/app/extensions/antigravity/dist/extension.js";
if(exists(extJs)){
  try{
    let src = fs.readFileSync(extJs,"utf8");
    if(src.includes("plan_model")){
      let patched = src.replace(/,\s*["']-plan_model["']\s*,\s*[A-Za-z0-9_$.\[\]"]+/g,"");
      patched = patched.replace(/,\s*["']-requested_model["']\s*,\s*[A-Za-z0-9_$.\[\]"]+/g,"");
      patched = patched.replace(/["']-plan_model["'][^,]*,?/g,"");
      patched = patched.replace(/["']-requested_model["'][^,]*,?/g,"");
      if(patched.length !== src.length){
        try{ fs.writeFileSync(extJs, patched); ok("patched extension.js"); }
        catch{ const t=`/tmp/ext-${Date.now()}.js`; fs.writeFileSync(t,patched); tryExec(`sudo cp "${t}" "${extJs}" && rm "${t}"`); ok("patched extension.js with sudo"); }
      }
    }
  }catch(e){ warn(`ext patch skip ${e}`); }
}

console.log("\n--- verify ---");
console.log(tryExec(`ls -lh /opt/antigravity-ide/Antigravity-IDE/resources/app/extensions/antigravity/bin/language_server* 2>/dev/null || ls -lh /opt/antigravity-ide/**/language_server* 2>/dev/null`));
console.log("Done. Fully quit Antigravity IDE then reopen. If it still shows code 2, run: /opt/antigravity-ide/Antigravity-IDE/resources/app/extensions/antigravity/bin/language_server_linux_x64.real --help");