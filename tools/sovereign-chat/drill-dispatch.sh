#!/bin/bash
# e3918e04 acceptance drills 1-4 (merged plan §6) against the TEST server :25121.
# Prints PASS/FAIL per assertion; exit code = number of failures.
set -u
PORT=${PORT:-25121}
B="http://127.0.0.1:$PORT"
T=$(cat /home/toxic/.config/sovereign-chat-token)
D=${DISPATCH_DIRECTIVES:-/home/toxic/dispatch-test/directives.md}
WT=${WT:-/home/toxic/wt/dispatch-e3918e04}
STATE=${STATE:-/home/toxic/dispatch-test/state}
MIRROR=${MIRROR:-/home/toxic/dispatch-test/mirror}
pass=0; fail=0
ok()  { echo "PASS: $1"; pass=$((pass+1)); }
bad() { echo "FAIL: $1"; fail=$((fail+1)); }
api() { curl -s -H "Authorization: Bearer $T" -H "Content-Type: application/json" -X "$1" "$B$2" ${3:+-d "$3"} --max-time 15; }
jget() { python3 -c "import json,sys; d=json.load(sys.stdin); print(eval(sys.argv[1]))" "$1"; }
wait_s() { local end=$(( $(date +%s) + $1 )); while [ "$(date +%s)" -lt "$end" ]; do read -t 2 < /dev/null || true; done; }

echo "=== setup: join drill agent ==="
AGENT=$(api POST /v1/join '{"name":"drill-lane-4","chat_id":"drill-e3918e04","summoner":"lane-4","surface":"drill"}' | jget "d['agent_id']")
[ -n "$AGENT" ] && ok "joined as $AGENT" || bad "join failed"
api POST /v1/presence "{\"agent_id\":\"$AGENT\",\"activity\":\"drill\"}" > /dev/null

echo "=== DRILL 1: wedged claim flagged, NOT requeued ==="
api POST /v1/dispatch/tasks '{"task_id":"drill-wedge-1","priority":10,"lease_secs":25,"cadence_secs":20,"payload":"drill 1"}' > /dev/null
L1=$(api POST /v1/dispatch/tasks/drill-wedge-1/claim "{\"claimed_by\":\"$AGENT\"}" | jget "d['claim']['lease_id']")
[ -n "$L1" ] && ok "claimed drill-wedge-1 lease $L1 (lease 25s, cadence 20s)" || bad "claim failed"
# wedged at min(3*20, 0.5*25)=12.5s of silence; lease expires at 25s. Wait 32s.
wait_s 32
api POST /v1/presence "{\"agent_id\":\"$AGENT\",\"activity\":\"drill-1-still-here\"}" > /dev/null
SCAN1=$(api POST /v1/dispatch/wedge-scan '{}')
echo "$SCAN1" | grep -q '"to":"wedged"' && ok "wedge-scan flagged drill-wedge-1 WEDGED" || bad "no wedged transition: $SCAN1"
ST1=$(api GET "/v1/dispatch/tasks?status=claimed" | jget "[t['task_id'] for t in d['tasks']]")
echo "$ST1" | grep -q drill-wedge-1 && ok "task still claimed (NOT requeued)" || bad "task wrongly requeued: $ST1"
EXP1=$(api POST /v1/dispatch/claims/$L1/expire '{"by":"drill"}')
echo "$EXP1" | grep -q '"ok":false' && echo "$EXP1" | grep -q -i wedged && ok "expire on WEDGED+fresh-heartbeat rejected" || bad "expire should have been rejected: $EXP1"
PROG1=$(api POST /v1/dispatch/claims/$L1/progress '{"state":"progressing"}')
echo "$PROG1" | grep -q '"signal":"wedge-cleared"' && ok "progress emitted wedge-cleared" || bad "no wedge-cleared: $PROG1"
api POST /v1/dispatch/claims/$L1/ack '{"by":"drill"}' > /dev/null && ok "ack closed drill-wedge-1" || bad "ack failed"

echo "=== DRILL 2: dead holder reclaimed after threshold ==="
api POST /v1/dispatch/tasks '{"task_id":"drill-dead-1","priority":10,"lease_secs":20,"cadence_secs":10,"payload":"drill 2"}' > /dev/null
GHOST="ghost-never-heartbeats"
L2=$(api POST /v1/dispatch/tasks/drill-dead-1/claim "{\"claimed_by\":\"$GHOST\"}" | jget "d['claim']['lease_id']")
[ -n "$L2" ] && ok "ghost claimed drill-dead-1 lease $L2" || bad "ghost claim failed"
# lease expires at 20s; dead when wedge_ts > max(3*10, 0.5*20)=30s and holder absent. Wait 36s.
wait_s 36
EXP2=$(api POST /v1/dispatch/claims/$L2/expire '{"by":"drill"}')
echo "$EXP2" | grep -q '"requeued":true' && ok "dead claim reclaimed (requeued)" || bad "reclaim failed: $EXP2"
echo "$EXP2" | grep -q '"new_priority":11' && ok "starved task priority rose 10 -> 11" || bad "no priority bump: $EXP2"
POISON=$(api POST /v1/dispatch/tasks/drill-dead-1/claim "{\"claimed_by\":\"$GHOST\"}")
echo "$POISON" | grep -q anti-poison && ok "anti-poison blocked ghost re-claim" || bad "anti-poison missing: $POISON"
L2B=$(api POST /v1/dispatch/tasks/drill-dead-1/claim "{\"claimed_by\":\"$AGENT\"}" | jget "d['claim']['lease_id']")
[ -n "$L2B" ] && ok "drill agent re-claimed (lease $L2B)" || bad "re-claim failed"
api POST /v1/dispatch/claims/$L2B/ack '{"by":"drill"}' > /dev/null && ok "ack closed drill-dead-1" || bad "ack failed"

echo "=== DRILL 3: synthetic fixtures + metrics hand-count ==="
api POST /v1/dispatch/tasks '{"task_id":"drill-fix-healthy","priority":5,"cadence_secs":60,"payload":"A"}' > /dev/null
LA=$(api POST /v1/dispatch/tasks/drill-fix-healthy/claim "{\"claimed_by\":\"$AGENT\"}" | jget "d['claim']['lease_id']")
api POST /v1/dispatch/claims/$LA/progress '{"state":"progressing"}' > /dev/null
api POST /v1/dispatch/tasks '{"task_id":"drill-fix-wedged","priority":5,"cadence_secs":60,"payload":"B"}' > /dev/null
LB=$(api POST /v1/dispatch/tasks/drill-fix-wedged/claim "{\"claimed_by\":\"$AGENT\"}" | jget "d['claim']['lease_id']")
api POST /v1/dispatch/tasks '{"task_id":"drill-fix-dead","priority":5,"cadence_secs":60,"payload":"C"}' > /dev/null
LC=$(api POST /v1/dispatch/tasks/drill-fix-dead/claim '{"claimed_by":"ghost2-never-here"}' | jget "d['claim']['lease_id']")
/home/toxic/.bun/bin/bun -e '
import { Database } from "bun:sqlite";
const db = new Database("'$STATE'/dispatch.db");
const old = (s) => new Date(Date.now() - s*1000).toISOString();
db.run("UPDATE dispatch_leases SET wedge_ts = ? WHERE lease_id = ?", [old(200), '"$LB"']);
db.run("UPDATE dispatch_leases SET wedge_ts = ? WHERE lease_id = ?", [old(400), '"$LC"']);
console.log("fixtures backdated");'
api POST /v1/presence "{\"agent_id\":\"$AGENT\",\"activity\":\"drill-3\"}" > /dev/null
SCAN3=$(api POST /v1/dispatch/wedge-scan '{}')
echo "$SCAN3" | python3 -c "
import json,sys
d=json.load(sys.stdin); tr={(t['task_id'],t['to']) for t in d['transitions']}
assert ('drill-fix-wedged','wedged') in tr, f\"missing wedged: {tr}\"
assert ('drill-fix-dead','dead') in tr, f\"missing dead: {tr}\"
healthy=[s for t,s in tr if t=='drill-fix-healthy']
assert all(s=='alive' for s in healthy), f\"healthy misclassified: {tr}\"
print('signals correct:', dict(tr))" && ok "fixtures classified: healthy alive, wedged, dead" || bad "fixture classification wrong: $SCAN3"
# metrics hand-count: direct DB counts vs /v1/dispatch/metrics
HAND=$(/home/toxic/.bun/bin/bun -e '
import { Database } from "bun:sqlite";
const db = new Database("'$STATE'/dispatch.db");
const c = (s) => db.query(s).get().c;
console.log(JSON.stringify({
  claims: c("SELECT COUNT(*) c FROM dispatch_leases"),
  acks: c("SELECT COUNT(*) c FROM dispatch_acks"),
  expires: (db.query("SELECT n FROM dispatch_counters WHERE name=\x27expire\x27").get()||{n:0}).n,
  dead_letters: c("SELECT COUNT(*) c FROM dispatch_dead_letters"),
}));')
MET=$(api GET /v1/dispatch/metrics)
echo "$MET" | python3 -c "
import json,sys
m=json.load(sys.stdin)['metrics']; h=json.loads('$HAND')
assert m['counters'].get('claim',0)==h['claims'], (m['counters'],h)
assert m['counters'].get('ack',0)==h['acks']
assert m['counters'].get('expire',0)==h['expires']
assert m['counters'].get('dead_letter',0)==h['dead_letters']
assert m['duplicate_execution_violations']==0
print('metrics match hand count:', h)" && ok "metrics counters match hand-counted fixture exactly" || bad "metrics mismatch"
# local wedge.py forensic mode agrees with server classification
/home/toxic/wt/dispatch-e3918e04/fleet/wedge.py --local --state-dir "$STATE" --json | python3 -c "
import json,sys
d=json.load(sys.stdin); sigs={c['task_id']:c['signal'] for c in d['live_claims']}
assert sigs.get('drill-fix-wedged')=='wedged', sigs
assert sigs.get('drill-fix-dead')=='dead', sigs
print('local classifier agrees:', sigs)" && ok "fleet/wedge.py --local agrees with server" || bad "wedge.py --local mismatch"

echo "=== DRILL 4: transport push, since_seq replay, fallback, resume ==="
rm -f /home/toxic/dispatch-test/ws-frames.jsonl
cat > /home/toxic/dispatch-test/ws-listen.ts <<EOF
const t = (await Bun.file("/home/toxic/.config/sovereign-chat-token").text()).trim();
const ws = new WebSocket("ws://127.0.0.1:$PORT/v1/stream?subscribe=fleet-claims,fleet-dispatch&token="+t);
ws.onmessage = async (e) => {
  const prev = await Bun.file("/home/toxic/dispatch-test/ws-frames.jsonl").text().catch(() => "");
  await Bun.write("/home/toxic/dispatch-test/ws-frames.jsonl", prev + e.data + "\n");
};
await new Promise((r) => setTimeout(r, 20000));
EOF
setsid nohup /home/toxic/.bun/bin/bun /home/toxic/dispatch-test/ws-listen.ts > /dev/null 2>&1 < /dev/null &
read -t 2 < /dev/null || true
api POST /v1/dispatch/tasks '{"task_id":"drill-transport-1","priority":5,"payload":"t4"}' > /dev/null
L4=$(api POST /v1/dispatch/tasks/drill-transport-1/claim "{\"claimed_by\":\"$AGENT\"}" | jget "d['claim']['lease_id']")
[ -n "$L4" ] && ok "push claim via :$PORT" || bad "claim push failed"
read -t 3 < /dev/null || true
grep -q '"type": "claim"' /home/toxic/dispatch-test/ws-frames.jsonl 2>/dev/null || grep -q '"type":"claim"' /home/toxic/dispatch-test/ws-frames.jsonl 2>/dev/null
[ $? -eq 0 ] && ok "WS push frame received reactively" || bad "no WS claim frame"
api GET "/v1/rooms/fleet-claims/messages?since_seq=0&limit=50" | grep -q drill-transport-1 && ok "since_seq replay confirms claim" || bad "replay missing claim"
# fallback engage: dead port
FB=$(python3 $WT/fleet/dispatch_fallback.py push --url http://127.0.0.1:25999/v1/dispatch/tasks --payload '{"task_id":"drill-fb-1","priority":5,"payload":"fb"}' --directives "$D")
echo "$FB" | grep -q '"fallback": "engaged"' && ok "fallback engaged on unreachable server" || bad "fallback did not engage: $FB"
grep -q "dispatch-fallback.*ENGAGED" "$D" && ok "frame landed in directives.md" || bad "directives.md missing ENGAGED line"
# restore: replay to live port
RP=$(python3 $WT/fleet/dispatch_fallback.py replay --url-override "$B/v1/dispatch/tasks" --directives "$D")
echo "$RP" | grep -q '"replayed": 1' && ok "replay delivered 1 queued frame" || bad "replay failed: $RP"
api GET "/v1/dispatch/tasks?status=pending" | grep -q drill-fb-1 && ok "replayed task drill-fb-1 live on server" || bad "replayed task missing"
python3 $WT/fleet/dispatch_fallback.py latencies --directives "$D" | grep -q '"p50"' && ok "push latency p50/p99 reported" || bad "latency report missing"
# mirrors
[ -s $MIRROR/lease-ledger.jsonl ] && ok "lease-ledger.jsonl mirror has $(wc -l < $MIRROR/lease-ledger.jsonl) lines" || bad "mirror empty"
grep -q wedge_signal $MIRROR/lease-ledger.jsonl && ok "wedge signals mirrored to JSONL" || bad "no wedge signals in mirror"

echo
echo "=== RESULT: $pass passed, $fail failed ==="
exit $fail
