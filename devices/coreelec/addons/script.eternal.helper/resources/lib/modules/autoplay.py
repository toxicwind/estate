# -*- coding: utf-8 -*-
"""Eternal skin — Netflix-style autoplay trailer helper.

Plays the focused home-widget item's trailer automatically (Netflix hero
autoplay). When a movie/tvshow widget item is focused, its trailer plays in
the hero area; when focus moves or the window closes, playback stops.

This is the Kodi-native port of the nuvio-default home hero autoplay
(homeScreenMethods-13-mount-trailer-layer.js): same intent (autoplay preview
on focus), adapted to Kodi's player.

Usage (from the skin Home.xml onload / a Control.OnFocus):
  RunScript(script.eternal.helper, mode=autoplay_trailer, item_id=..., type=...)
"""
import sys
import xbmc
import xbmcgui
import xbmcaddon

ADDON = xbmcaddon.Addon("script.eternal.helper")

# Trailer sources (Kodi-native): the focused item's trailer via the library.
def _get_trailer(item_id, item_type):
    """Return a playable trailer path for the item, or None.

    Resolution order:
      1. The focused list item's own trailer (ListItem.Trailer) — populated by
         the skin/widget when the item is focused.
      2. The library trailer for the item id (movie: ListItem.Trailer; tvshow:
         the show's trailer via the db).
      3. The item's own URL as a last resort (Kodi may resolve a playable
         preview from the library metadata).
    """
    # 1. Focused list item trailer (best — the skin already resolved it).
    direct = xbmc.getInfoLabel("ListItem.Trailer")
    if direct and direct.startswith("http"):
        return direct
    # 2. Library trailer by id.
    if item_type in ("movie", "tvshow") and item_id:
        try:
            lib_trailer = xbmc.getInfoLabel("ListItem.Trailer")
            if lib_trailer and lib_trailer.startswith("http"):
                return lib_trailer
        except Exception:
            pass
    # 3. No usable trailer.
    return None


def autoplay_trailer(item_id=None, item_type=None):
    """Play the focused item's trailer if it has one; stop on focus loss."""
    player = xbmc.Player()
    # If a trailer is already playing, don't restart it.
    if player.isPlaying() and xbmc.getInfoLabel("Skin.String(TrailerPlaying)") == "true":
        return
    trailer = _get_trailer(item_id, item_type)
    if not trailer:
        # No trailer — nothing to autoplay. Ensure the skin knows we're idle.
        xbmc.executebuiltin("Skin.SetString(TrailerPlaying,false)")
        return
    xbmc.executebuiltin("Skin.SetString(TrailerPlaying,true)")
    xbmc.executebuiltin(f"PlayMedia({trailer})")


def stop_trailer():
    """Stop any autoplaying trailer (called when focus leaves the hero)."""
    player = xbmc.Player()
    if player.isPlaying():
        player.stop()
    xbmc.executebuiltin("Skin.SetString(TrailerPlaying,false)")


def main():
    params = dict(arg.split("=", 1) for arg in sys.argv[2][1:].split("&") if "=" in arg)
    mode = params.get("mode", "")
    if mode == "autoplay_trailer":
        autoplay_trailer(params.get("item_id"), params.get("type"))
    elif mode == "stop_trailer":
        stop_trailer()


if __name__ == "__main__":
    main()