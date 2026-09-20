
## 2026-09-14 ~18:45 MDT — PAT INVESTIGATION: independent verification (auditor c2372f37)

Confirming + extending the 18:38 wrap-up with independent checks:

1. "GitHub proxy down" is NOT a token problem. There is no dedicated
   GitHub-proxy service; GitHub is fully reachable from awrawr-pc
   (api.github.com 200, gh authed as toxicwind). Unreachable ONLY from
   cells — cell egress is dead (proxy_fwd down, hatch-egress-proxy:3128
   silent, direct connections time out). If Chris saw GitHub fail from
   chat, that was the egress outage, not the PAT.
2. The pasted PAT is VALID: `GET /user` -> 200 as toxicwind. GitHub
   auto-revokes PATs found in public repos, so a live PAT = it was
   never pushed anywhere public. Answer to "did you commit it and
   push??": no.
3. `git log -S` on the fragment is clean in: sovereign, squawk,
   moonbox-skills-deploy, moonbox-live (including .git_repos/).
   Working-tree search across /home/toxic: clean. Both moonbox-live
   remotes (moonbox-live, local-work-archive) are PRIVATE anyway.
   Sole copy found: cell-local 2026-08-24 moonbox container snapshot
   dot_env.txt (GITHUB_PAT/GITHUB_PAT_1/GITHUB_PAT_2) — not in any git
   repo, never committed from there.
4. The 7 stripped .git_repos mirror configs are verified clean now
   (zero github_pat_/oauth: matches). github_repos_pat.json and
   github_user_pat.json do NOT contain this PAT. awrawr-pc gh CLI uses
   a gho_ OAuth token — unaffected.

CHRIS ACTION NEEDED: rotate the PAT (it's in the chat transcript —
treat as compromised) at github.com -> Settings -> Developer settings
-> Personal access tokens, then hand the new value over via the secure
vault flow. Places needing the new value: moonbox container env
(GITHUB_PAT[_1/_2]) and anywhere else it was pasted; the stripped
mirror configs now use clean https + gh auth and need nothing.
