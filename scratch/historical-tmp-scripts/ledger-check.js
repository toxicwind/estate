const {Database} = require("bun:sqlite");
const db = new Database(process.env.HOME+"/.yote/delivery-ledger.db",{readonly:true});
console.log("dedupe cols:", db.query("PRAGMA table_info(send_dedupe)").all().map(r=>r.name).join(","));
const rows = db.query("SELECT * FROM send_dedupe ORDER BY rowid DESC LIMIT 3").all();
console.log("dedupe:", JSON.stringify(rows).slice(0,600));
console.log("kv:", JSON.stringify(db.query("SELECT k,v FROM ledger_kv").all()).slice(0,400));
