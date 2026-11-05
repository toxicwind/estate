"""Minimal xbmc* module stubs for testing the eternal addon off-box.
Rolled in-house (no npm lib exists for Kodi Python addon testing)."""
import sys
import types


def _cls(name, methods=()):
    def __init__(self, *a, **k): pass
    d = {"__init__": __init__}
    for m in methods:
        d[m] = lambda *a, **k: None
    # every instance gets the common read/write accessors
    d["getProperty"] = lambda *a, **k: ""
    d["setProperty"] = lambda *a, **k: None
    d["getSetting"] = lambda *a, **k: ""
    d["setSetting"] = lambda *a, **k: None
    return type(name, (), d)


class _Any(types.ModuleType):
    """Catch-all module: any missing attr becomes a no-op stub."""
    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        v = _cls(name)
        setattr(self, name, v)
        return v

xbmc = _Any("xbmc")
xbmc.LOGINFO = 1
xbmc.LOGERROR = 4
xbmc.log = lambda *a, **k: None
xbmc.getInfoLabel = lambda *a, **k: ""
xbmc.translatePath = lambda p, *a, **k: str(p)
xbmc.getCondVisibility = lambda *a, **k: False
xbmc.getLocalizedString = lambda *a, **k: ""
xbmc.executebuiltin = lambda *a, **k: None
xbmc.sleep = lambda *a, **k: None
xbmc.getLanguage = lambda *a, **k: "English"
xbmc.getRegion = lambda *a, **k: "US"
xbmc.getSetting = lambda *a, **k: ""
xbmc.setSetting = lambda *a, **k: None
xbmc.Player = _cls("Player", ("play", "stop", "seekTime", "isPlaying"))
xbmc.Monitor = _cls("Monitor", ("waitForAbort", "abortRequested"))

xbmcgui = _Any("xbmcgui")
xbmcgui.getCurrentWindowId = lambda: 10000

xbmcaddon = types.ModuleType("xbmcaddon")
class _Addon:
    def __init__(self, id=None): self.id = id or "plugin.video.eternal"
    def getSetting(self, k): return ""
    def setSetting(self, k, v): pass
    def getAddonInfo(self, k): return "/storage/.kodi/addons/plugin.video.eternal"
    def getLocalizedString(self, i): return ""
xbmcaddon.Addon = _Addon

xbmcplugin = _Any("xbmcplugin")

xbmcvfs = _Any("xbmcvfs")
xbmcvfs.translatePath = lambda p, *a, **k: str(p)
xbmcvfs.exists = lambda p, *a, **k: True

import sys
sys.modules.setdefault("xbmc", xbmc)
sys.modules.setdefault("xbmcgui", xbmcgui)
sys.modules.setdefault("xbmcaddon", xbmcaddon)
sys.modules.setdefault("xbmcplugin", xbmcplugin)
sys.modules.setdefault("xbmcvfs", xbmcvfs)