
import json
L="/home/toxic/sovereign/hatch/agents/ember/coord/lanes"
now="2026-09-22T04:45:00Z"
jobs=[
 ("bridge-bootstrap-v2.json","done","Deliverable verified on box: coord/work/bridge-bootstrap-v2-design.md (written 2026-09-21, sha256 ok). Owner pre-restart, no live worker. Closed; re-open if coordinator re-staffs."),
 ("cron-resurrect.json","blocked","Safety-gate blocker untested post-restart; lane unowned (hb 2026-09-16). Downgraded from in-progress: needs gate re-assessment before any resume."),
 ("do-the-thing.json","active","Kept active but unowned: owner side-chat gone, deliverables pending (TOKEN correlation, ACCEPT tests, report to Chris). Needs owner pickup or coordinator decision."),
 ("vompl-entry-probe.json","done","Ephemeral coord-DB round-trip probe; purpose served pre-restart (coord-scout verified round-trip OK). Retired post-restart."),
]
for fn,status,verdict in jobs:
    p=L+"/"+fn
    d=json.load(open(p))
    d["status"]=status
    d["heartbeat"]=now
    d["deconfliction"]={"by":"cinder","at":now,"verdict":verdict}
    json.dump(d,open(p,"w"),indent=2)
    print(fn,"->",status)
