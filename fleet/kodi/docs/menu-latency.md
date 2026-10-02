# Menu-latency diagnosis (2026-09-18)

Chris: "the ass menu loading etc it's bizzare on both boxes."

## 246 (CoreELEC) — from kodi.log via SSH

1. **Red Light spawns 6 monitor services at every startup** — SimklMonitor,
   MDBListMonitor, PunchPlayMonitor, WidgetRefresher, AutoStart,
   ServiceExpiryAlerts (+ Deferred Service Setup). Every one hits the network.
   Prime suspect for main-menu sluggishness: Python threads competing on boot
   and on every menu open that triggers widget refresh.
2. **Missing skin windows** — `Window Translator: Can't find window
   nextep_handoff.xml / sources_playback.xml / sources_results.xml / extras.xml`.
   Culprit: `plugin.video.redlight` (references found in its sources.py/player.py).
   Red Light's dialogs expect Fen/Umbrella-style skin XMLs that Fen-tastic does
   not ship → broken/slow dialog rendering during browse + playback flows.
3. **Dead scrapers stalling source resolution** — aiostreams log shows Knaben
   API 403, Sootio TB / WebStreamr / yastream timeouts, Search capabilities
   fetch failures. Every browse that waits on these eats a full timeout.
4. **Repeated audio-sink re-init** — `CActiveAESink::OpenSink` cycling; mostly
   tied to stop/open/seek during testing, but `CAEStreamInfo::GetDuration -
   invalid stream type` also appears in normal playback.
5. No `advancedsettings.xml` tuning (file only pins `skin.fentastic`).

## 225 (Android TV) — JSON-RPC only, no log access

- Same `plugin.video.redlight 2.6.4` installed → same 6-service startup tax and
  same missing-window dialogs (against Nimbus instead of Fen-tastic).
- Extra weight vs 246: 35 addons 246 doesn't have, incl. `pvr.iptvsimple`,
  chains scrapers, `service.wizinstaller`, `service.installmybinaries`,
  three extra skins. Nimbus + `script.nimbus.helper` is the active skin stack.
- 225's kodi.log is unreachable (no SSH/ADB creds). If menu slowness persists
  after the Red Light fixes, next step is ADB or the Log Viewer addon.

## Fixes queued

- [ ] Red Light: disable unused monitors (Simkl/MDBList/Punch/Expiry) if the
      features aren't used — biggest single win on both boxes.
- [ ] aiostreams: disable dead scrapers (Knaben, Sootio TB, WebStreamr, yastream).
- [ ] 225: decide on the 35 extra addons (report-only in `kodi-audit addons --diff`;
      PVR/live-TV plugins may be in active bedroom use — needs Chris's call).
- [ ] Consider skin-provided window XMLs or disabling Red Light's custom dialogs.
