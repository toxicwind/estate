# CoreELEC Addons: Eternal home-widget rebuild + redlight eradication + dependency resolution (hestia 10.0.0.246, 2026-11-07)

## Symptom / scope
Home widgets on the Eternal skin were broken: they pointed at `plugin.video.gears` (the
GDPd-era backup addon) and the live skin had drifted to `plugin.video.redlight` — neither
installed. Kodi flooded errors (`Unable to find plugin plugin.video.redlight`), showed
"Addon Required" banners, and the home widget rows (Movies/TV/Anime) didn't render.
Rebuild = restore the backed-up widgets onto the installed `plugin.video.eternal` and clear
every missing addon dependency.

## Root causes (layered — each layer would have re-broken it alone)
1. **Duplicate widget-include collision.** `skin.eternal` loads Home widgets via includes
   `MovieWidgets`/`TVShowWidgets`/`Custom1-6Widgets` defined in BOTH the backup-derived
   `script-fentastic-widget_*.xml` (gears, user) AND the stock `script-eternal-widget_*.xml`
   (redlight). Same include names -> LAST-loaded wins (redlight won).
2. **Database is the real source of truth.** Kodi REGENERATES the stock
   `script-eternal-*` widget XML on restart from persisted DB rows. Editing XML alone
   reverts. Widget `content_path` lives in `MyVideos<v>.db:path(strPath)` and
   `ViewModes<v>.db:view(path)` (229 rows + 1 path row each).
3. **Dead `script.eternal.helper` entrypoint.** The skin `<import addon="script.eternal.helper">`
   + many `RunScript(...)`; `resources/lib/default.py` had no `main`, so every call threw
   `ImportError: cannot import name 'main' from 'default'`.
4. **Renamed-addon stale package dir.** `script.module.eternalmgr` (AM Lite) was renamed
   from `script.module.acctmgr` — addon id + ALL imports are `eternalmgr.*` (207 refs) but
   `lib/` still held `acctmgr/` -> `No module named 'eternalmgr'`.
5. **Missing third-party deps** (9 total) produced "Addon Required" banners.

## Fixes
### Widgets (gears/redlight -> eternal)
- Convert each backup `script-fentastic-*.xml`: `sed s|plugin://plugin.video.gears/|plugin://plugin.video.eternal/|g`,
  place into `skin.eternal/xml/`. Retire stock `script-eternal-*.xml` (`.disabled`) to break the include collision.
- Repoint DB widget rows to eternal (source of truth):
  `MyVideos149.db:path`, `MyVideos131.db:path`, `ViewModes6.db:view` -> `replace(path, 'plugin.video.redlight','plugin.video.eternal')`
- Convert remaining `plugin://plugin.video.{redlight,gears}` nav targets across
  `Variables.xml`, `Custom_1108/1113-1116/1122`, etc. Leave `System.HasAddon(plugin.video.gears)`
  existence-checks (harmless).
- Reload: `Addons.SetAddonEnabled` on the ACTIVE skin is rejected; `Skin.Reload` RPC does not
  exist. Use `systemctl restart kodi` + `GUI.ActivateWindow home`.

### Dependencies (9 -> 1)
Installed real addons from the official Kodi mirror `mirror.hro.nl/xbmc/addons/piers/`
(`mirrors.kodi.tv` 302-redirects to a CDN that 404s) — zips carry top-level addon folder:
`inputstreamhelper`, `pysocks`, `beautifulsoup4`, `soupsieve`, `openweathermap.maps`,
`metadata.common.allmusic.com` / `.musicbrainz.org` / `.theaudiodb.com`.
`script.module.pil`: NOT on official mirrors, but the box ships native Pillow 12.3.0 at
`/usr/lib/python3.14/site-packages/PIL`. Added a `script.module.pil` addon (v12.3.0) with
EMPTY `lib/` so the Kodi gate is satisfied and `import PIL` resolves to the real system
Pillow (a `lib/PIL` shim would shadow+break it).
Only `vfs.libarchive` remains (needed by `service.subtitles.a4ksubtitles`): a system-distributed
binary VFS addon, source-only at `github.com/xbmc/vfs.libarchive`, no reachable prebuilt binary
— left for zipped-subtitle-only (decision: option a, leave as-is).

### Code fixes
- `script.eternal.helper`: `resources/lib/default.py` `main()` wraps `routing()`.
- `script.module.eternalmgr`: `mv addons/script.module.eternalmgr/lib/acctmgr lib/eternalmgr`.

## Contract / verification
- Log: `grep -cE "plugin.video.redlight|plugin.video.gears" kodi.log` == 0;
  `cannot import name 'main'` == 0; `No module named eternalmgr` == 0.
- Widget content: `Files.GetDirectory` on
  `plugin://plugin.video.eternal/?mode=build_tvshow_list&action=trakt_anime_trending`
  (and movie/tv) returns 21 items.
- Dev-twid: kodi.log shows `EternalTiming` metadata hits while widgets render.
- Remaining missing third-party import across addon.xml (filtering `xbmc.*`/`kodi.*` core):
  only `vfs.libarchive`.
- `import PIL; from PIL import Image; print(Image.__file__)` -> system Pillow.

## Gotchas / evidence chain
- The `repository.redwizard` repo (repo.redwizard.xyz) is a 302 GHOST -> google.com; never
  source addons from it.
- Dead URL-encoded Windows `iconImage` paths (`D:\Builds\...Redflix\...plugin.video.gears...`)
  are cosmetic; not nav.
- Widget probes can't hit :25270 JSON-RPC while Kodi is in heavy metadata load — the log
  counts are the reliable check then.
- Auth note: the box identifies as `hestia` (10.0.0.246); anomaly cross-refs the
  `coreelec-marantz-lg-hdmi-stuck-negotiation.md` doc from the same day (same box).