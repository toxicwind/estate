Beat: web
Angle: the paper's primary lane, after this hour's pick did not land

## GitLab fixes critical CVSS 10 file-read flaw
[CVE-2026-85706](https://techupdate24.com/gitlab-cve-2026-85706-file-read-vulnerability/) is a CVSS 10.0 path traversal in GitLab's commits API, and it lets an unauthenticated attacker read arbitrary files off a self-managed server. September 14 is CISA's deadline: the agency added the flaw to its [exploited-vulnerabilities catalog](https://gbhackers.com/cisa-warns-of-critical-gitlab-vulnerability-exploited-in-attacks/) on September 11 after confirming attacks in the wild. [The fixes shipped September 10](https://thearabianpost.com/gitlab-issues-urgent-patches-for-exploited-critical-flaw/) in 19.1.8, 19.2.6, and 19.3.2; with probing already reported in the wild, check the logs for odd commits-API requests and rotate tokens and keys.
- https://techupdate24.com/gitlab-cve-2026-85706-file-read-vulnerability/ (published 2026-09-12)
- https://thearabianpost.com/gitlab-issues-urgent-patches-for-exploited-critical-flaw/ (undated)
- https://gbhackers.com/cisa-warns-of-critical-gitlab-vulnerability-exploited-in-attacks/ (undated)
