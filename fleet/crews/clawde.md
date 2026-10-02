---
crew: 'clawde'
scope: 'metaclaw-runtime: .gitignore hardening, synthetic JWT test fixture, private publish to toxicwind/metaclaw-runtime, Sparkfall quarantine-resolved registry update'
owner: 'Ember'
status: 'DONE (2026-09-30) -- repo e7c74c5, ranch registry 7840ec1'
order: 99
registered: '2026-09-30'
updated: '2026-09-30'
---

# clawde

Per-crew ownership record. Edit the frontmatter above; the section 2 table in
docs/fleet-knowledgebase.md is generated from these files -- do not edit it by hand.

## 2026-09-30 -- metaclaw-runtime hardening + publish (DONE)

Chris's direct call: "gitignore hardened", publish -- not quarantine.

- Read every persistence/token path: `SessionManager` persists
  hatchSessionCookie/authToken/noiseNotaryToken to `data/session.json`.
- Wrote comprehensive `.gitignore`: data/session.json, *.pem/*.key, .env,
  logs, caches, build output. `src/**/*.js` intentionally TRACKED
  (test/runner.js imports compiled .js under plain node).
- Replaced JWT-shaped test fixture with unmistakably synthetic value
  (alg=none, .invalid issuer, nil UUID, literal fake signature).
- Tree swept for secret shapes -- clean. Auto-approval kept: it is the
  project's intended feature.
- Tests: `node test/runner.js` 9/9 green, `tsc --noEmit` clean.
- Repo: PRIVATE toxicwind/metaclaw-runtime @ e7c74c5 (ls-remote verified).
- Sparkfall registry: repo-registry.json + audit-batch-3.json
  quarantined-secrets -> published, ranch @ 7840ec1 (remote verified).
