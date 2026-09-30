const {Database}=require("bun:sqlite");
const db=new Database(process.env.HOME+"/.yote/delivery-ledger.db",{readonly:true});
console.log("TABLES:"+db.query("SELECT name FROM sqlite_master WHERE type='table'").all().map(r=>r.name).join(","));
const rows=db.query("SELECT * FROM send_dedupe ORDER BY rowid DESC LIMIT 3").all();
console.log("DEDUPE:"+JSON.stringify(rows).slice(0,600));