# Terminology Correction & Framework Mapping
## 2026-09-30 — Chris's explicit correction, applied

### The correction (verbatim user instruction)
> "Sorry, this isn't hatch, this is spark, I pasted wrong name replace hatch with spark and meta VM with Google VM you know here"

**Applied:** In the analytical framework document (the "Category Error" analysis), all references to "hatch" are read as **spark** (Gemini Spark), and all references to "meta VM" are read as **Google VM** (Google Cloud VM sandbox).

### Why the correction matters
The framework analyzes **Gemini Spark** (Google's always-on agent), not Muse/Hatch (Meta's). Conflating the two platforms is itself a category error of the same shape the document diagnoses: same word ("tasks", "VM", "agent"), different referent, wrong dispatch.

### Framework-to-estate mapping (isomorphic failure modes, different platforms)

| Framework concept (Gemini Spark / Google) | Estate referent (Muse / Hatch / yote) | Notes |
|---|---|---|
| spark (always-on cloud agent) | Ember / Hatch runtime cell + yote bridge | Different vendors; same autonomy problem |
| Google VM (gVisor sandbox, UID 1235, /working_dir) | hatch cell (systemd-nspawn container) | Both are sandboxed execution contexts with egress limits |
| /home/toxic (local bare-metal host) | /home/toxic on yote (CachyOS/Arch, 16 cores) | Same path, same role: the sovereign host |
| "Tasks" (internal DAG of async ops) | cron scheduled tasks, worker queue, classifier-sweep | The protected meaning. Never a consumer checklist. |
| Google Tasks API (consumer CRUD) | N/A — no consumer task API in this estate | The misdispatch target; the category error to guard against |
| Skills (MCP tool bundles) | ~/workspace/skills/ catalog | Same role: capability bundles |
| Schedules (background event dispatchers) | cron jobs (interval/daily/runonce) | Same role: background triggers |
| Outbound POST blocked → MCP gateway | Cell egress limits → yote-conn bridge | The bridge is this estate's gateway pattern |
| Lane BLOCKED → prompt human | Lane blocked/awaiting-input → stall | The failure mode under repair |

### The category error (restated for this estate)
When an instruction references "tasks" in the internal sense (a scheduled task definition, a worker-queue item, a DAG of operations), the runtime must NEVER dispatch it to a consumer checklist API. In this estate there is no Google Tasks connector, but the guard generalizes: **"tasks" in an autonomy/ops context always means the internal execution architecture** (cron jobs, worker queue, classifier sweep). Any tool call that treats an ops "task" as a consumer reminder/errand is a misattributed dispatch and must be flagged by the classifier.

### Standing rule going forward
- In framework/theory discussion: **spark**, **Google VM**.
- In estate operations: **Hatch cell**, **yote**, **/home/toxic**, **cron tasks**, **worker queue**.
- Never mix the two vocabularies in a single instruction without an explicit mapping line.
