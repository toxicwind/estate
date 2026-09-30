# kataware-doki 🧵

![status](https://img.shields.io/badge/status-empty_repo_no_commits_yet-lightgrey)
![concept](https://img.shields.io/badge/concept-distributed_inference-6b21a8)

**The Thread That Connects** — distributed inference network architecture.

> ⚠️ **This repo is empty** (no commits as of 2026-09-30). What follows is
> intent, not implementation — nothing here is built yet.

## Intent

A network architecture for distributed inference: multiple inference nodes
connected as a single mesh ("the thread that connects"), so model serving
can span machines instead of living on one box.

## Roadmap (planned, unverified)

- [ ] Topology: node discovery and mesh join/leave
- [ ] Routing: request dispatch across the mesh
- [ ] Failover: node loss without dropped sessions
- [ ] Benchmarks: latency/throughput across topologies

## Estate context

The toxicwind estate already runs inference infrastructure that a mesh like
this would build on: the herd router (`:25100`, sovereign-projects), the
`kimi-auto` alias forwarder, and the 43-MCP federation via mcpproxy
(`:25109`). Any design here should assume those as the local substrate —
see the [fleet knowledgebase](https://github.com/toxicwind/sovereign-projects/blob/main/docs/fleet-knowledgebase.md).

---

When code lands, this README gets replaced with the real thing — audited
against the code, per the readme-audit-first skill.
