// fix-overlord.ts
import { readFileSync, writeFileSync } from "fs";

const path = `/home/toxic/sovereign/yote/src/lib/overlord.ts`;
let content = readFileSync(path, "utf-8");

// Remove broken catch-all disconnect handler
content = content.replace(
  /\/\/ Set up disconnect handler for auto-reconnect[\s\S]*?this\.scheduleReconnect\(\);\s*}\);/,
  `// GramJS autoReconnect handles disconnects; no manual handler needed`
);

// Fix scheduleReconnect to not call start()
content = content.replace(
  /this\.start\(\)\.catch\(\(e: any\) => \{\s*this\.log\(`reconnect failed: \$\{e\.message \?\? e\}`\);\s*this\.scheduleReconnect\(\);\s*\}\);/,
  `this.client.connect().catch((e: any) => {
        this.log(\`reconnect failed: \${e.message ?? e}\`);
        this.scheduleReconnect();
      });`
);

// Guard start() against double-connect
content = content.replace(
  /async start\(\): Promise<void> \{\s*if \(this\.started\) return;\s*await this\.client\.connect\(\);/,
  `async start(): Promise<void> {
    if (this.started) return;
    if (!this.client.connected) await this.client.connect();`
);

writeFileSync(path, content);
console.log("Fixed overlord.ts");