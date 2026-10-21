import { toolRetrieval, READY } from "./eap-shim.mjs";
console.log("import OK, READY:", JSON.stringify(READY), "| toolRetrieval:", typeof toolRetrieval);
const r = await toolRetrieval({ input: "hi" });
console.log("status", r.status, "ok", r.ok);
const b = r.body && typeof r.body === "object" ? JSON.stringify(r.body).slice(0, 160) : String(r.body).slice(0, 160);
console.log("body:", b);