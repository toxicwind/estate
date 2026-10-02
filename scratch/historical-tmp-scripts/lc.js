const {Database}=require("bun:sqlite");
const db=new Database(process.env.HOME+"/.yote/delivery-ledger.db",{readonly:true});
const rows=db.query("SELECT * FROM send_dedupe ORDER BY rowid DESC LIMIT 3").all();
console.log("DEDUPE:"+JSON.stringify(rows).slice(0,500));
const kv=db.query("SELECT k,v FROM ledger_kv").all();
console.log("KV:"+JSON.stringify(kv).slice(0,400));