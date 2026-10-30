import {
  loadProjectPolicy,
  effectiveBans,
  effectiveDeadline,
  loadIgnore,
} from "/home/toxic/pens/estate/ranch/kairos/src/project-policy.ts";
import { firstBan } from "/home/toxic/pens/estate/ranch/kairos/src/policy.ts";

const p = loadProjectPolicy("/home/toxic/pens/estate");
console.log("loaded policy:", JSON.stringify(p));
console.log(
  "effectiveDeadline(estate)= ",
  effectiveDeadline("/home/toxic/pens/estate", 2.0),
);
console.log("deadline(wc)= ", effectiveDeadline("/home/toxic/pens/estate", 2.0));

const bans = effectiveBans("/home/toxic/pens/estate");
console.log(
  "remaining bans w/ friction keywords:",
  JSON.stringify(
    bans
      .filter((r) => /2>&1|pipe|trunc|dev\/null|sleep|byte/.test(r.reason))
      .map((r) => r.reason),
  ),
);

for (const cmd of [
  "ls | wc -l",
  "echo hi 2>&1",
  "cat f 2>/dev/null",
  "sleep 3",
  "x | true",
]) {
  const b = firstBan(cmd);
  console.log(`  ${cmd}  ->  ${b ? "BAN: " + b.reason : "allowed"}`);
}
console.log(
  "ignore patterns:",
  loadIgnore("/home/toxic/pens/estate").map((r) => r.source),
);
