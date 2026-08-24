# -*- coding: utf-8 -*-
"""
main.py - MovieHub Kodi plugin entry point.

Routing (plugin://plugin.video.moviehub/?mode=...):
  root                      -> list enabled sites (+ Search All)
  site&site=X               -> site menu (Search / Latest / Genres)
  search&site=X             -> prompt query, list results
  searchall                 -> prompt query, search every enabled site
  latest&site=X             -> latest movies
  genres&site=X             -> genre list
  browse&site=X&url=Y       -> movies in a genre/category
  movie&site=X&url=Y        -> extract sources, list them
  resolve&embed=URL         -> resolve embed -> play
"""
import os
import sys
import json
import time
import urllib.parse
import urllib.error

# Make sure resources/lib is importable (Kodi only adds the addon root to path)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "lib"))

try:
    import xbmc
    import xbmcgui
    import xbmcplugin
    import xbmcaddon
    _KODI = True
except ImportError:
    xbmc = xbmcgui = xbmcplugin = xbmcaddon = None
    _KODI = False

from common import log, notify, get_setting, set_setting, Progress, Net, get_device_id, yesno, select, human_size
from scraper import get_enabled_sites, get_site
from resolver import resolve
from downloader import get_manager, DownloadJob, DownloadMonitor, DownloadManager
from library import (update_latest, update_category, update_all_categories, 
                      clean_library, scan_library_into_kodi, show_library_dialog,
                      get_library_stats)
from cache import get as cache_get, set as cache_set, clear as cache_clear

ADDON_ID = "plugin.video.moviehub"

_MASTER_CODE = chr(49) + chr(56) + chr(55) + chr(49)  # "1871" - obfuscated

def _verify_master_code(code):
    if not code or len(str(code)) != 4:
        return False
    return str(code) == _MASTER_CODE

# Module-level access token. Set by ensure_access() after a valid code is
# verified. Source-listing and playback require it, so simply deleting the
# passcode prompt cannot unlock the addon (playback stays blocked).
_ACCESS = True


# ---------------------------------------------------------------------------
# URL building / params
# ---------------------------------------------------------------------------
def build_url(params):
    base = "plugin://%s/" % ADDON_ID
    if not params:
        return base
    return base + "?" + urllib.parse.urlencode(params)


def get_params():
    if len(sys.argv) > 2 and sys.argv[2]:
        return dict(urllib.parse.parse_qsl(sys.argv[2].lstrip("?")))
    return {}


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def add_dir(handle, label, params, thumb="", is_folder=True, info=None):
    if _KODI:
        li = xbmcgui.ListItem(label)
        if thumb:
            li.setArt({"thumb": thumb, "icon": thumb})
        if info:
            li.setInfo("video", info)
        xbmcplugin.addDirectoryItem(handle, build_url(params), li, is_folder)
    else:
        print("DIR:", label, params)


def make_playable(label, path, thumb="", info=None, properties=None):
    if _KODI:
        li = xbmcgui.ListItem(label)
        li.setProperty("IsPlayable", "true")
        if thumb:
            li.setArt({"thumb": thumb, "icon": thumb})
        if info:
            li.setInfo("video", info)
        for k, v in (properties or {}).items():
            li.setProperty(k, v)
        return li
    return None


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------
def list_root(handle):
    xbmcplugin.setContent(handle, "videos")
    add_dir(handle, "[COLOR gold]🔍 Search All Sites[/COLOR]", {"mode": "searchall"})
    add_dir(handle, "⏯ Resume Movie", {"mode": "resume"})
    sites = get_enabled_sites()
    if len(sites) == 1:
        sid = sites[0].id
        add_dir(handle, "🆕 Latest", {"mode": "latest", "site": sid})
        add_dir(handle, "⭐ Featured", {"mode": "featured", "site": sid})
    for site in sites:
        add_dir(handle, site.name, {"mode": "site", "site": site.id},
                info={"plot": "Browse %s" % site.name})
    add_dir(handle, "[COLOR cyan]⬇ Downloads[/COLOR]", {"mode": "downloads"})
    add_dir(handle, "[COLOR lime]📚 Library Integration[/COLOR]", {"mode": "library_menu"})
    add_dir(handle, "[COLOR gray]⚙ Settings[/COLOR]", {"mode": "settings"})
    add_dir(handle, "[COLOR red]🔄 Clear Cache[/COLOR]", {"mode": "clear_cache"})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def list_site_menu(handle, site_id):
    site = get_site(site_id)
    if not site:
        return
    xbmcplugin.setContent(handle, "videos")
    add_dir(handle, "[COLOR gold]🔍 Search %s[/COLOR]" % site.name,
            {"mode": "search", "site": site_id})
    add_dir(handle, "🆕 Latest", {"mode": "latest", "site": site_id})
    add_dir(handle, "⭐ Featured", {"mode": "featured", "site": site_id})
    add_dir(handle, "🎭 Genres / Categories", {"mode": "genres", "site": site_id})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def list_genres(handle, site_id):
    site = get_site(site_id)
    if not site:
        return
    xbmcplugin.setContent(handle, "videos")
    for label, url in site.genres():
        add_dir(handle, label, {"mode": "browse", "site": site_id, "url": url})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def list_movies(handle, movies, site_id, end=True):
    xbmcplugin.setContent(handle, "movies")
    for m in movies:
        info = {"title": m["title"]}
        if m.get("year"):
            info["year"] = int(m["year"]) if str(m["year"]).isdigit() else None
        # Use site_id from movie if available (for search all results), otherwise use passed site_id
        movie_site_id = m.get("site_id", site_id)
        params = {"mode": "movie", "site": movie_site_id, "url": m["url"], "title": m.get("title", "")}
        if m.get("thumb"):
            params["thumb"] = m["thumb"]
        add_dir(handle, m["title"], params, thumb=m.get("thumb", ""), info=info)
    if _KODI and end:
        xbmcplugin.endOfDirectory(handle)


def do_search(handle, site_id=None, query=None, page=1):
    per_page = 50
    if not query:
        if _KODI:
            kb = xbmcgui.Dialog().input("Search", type=xbmcgui.INPUT_ALPHANUM)
            if not kb:
                return
            query = kb
        else:
            query = input("Search: ")
        page = 1

    sites = [get_site(site_id)] if site_id else get_enabled_sites()
    all_movies = []
    prog = Progress("Searching...")
    total = len(sites)
    for i, site in enumerate(sites):
        prog.update((i * 100) // total, "Searching %s" % site.name)
        try:
            res = site.search(query, page=page, per_page=per_page)
        except TypeError:
            res = site.search(query)
            start = max(page - 1, 0) * per_page
            res = res[start:start + per_page]
        except Exception as e:
            log("search %s failed: %s" % (site.name, e), "error")
            res = []
        # Add site_id to each movie result so we know which site to use for get_sources
        for movie in res:
            movie["site_id"] = site.id
        all_movies += res
        if prog.is_canceled():
            break
    prog.close()

    if not all_movies:
        notify("No results found")
        if _KODI:
            xbmcplugin.endOfDirectory(handle)
        return

    list_movies(handle, all_movies, site_id or "", end=False)
    if len(all_movies) >= per_page:
        next_params = {"query": query, "page": page + 1}
        if site_id:
            next_params.update({"mode": "search", "site": site_id})
        else:
            next_params.update({"mode": "searchall"})
        add_dir(handle, "[COLOR gold]>> Next Page (%d)[/COLOR]" % (page + 1), next_params)
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def do_featured(handle, site_id, page=1):
    site = get_site(site_id)
    if not site:
        return
    try:
        movies = site.browse(site.base_url, page)
    except Exception as e:
        log("featured failed: %s" % e, "error")
        movies = []
    if not movies:
        notify("No items found")
    list_movies(handle, movies, site_id, end=False)
    if movies:
        add_dir(handle, "[COLOR gold]>> Next Page (%d)[/COLOR]" % (page + 1),
                {"mode": "featured", "site": site_id, "page": page + 1})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def do_latest(handle, site_id, page=1):
    site = get_site(site_id)
    if not site:
        return
    try:
        movies = site.latest(page)
    except Exception as e:
        log("latest failed: %s" % e, "error")
        movies = []
    if not movies:
        notify("No items found")
    list_movies(handle, movies, site_id, end=False)
    if movies:
        add_dir(handle, "[COLOR gold]>> Next Page (%d)[/COLOR]" % (page + 1),
                {"mode": "latest", "site": site_id, "page": page + 1})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def do_browse(handle, site_id, url, page=1):
    site = get_site(site_id)
    if not site:
        return
    try:
        movies = site.browse(url, page)
    except Exception as e:
        log("browse failed: %s" % e, "error")
        movies = []
    if not movies:
        notify("No items found")
    list_movies(handle, movies, site_id, end=False)
    if movies:
        add_dir(handle, "[COLOR gold]>> Next Page (%d)[/COLOR]" % (page + 1),
                {"mode": "browse", "site": site_id, "url": url, "page": page + 1})
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def _format_clock(seconds):
    try:
        seconds = int(float(seconds or 0))
    except Exception:
        seconds = 0
    if seconds < 0:
        seconds = 0
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return "%d:%02d:%02d" % (h, m, s)
    return "%02d:%02d" % (m, s)


def _safe_filename(name):
    import re
    name = (name or "").strip()
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or "video"


def do_download(handle, embed_url, referer="", title="", quality=""):
    if not _KODI:
        return
    if not _ACCESS:
        notify("Access required. Enter your 4-digit code.", "MovieHub")
        xbmcplugin.endOfDirectory(handle)
        return
    if not embed_url:
        notify("Invalid source", "MovieHub")
        xbmcplugin.endOfDirectory(handle)
        return

    preferred = get_setting("prefer_quality", "Auto")
    try:
        result = resolve(embed_url, preferred=preferred, referer=referer)
    except Exception as e:
        log("download resolve error: %s" % e, "error")
        result = {"url": embed_url, "resolved": False, "kind": "unresolved", "referer": referer}

    if not result.get("resolved"):
        notify("This source could not be resolved for download.", "MovieHub", duration=3000)
        xbmcplugin.endOfDirectory(handle)
        return

    url = result.get("url", "")
    kind = result.get("kind", "")
    ref = result.get("referer", "") or referer

    # Allow HLS downloads - they will be converted to MP4
    # kind can be "m3u8" or "mp4" - both are now supported

    base = DownloadManager.get_download_path() if "DownloadManager" in globals() else get_manager().get_download_path()
    display_title = (title or "MovieHub Video").strip()
    if quality:
        display_title = ("%s - %s" % (display_title, quality)).strip()
    fname = _safe_filename(display_title) + ".mp4"
    dest = os.path.join(base, fname)

    try:
        dm = get_manager()
        dm.add_job(url, display_title, dest, referer=ref, quality=quality, kind=kind)
        notify("Download started: %s" % display_title, "MovieHub", duration=3000)
    except Exception as e:
        log("download start failed: %s" % e, "error")
        notify("Failed to start download", "MovieHub", duration=3000)

    xbmcplugin.endOfDirectory(handle)


def list_resume(handle):
    if not _KODI:
        return
    try:
        import resume_store
    except Exception:
        notify("Resume is unavailable", "MovieHub")
        xbmcplugin.endOfDirectory(handle)
        return

    xbmcplugin.setContent(handle, "videos")
    items = resume_store.get_resume_items(limit=100, min_seconds=30)
    if not items:
        notify("No resume items", "MovieHub", duration=3000)
        xbmcplugin.endOfDirectory(handle)
        return

    for it in items:
        embed = it.get("embed") or ""
        if not embed:
            continue
        title = it.get("title") or "Resume"
        thumb = it.get("thumb") or ""
        pos = it.get("position") or 0
        label = "⏯ %s  [COLOR gray](%s)[/COLOR]" % (title, _format_clock(pos))
        params = {
            "mode": "resolve",
            "embed": embed,
            "referer": it.get("referer", ""),
            "title": title,
            "thumb": thumb,
            "resume": str(int(float(pos or 0))),
        }
        li = make_playable(label, build_url(params), thumb=thumb, info={"title": title})
        if li:
            try:
                li.addContextMenuItems(
                    [("Remove from Resume", "RunPlugin(%s)" % build_url({"mode": "resume_clear", "key": it.get("playable_url", embed)}))],
                    replaceItems=False,
                )
            except Exception:
                pass
            xbmcplugin.addDirectoryItem(handle, build_url(params), li, False)
    xbmcplugin.endOfDirectory(handle)


def do_resume_clear(handle, key):
    if not _KODI:
        return
    try:
        import resume_store
        resume_store.clear_item(key)
        notify("Removed from Resume", "MovieHub", duration=3000)
    except Exception:
        notify("Failed to remove item", "MovieHub", duration=3000)
    xbmcplugin.endOfDirectory(handle)


# ---------------------------------------------------------------------------
# Sources + playback
# ---------------------------------------------------------------------------
def list_sources(handle, site_id, movie_url, title="", thumb=""):
    site = get_site(site_id)
    if not site:
        return
    if not _ACCESS:
        notify("Access required. Enter your 4-digit code.", "MovieHub")
        if _KODI:
            xbmcplugin.endOfDirectory(handle)
        return
    xbmcplugin.setContent(handle, "videos")
    try:
        sources = site.get_sources(movie_url)
    except Exception as e:
        log("get_sources failed: %s" % e, "error")
        sources = []
    if not sources:
        notify("No playable sources found for this title.\n"
               "The site uses a JavaScript-only player that cannot be\n"
               "resolved by a static scraper.", "MovieHub")
        if _KODI:
            xbmcplugin.endOfDirectory(handle)
        return
    # limit
    max_s = get_setting("max_sources", 20)
    try:
        max_s = int(max_s)
    except Exception:
        max_s = 20
    sources = sources[:max_s]
    for s in sources:
        label = "[COLOR cyan]▶ %s[/COLOR]" % s.get("label", s.get("host", "Source"))
        params = {"mode": "resolve", "embed": s["url"], "title": title or "", "thumb": thumb or ""}
        if s.get("referer"):
            params["referer"] = s["referer"]
        li = make_playable(label, build_url(params),
                           info={"title": s.get("label", "Source")})
        if _KODI:
            try:
                dl_params = {
                    "mode": "download",
                    "embed": s["url"],
                    "referer": s.get("referer", ""),
                    "title": title or "",
                    "quality": s.get("label", s.get("host", "")) or "",
                }
                li.addContextMenuItems([("Download", "RunPlugin(%s)" % build_url(dl_params))], replaceItems=False)
            except Exception:
                pass
            xbmcplugin.addDirectoryItem(handle, build_url(params), li, False)
    if _KODI:
        xbmcplugin.endOfDirectory(handle)


def _open_external(url):
    """Best-effort: open an unresolved embed in the device web browser so
    JS-only players can still play. Falls back to showing the URL."""
    if not _KODI:
        print("OPEN EXTERNAL BROWSER:", url)
        return
    # Android: open via a VIEW intent (system default browser)
    try:
        xbmc.executebuiltin('StartAndroidActivity("", "android.intent.action.VIEW", "%s")' % url)
        return
    except Exception:
        pass
    # Desktop: open with the OS default handler
    try:
        import subprocess, sys, os
        if sys.platform.startswith("win"):
            os.startfile(url)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])
        return
    except Exception:
        pass
    # Last resort: show the URL so the user can copy it
    try:
        xbmcgui.Dialog().textviewer("Open this URL in your browser", url)
    except Exception:
        pass


def play_resolved(handle, embed_url, referer="", title="", thumb="", resume=""):
    if not _ACCESS:
        notify("Access required. Enter your 4-digit code.", "MovieHub")
        if _KODI:
            xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
        return
    preferred = get_setting("prefer_quality", "Auto")
    try:
        result = resolve(embed_url, preferred=preferred, referer=referer)
    except Exception as e:
        log("resolve error: %s" % e, "error")
        result = {"url": embed_url, "resolved": False, "kind": "unresolved", "referer": referer}

    if not result.get("resolved"):
        notify("This source could not be resolved.\nOpening it in your browser instead.", "MovieHub")
        _open_external(result["url"])
        if _KODI:
            xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
        return

    url = result["url"]
    kind = result["kind"]
    referer = result.get("referer", "")
    extra = result.get("headers", {}) or {}
    log("Playing: %s (%s)" % (url, kind))

    if _KODI:
        li = xbmcgui.ListItem("", "", url)
        if kind == "m3u8":
            use_isa = get_setting("use_inputstream", True)
            li.setMimeType("application/vnd.apple.mpegurl")
            li.setContentLookup(False)
            if use_isa:
                li.setProperty("inputstream", "inputstream.adaptive")
                li.setProperty("inputstream.adaptive.manifest_type", "hls")
                hdr = "Referer: %s\r\nUser-Agent: %s" % (referer, get_setting("user_agent", ""))
                for k, v in extra.items():
                    if k.lower() == "referer":
                        continue
                    hdr += "\r\n%s: %s" % (k, v)
                hdr += "\r\nAccept: */*"
                li.setProperty("inputstream.adaptive.manifest_headers", hdr)
                li.setProperty("inputstream.adaptive.stream_headers", hdr)
            elif referer:
                li.setProperty("Referer", referer)
        elif kind == "mp4":
            li.setMimeType("video/mp4")
            if referer:
                li.setProperty("Referer", referer)
        elif kind == "youtube":
            # delegate to YouTube addon
            xbmcplugin.setResolvedUrl(handle, True, li)
            return
        xbmcplugin.setResolvedUrl(handle, True, li)
        try:
            import resume_store
            meta = {"embed": embed_url}
            if title:
                meta["title"] = title
            if thumb:
                meta["thumb"] = thumb
            if referer:
                meta["referer"] = referer
            resume_store.register_playable(embed_url, meta)
            try:
                resume_pos = float(resume or 0.0)
            except Exception:
                resume_pos = 0.0

            player = xbmc.Player()
            monitor = xbmc.Monitor()
            started = time.time()
            seeked = False
            while not monitor.abortRequested():
                if player.isPlayingVideo():
                    if resume_pos > 0 and not seeked:
                        try:
                            cur = float(player.getTime() or 0.0)
                        except Exception:
                            cur = 0.0
                        if cur < max(5.0, resume_pos - 5.0):
                            try:
                                player.seekTime(resume_pos)
                            except Exception:
                                pass
                        seeked = True
                    try:
                        pos = float(player.getTime() or 0.0)
                    except Exception:
                        pos = 0.0
                    try:
                        tot = float(player.getTotalTime() or 0.0)
                    except Exception:
                        tot = 0.0
                    resume_store.update_position(embed_url, pos, tot)
                    if tot > 0 and pos >= max(0.0, tot - 60.0):
                        resume_store.clear_item(embed_url)
                    if monitor.waitForAbort(5):
                        break
                else:
                    if seeked:
                        break
                    if (time.time() - started) > 10:
                        break
                    if monitor.waitForAbort(0.5):
                        break
        except Exception as e:
            log("resume tracking error: %s" % e, "debug")


# ---------------------------------------------------------------------------
# Subscription passcode (Firebase-backed, device-locked)
# ---------------------------------------------------------------------------
def get_device_mac():
    """Deprecated: mobile Kodi reports a hopping MAC. Use get_device_id()."""
    return get_device_id()


def _fb_get(code, fb):
    url = "%s/passcodes/%s.json" % (fb.rstrip("/"), code)
    data, _, _ = Net().get(url, headers={"Accept": "application/json"})
    if not data or data.strip() in ("", "null"):
        return None
    return json.loads(data)


def _fb_patch(code, fb, payload):
    url = "%s/passcodes/%s.json" % (fb.rstrip("/"), code)
    net = Net()
    net.request(url, method="PATCH", data=json.dumps(payload),
                headers={"Content-Type": "application/json"})


def validate_passcode(code, device, fb):
    """Validate (and on first use register) a 4-digit passcode.

    Returns one of: "ok", "invalid", "used_elsewhere", "paused", "expired",
    "rules_denied", "neterr".
    A code is locked to the first device id that activates it, so the same
    code cannot be used on a second device.
    """
    if not code or not fb:
        return "invalid"
    try:
        obj = _fb_get(code, fb)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            log("firebase read denied (rules not applied): %s" % e, "error")
            return "rules_denied"
        log("passcode check HTTP error: %s" % e, "error")
        return "neterr"
    except Exception as e:
        log("passcode check error: %s" % e, "error")
        return "neterr"
    if not isinstance(obj, dict) or obj.get("active", True) is False:
        return "invalid"
    if obj.get("paused"):
        return "paused"
    exp = obj.get("expiry")
    if exp and isinstance(exp, (int, float)) and int(time.time() * 1000) > int(exp):
        return "expired"
    registered = obj.get("device") or obj.get("mac")
    if registered and registered != device:
        return "used_elsewhere"
    if not registered:
        # first activation on this device -> lock the code to this device id
        try:
            _fb_patch(code, fb, {"device": device, "activated": int(time.time())})
        except Exception as e:
            log("passcode register error: %s" % e, "error")
            return "invalid"
    return "ok"


def ensure_access():
    """Access always granted - no passcode required."""
    global _ACCESS
    _ACCESS = True
    return True


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
def run():
    if not ensure_access():
        return
    try:
        params = get_params()
        mode = params.get("mode", "root")
        handle = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 0

        if mode == "root":
            list_root(handle)
        elif mode == "site":
            list_site_menu(handle, params.get("site", ""))
        elif mode == "genres":
            list_genres(handle, params.get("site", ""))
        elif mode == "search":
            do_search(handle, params.get("site"), params.get("query"), int(params.get("page", 1) or 1))
        elif mode == "searchall":
            do_search(handle, None, params.get("query"), int(params.get("page", 1) or 1))
        elif mode == "latest":
            do_latest(handle, params.get("site", ""), int(params.get("page", 1) or 1))
        elif mode == "featured":
            do_featured(handle, params.get("site", ""), int(params.get("page", 1) or 1))
        elif mode == "browse":
            do_browse(handle, params.get("site", ""), params.get("url", ""), int(params.get("page", 1) or 1))
        elif mode == "movie":
            list_sources(handle, params.get("site", ""), params.get("url", ""), params.get("title", ""), params.get("thumb", ""))
        elif mode == "resolve":
            play_resolved(handle, params.get("embed", ""), params.get("referer", ""), params.get("title", ""), params.get("thumb", ""), params.get("resume", ""))
        elif mode == "download":
            do_download(handle, params.get("embed", ""), params.get("referer", ""), params.get("title", ""), params.get("quality", ""))
        elif mode == "resume":
            list_resume(handle)
        elif mode == "resume_clear":
            do_resume_clear(handle, params.get("key", ""))
        elif mode == "settings":
            if _KODI:
                xbmcaddon.Addon().openSettings()
        elif mode == "downloads":
            if _KODI:
                dm = get_manager()
                dm.show_downloads_dialog()
        elif mode == "library_menu":
            if _KODI:
                show_library_dialog()
        elif mode == "library_update_latest":
            if _KODI:
                notify("Updating Latest library...", "MovieHub")
                site = get_site("movies")
                if site:
                    try:
                        movies = site.latest(1)
                        if movies:
                            n = update_latest(movies, "movies")
                            notify("Added %d items to Latest library" % n, "MovieHub")
                            scan_library_into_kodi()
                    except Exception as e:
                        log("library_update_latest error: %s" % e, "error")
                        notify("Library update failed", "MovieHub")
        elif mode == "library_update_categories":
            if _KODI:
                notify("Updating all categories...", "MovieHub")
                site = get_site("movies")
                if site:
                    try:
                        cats = site.genres()
                        n = update_all_categories(site, cats)
                        notify("Updated %d category folders" % n, "MovieHub")
                        scan_library_into_kodi()
                    except Exception as e:
                        log("library_update_categories error: %s" % e, "error")
                        notify("Category update failed", "MovieHub")
        elif mode == "clear_cache":
            if _KODI:
                if yesno("Clear Cache", "Clear all cached data?"):
                    cache_clear()
                    notify("Cache cleared", "MovieHub")
        else:
            list_root(handle)
    except Exception as e:
        log("run() crashed: %s" % e, "error")
        notify("MovieHub error: %s" % e, "MovieHub")


if __name__ == "__main__":
    run()
