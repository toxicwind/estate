# Firefox enterprise policies — /etc/firefox/policies/

Deployed from `projects/yote/ops/firefox-policies/` by `firefox-rs-repair.sh`
(`--install` / `--repair`). Do not hand-edit on the box; change the repo
source and re-run the script (or let the pacman hook / path unit re-apply it).

## Current policies

| Policy | Value | Why |
|---|---|---|
| `DisableAppUpdate` | `true` | This box runs `firefox-nightly` from pacman. In-browser updates would fight the package manager and can leave a half-updated install. Updates come from `pacman -Syu`; the `firefox-rs-repair` pacman hook re-applies this repair after every upgrade. |

## Deliberately NOT set (pending final source trace): `DisableFirefoxStudies`

Chris's requirement is: no experiments/studies enrolled, Remote Settings
security/update collections keep working, emergency remediation preserved if
separable from experimentation.

Status 2026-09-21: `DisableFirefoxStudies` is under active source trace
(mozilla-central `browser/components/enterprisepolicies/Policies.sys.mjs`).
Verified so far: the handler calls `manager.disallowFeature("Shield")` and
locks CFR prefs off. The open question being nailed down with exact
file:line citations is what the `"Shield"` feature string gates — whether it
covers only studies/experiments or also the Normandy recipe pipeline that
carries emergency remediation. Until that trace lands with citations, this
policy stays OUT: the safe posture is to not touch a gate whose blast radius
is unconfirmed.

The chosen mechanism instead (independent of that outcome):

- **No enrollment happens without data.** The 2026-09-21 incident was a
  poisoned `services.settings.server` (`data:,#remote-settings-dummy/v1`, a
  Mozilla test fixture from `services/settings/Utils.sys.mjs`) plus a blanked
  `app.normandy.api_url`, which starved ALL Remote Settings syncs (no
  successful client sync since 2026-07-22). With the real server restored,
  recipe delivery resumes and enrollment decisions are driven by actual
  recipes again.
- **Enrollment audit** (2026-09-21): existing enrollments inventoried; the
  no-future-studies posture is enforced by keeping the recipe pipeline
  honest, not by breaking the pipeline.
- If the trace shows `DisableFirefoxStudies` (or a narrower knob) suppresses
  studies while preserving remediation, it will be added here with the exact
  mechanism and source lines cited.

## Remote Settings collections this preserves

Security- and update-relevant collections that keep syncing with the default
server (none are gated by the studies policy):

- `hijack-blocklists`, `cert-revocation` / blocklist family
- `addons-manager-settings`, `addons-data-leak-blocker-domains`
- `search-config-v2`, `doh-config` / `doh-providers`
- `fingerprinting-protection-overrides`, `query-stripping`,
  `anti-tracking-url-decoration`, `cookie-banner-rules-list`
- `password-rules`, `change-password-urls`, `fxmonitor-breaches`
- `nimbus-desktop-experiments`, `nimbus-secure-experiments` (recipe delivery)

## Incident log

- 2026-09-21: `services.settings.server` found set to
  `data:,#remote-settings-dummy/v1` and `app.normandy.api_url` blanked in the
  Nightly profile. Provenance hunt in progress (see fleet). Repaired by
  `firefox-rs-repair.sh v2`: prefs.js cleaned, good values pinned in
  `user.js` (Firefox reads it at every startup, never writes it), policies
  deployed, pacman hook + systemd path unit installed for durability.
