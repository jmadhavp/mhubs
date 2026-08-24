# -*- coding: utf-8 -*-
"""
library.py - Kodi Library Integration for MovieHub addon.

Creates STRM files for movies/series so they appear in Kodi's video library.
Supports: Latest, Categories (Bollywood, Hollywood, etc.), Search results.
"""
import os
import re
import json
import time
import urllib.parse
from collections import OrderedDict

from common import log, notify, get_setting, set_setting, _KODI, xbmc, xbmcgui, xbmcaddon, xbmcplugin

ADDON_ID = "plugin.video.moviehub"

if _KODI:
    try:
        import xbmcvfs
    except ImportError:
        xbmcvfs = None


def _library_base_path():
    """Get the library root path from settings."""
    path = get_setting("library_path", "")
    if not path:
        if _KODI:
            try:
                from xbmc import translatePath
                path = translatePath("special://profile/addon_data/%s/library/" % ADDON_ID)
            except Exception:
                path = os.path.join(os.path.expanduser("~"), "KodiLibrary", "MovieHub")
        else:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "test_library")
    try:
        if xbmcvfs:
            if not xbmcvfs.exists(path):
                xbmcvfs.mkdirs(path)
        else:
            os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _strm_content(url, label, thumb="", info=None):
    """Generate content for a STRM file.
    
    STRM files contain the plugin URL that Kodi will call when the item is played.
    """
    params = {"mode": "resolve", "url": url}
    if thumb:
        params["thumb"] = thumb
    plugin_url = "plugin://%s/?%s" % (ADDON_ID, urllib.parse.urlencode(params))
    return plugin_url


def _clean_filename(title):
    """Clean a title for use as a filename."""
    title = re.sub(r'[<>:"/\\|?*]', '_', title)
    title = re.sub(r'\s+', ' ', title).strip()
    title = title[:200]  # Limit length
    return title


def _update_library_folder(site_id, section, items, library_type="movies"):
    """Update a library folder with STRM files for the given items.
    
    Args:
        site_id: Site identifier (e.g., 'movies')
        section: Section name (e.g., 'latest', 'bollywood', 'hollywood')
        items: List of movie dicts with 'title', 'url', 'thumb', 'year'
        library_type: Kodi library type ('movies' or 'tvshows')
    """
    base = _library_base_path()
    section_path = os.path.join(base, section)
    
    try:
        if xbmcvfs:
            if not xbmcvfs.exists(section_path):
                xbmcvfs.mkdirs(section_path)
        else:
            os.makedirs(section_path, exist_ok=True)
    except Exception as e:
        log("Failed to create library folder %s: %s" % (section_path, e), "error")
        return
    
    existing = set()
    if xbmcvfs:
        dirs, files = xbmcvfs.listdir(section_path)
        existing = set(files)
    else:
        try:
            existing = set(os.listdir(section_path))
        except Exception:
            pass
    
    added = 0
    for item in items:
        title = item.get("title", "")
        if not title:
            continue
        year = item.get("year", "")
        if year:
            fname = "%s (%s).strm" % (_clean_filename(title), year)
        else:
            fname = "%s.strm" % _clean_filename(title)
        
        if fname in existing:
            continue
        
        url = item.get("url", "")
        thumb = item.get("thumb", "")
        
        strm_url = _strm_content(url, title, thumb)
        filepath = os.path.join(section_path, fname)
        
        try:
            if xbmcvfs:
                f = xbmcvfs.File(filepath, "w")
                f.write(strm_url)
                f.close()
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(strm_url)
            added += 1
        except Exception as e:
            log("Failed to write STRM %s: %s" % (filepath, e), "error")
    
    log("Library update: %s/%s -> %d new items" % (section, library_type, added), "info")
    return added


def update_latest(movies, site_id="movies"):
    """Update the 'Latest' library section."""
    return _update_library_folder(site_id, "Latest", movies, "movies")


def update_category(cat_name, movies, site_id="movies"):
    """Update a category/library section."""
    safe_name = _clean_filename(cat_name)
    return _update_library_folder(site_id, safe_name, movies, "movies")


def update_all_categories(site, categories):
    """Update all category library folders."""
    total = 0
    for cat_name, cat_url in categories:
        try:
            items = site.browse(cat_url, 1)
            if items:
                c = update_category(cat_name, items)
                total += c
        except Exception as e:
            log("Failed to update category %s: %s" % (cat_name, e), "error")
    return total


def clean_library():
    """Remove empty STRM files and orphaned folders from the library."""
    base = _library_base_path()
    cleaned = 0
    try:
        if xbmcvfs:
            dirs, files = xbmcvfs.listdir(base)
            for d in dirs:
                sub_path = os.path.join(base, d)
                sub_dirs, sub_files = xbmcvfs.listdir(sub_path)
                # Remove empty folders
                if not sub_files and not sub_dirs:
                    xbmcvfs.rmdir(sub_path)
                    cleaned += 1
            # Remove 0-byte STRM files
            for f in files:
                if f.endswith(".strm"):
                    fpath = os.path.join(base, f)
                    stat = xbmcvfs.Stat(fpath)
                    if stat.size() == 0:
                        xbmcvfs.delete(fpath)
                        cleaned += 1
        else:
            for root, dirs, files in os.walk(base, topdown=False):
                for f in files:
                    if f.endswith(".strm"):
                        fpath = os.path.join(root, f)
                        if os.path.getsize(fpath) == 0:
                            os.remove(fpath)
                            cleaned += 1
                for d in dirs:
                    dpath = os.path.join(root, d)
                    try:
                        os.rmdir(dpath)
                        cleaned += 1
                    except OSError:
                        pass  # Directory not empty
    except Exception as e:
        log("clean library error: %s" % e, "debug")
    return cleaned


def scan_library_into_kodi():
    """Tell Kodi to scan the library path for new content."""
    if not _KODI:
        return
    try:
        path = _library_base_path()
        xbmc.executebuiltin('UpdateLibrary(video, "%s")' % path)
        log("Triggered Kodi library scan for: %s" % path, "info")
    except Exception as e:
        log("Failed to trigger Kodi library scan: %s" % e, "error")


def get_library_stats():
    """Get statistics about the current library."""
    base = _library_base_path()
    stats = {"folders": 0, "strm_files": 0, "total_size": 0}
    try:
        if xbmcvfs:
            dirs, files = xbmcvfs.listdir(base)
            stats["folders"] = len(dirs)
            for d in dirs:
                sub_path = os.path.join(base, d)
                sd, sf = xbmcvfs.listdir(sub_path)
                stats["strm_files"] += len([x for x in sf if x.endswith(".strm")])
        else:
            for root, dirs, files in os.walk(base):
                stats["folders"] += len(dirs)
                strm_files = [f for f in files if f.endswith(".strm")]
                stats["strm_files"] += len(strm_files)
                for f in files:
                    fpath = os.path.join(root, f)
                    try:
                        stats["total_size"] += os.path.getsize(fpath)
                    except Exception:
                        pass
    except Exception as e:
        log("get library stats error: %s" % e, "debug")
    return stats


def show_library_dialog():
    """Show a dialog with library management options."""
    if not _KODI:
        return
    
    options = [
        "🔄 Update Library (Latest)",
        "📂 Update All Categories",
        "🧹 Clean Library",
        "📊 Library Statistics",
        "⚙ Open Library Settings",
        "[B]Close[/B]",
    ]
    
    while True:
        selected = xbmcgui.Dialog().select("MovieHub - Library Integration", options)
        if selected < 0 or selected >= len(options):
            break
        
        if selected == 0:  # Update Latest
            notify("Library update started...", "MovieHub")
            # This will be called from main.py with actual data
            xbmc.executebuiltin('Container.Update("plugin://%s/?mode=library_update_latest")' % ADDON_ID)
            
        elif selected == 1:  # Update All Categories
            notify("Updating all categories...", "MovieHub")
            xbmc.executebuiltin('Container.Update("plugin://%s/?mode=library_update_categories")' % ADDON_ID)
            
        elif selected == 2:  # Clean Library
            c = clean_library()
            notify("Cleaned %d items from library" % c, "MovieHub")
            
        elif selected == 3:  # Statistics
            stats = get_library_stats()
            msg = "Folders: %d\nSTRM Files: %d\nTotal Size: %d bytes" % (
                stats["folders"], stats["strm_files"], stats["total_size"]
            )
            xbmcgui.Dialog().ok("MovieHub Library Stats", msg)
            
        elif selected == 4:  # Open Settings
            xbmcaddon.Addon(id=ADDON_ID).openSettings()
            
        elif selected == 5:  # Close
            break


def build_library_url(section, movie_url, title, thumb=""):
    """Build a plugin URL for a library item (used in STRM files)."""
    params = OrderedDict()
    params["mode"] = "library_play"
    params["section"] = section
    params["url"] = movie_url
    params["title"] = title
    if thumb:
        params["thumb"] = thumb
    return "plugin://%s/?%s" % (ADDON_ID, urllib.parse.urlencode(params))

