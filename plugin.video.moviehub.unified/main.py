# -*- coding: utf-8 -*-
"""
MovieHub Unified - All-in-one Entertainment Addon for Kodi 19+

4 Separate Movie Sources:
1. HDMovie2 (hdmovie2a.icu) - iPad mini optimized
2. MovieHub (hdmovie2a.bar) - Original MovieHub site
3. StreamIMDB (streamimdb.ru) - Movies & TV Shows
4. FreeTV Studio (freetv.studio) - Live TV Channels

Plus: Universal Search, Favorites, IPTV Auto-Merge
"""

import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "lib"))

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

ADDON_ID = "plugin.video.moviehub.unified"

_addon = xbmcaddon.Addon()
_handle = int(sys.argv[1]) if len(sys.argv) > 1 else 0
_url = sys.argv[0]


def get_setting(key, default=""):
    try:
        val = _addon.getSetting(key)
        if val == "" and default is not None:
            return default
        if isinstance(default, bool):
            return val.lower() == "true"
        return val
    except Exception:
        return default


def build_url(params):
    base = "plugin://%s/" % ADDON_ID
    if not params:
        return base
    return base + "?" + urllib.parse.urlencode(params)


def add_dir(label, params, thumb="", is_folder=True, info=None):
    li = xbmcgui.ListItem(label)
    if thumb:
        li.setArt({"thumb": thumb, "icon": thumb})
    if info:
        li.setInfo("video", info)
    if not is_folder:
        li.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(_handle, build_url(params), li, is_folder)


def end_dir(content=None):
    if content:
        xbmcplugin.setContent(_handle, content)
    xbmcplugin.endOfDirectory(_handle)


def notify(msg, error=False):
    try:
        xbmcgui.Dialog().notification(
            "MovieHub Unified",
            str(msg),
            xbmcgui.NOTIFICATION_ERROR if error else xbmcgui.NOTIFICATION_INFO,
            5000,
        )
    except Exception:
        pass


def get_params():
    if len(sys.argv) > 2 and sys.argv[2]:
        return dict(urllib.parse.parse_qsl(sys.argv[2].lstrip("?")))
    return []


# ===================== ROOT MENU =====================

def root():
    """Root menu with 4 addon sources"""
    add_dir("🎬 [B]HDMovie2[/B] (hdmovie2a.icu)", {"mode": "hdm2_index"})
    add_dir("🎬 [B]MovieHub[/B] (hdmovie2a.bar)", {"mode": "mh_index"})
    add_dir("🎬 [B]StreamIMDB[/B] (streamimdb.ru)", {"mode": "si_index"})
    add_dir("📡 [B]FreeTV Studio[/B] (freetv.studio)", {"mode": "ftv_index"})
    add_dir("[COLOR gold]🔍 Universal Search[/COLOR]", {"mode": "universal_search"})
    add_dir("⭐ My Favorites", {"mode": "favorites"})
    add_dir("📋 Simple IPTV Player", {"mode": "iptv_player"})
    add_dir("[COLOR gray]⚙ Settings[/COLOR]", {"mode": "settings"})
    end_dir("videos")


# ===================== SOURCE 1: HDMOVIE2 (hdmovie2a.icu) =====================

def hdm2_index():
    """HDMovie2 main menu"""
    add_dir("[COLOR gold]🔍 Search[/COLOR]", {"mode": "hdm2_search"})
    add_dir("🆕 Latest Movies", {"mode": "hdm2_latest", "page": "1"})
    add_dir("🎭 Genres", {"mode": "hdm2_genres"})
    add_dir("📅 Years", {"mode": "hdm2_years"})
    end_dir("videos")


def hdm2_latest():
    params = get_params()
    page = int(params.get("page", "1"))
    source = params.get("genre", "")

    from resources.lib import hdm2_scraper
    if source:
        movies = hdm2_scraper.get_genre(source, page)
    else:
        movies = hdm2_scraper.get_latest(page)

    if not movies:
        add_dir("[COLOR gray]No movies found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]HDMovie2 - Page {page} ({len(movies)} movies)[/COLOR]", {"mode": "root"})

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        if m.get("year"):
            info["year"] = int(m["year"]) if m["year"].isdigit() else None
        add_dir(
            m.get("title", ""),
            {"mode": "hdm2_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "hdm2_latest", "page": str(page + 1), "genre": source})
    end_dir("videos")


def hdm2_genres():
    from resources.lib import hdm2_scraper
    genres = hdm2_scraper.get_genres()
    for label, slug in genres:
        add_dir(label, {"mode": "hdm2_latest", "genre": slug, "page": "1"})
    end_dir("videos")


def hdm2_years():
    for year in range(2026, 2009, -1):
        add_dir(str(year), {"mode": "hdm2_browse_year", "year": str(year), "page": "1"})
    end_dir("videos")


def hdm2_browse_year():
    params = get_params()
    year = params.get("year", "")
    page = int(params.get("page", "1"))

    from resources.lib import hdm2_scraper
    movies = hdm2_scraper.get_latest(page)  # Fallback

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "hdm2_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "hdm2_browse_year", "year": year, "page": str(page + 1)})
    end_dir("videos")


def hdm2_search():
    kb = xbmcgui.Dialog().input("Search HDMovie2", type=xbmcgui.INPUT_ALPHANUM)
    if not kb:
        return
    xbmc.executebuiltin("Container.Update(%s)" % build_url({"mode": "hdm2_search_results", "query": kb, "page": "1"}))


def hdm2_search_results():
    params = get_params()
    query = params.get("query", "")
    page = int(params.get("page", "1"))

    from resources.lib import hdm2_scraper
    movies = hdm2_scraper.search(query, page)

    if not movies:
        add_dir("[COLOR gray]No results found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]HDMovie2 Search: '{query}' ({len(movies)} results)[/COLOR]", {"mode": "root"})

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "hdm2_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "hdm2_search_results", "query": query, "page": str(page + 1)})
    end_dir("videos")


def hdm2_detail():
    params = get_params()
    url = params.get("url", "")
    title = params.get("title", "")
    thumb = params.get("thumb", "")

    if not url:
        return

    from resources.lib import hdm2_scraper
    detail = hdm2_scraper.get_detail(url)

    if not detail:
        notify("Could not load movie details", error=True)
        return

    info = {"title": detail.get("title", title), "mediatype": "video"}
    if detail.get("plot"):
        info["plot"] = detail["plot"]

    poster = detail.get("poster", thumb)
    sources = detail.get("sources", [])

    if not sources:
        notify("No video sources found", error=True)
        return

    for s in sources:
        label = s.get("label", "Source")
        add_dir(label, {"mode": "play", "url": s.get("url", ""), "title": detail.get("title", title), "thumb": poster}, poster, False, info)
    end_dir("videos")


# ===================== SOURCE 2: MOVIEHUB (hdmovie2a.bar) =====================

def mh_index():
    """MovieHub main menu"""
    add_dir("[COLOR gold]🔍 Search[/COLOR]", {"mode": "mh_search"})
    add_dir("🆕 Latest Movies", {"mode": "mh_latest", "page": "1"})
    add_dir("🎭 Genres", {"mode": "mh_genres"})
    add_dir("📅 Years", {"mode": "mh_years"})
    end_dir("videos")


def mh_latest():
    params = get_params()
    page = int(params.get("page", "1"))
    genre = params.get("genre", "")

    from resources.lib import moviehub_scraper
    if genre:
        movies = moviehub_scraper.get_genre(genre, page)
    else:
        movies = moviehub_scraper.get_latest(page)

    if not movies:
        add_dir("[COLOR gray]No movies found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]MovieHub - Page {page} ({len(movies)} movies)[/COLOR]", {"mode": "root"})

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        if m.get("year"):
            info["year"] = int(m["year"]) if m["year"].isdigit() else None
        add_dir(
            m.get("title", ""),
            {"mode": "mh_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "mh_latest", "page": str(page + 1), "genre": genre})
    end_dir("videos")


def mh_genres():
    from resources.lib import moviehub_scraper
    genres = moviehub_scraper.get_genres()
    for label, slug in genres:
        add_dir(label, {"mode": "mh_latest", "genre": slug, "page": "1"})
    end_dir("videos")


def mh_years():
    for year in range(2026, 2009, -1):
        add_dir(str(year), {"mode": "mh_browse_year", "year": str(year), "page": "1"})
    end_dir("videos")


def mh_browse_year():
    params = get_params()
    year = params.get("year", "")
    page = int(params.get("page", "1"))

    from resources.lib import moviehub_scraper
    movies = moviehub_scraper.get_latest(page)

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "mh_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "mh_browse_year", "year": year, "page": str(page + 1)})
    end_dir("videos")


def mh_search():
    kb = xbmcgui.Dialog().input("Search MovieHub", type=xbmcgui.INPUT_ALPHANUM)
    if not kb:
        return
    xbmc.executebuiltin("Container.Update(%s)" % build_url({"mode": "mh_search_results", "query": kb, "page": "1"}))


def mh_search_results():
    params = get_params()
    query = params.get("query", "")
    page = int(params.get("page", "1"))

    from resources.lib import moviehub_scraper
    movies = moviehub_scraper.search(query, page)

    if not movies:
        add_dir("[COLOR gray]No results found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]MovieHub Search: '{query}' ({len(movies)} results)[/COLOR]", {"mode": "root"})

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "mh_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "mh_search_results", "query": query, "page": str(page + 1)})
    end_dir("videos")


def mh_detail():
    params = get_params()
    url = params.get("url", "")
    title = params.get("title", "")
    thumb = params.get("thumb", "")

    if not url:
        return

    from resources.lib import moviehub_scraper
    detail = moviehub_scraper.get_detail(url)

    if not detail:
        notify("Could not load movie details", error=True)
        return

    info = {"title": detail.get("title", title), "mediatype": "video"}
    if detail.get("plot"):
        info["plot"] = detail["plot"]

    poster = detail.get("poster", thumb)
    sources = detail.get("sources", [])

    if not sources:
        notify("No video sources found", error=True)
        return

    for s in sources:
        label = s.get("label", "Source")
        add_dir(label, {"mode": "play", "url": s.get("url", ""), "title": detail.get("title", title), "thumb": poster}, poster, False, info)
    end_dir("videos")


# ===================== SOURCE 3: STREAMIMDB (streamimdb.ru) =====================

def si_index():
    """StreamIMDB main menu"""
    add_dir("[COLOR gold]🔍 Search[/COLOR]", {"mode": "si_search"})
    add_dir("🆕 Latest Movies", {"mode": "si_movies_latest", "page": "1"})
    add_dir("📺 TV Shows", {"mode": "si_tv_latest", "page": "1"})
    add_dir("🎭 Movies by Genre", {"mode": "si_movie_genres"})
    end_dir("videos")


def si_movies_latest():
    params = get_params()
    page = int(params.get("page", "1"))

    from resources.lib import streamimdb_scraper
    movies = streamimdb_scraper.get_latest(page)

    if not movies:
        add_dir("[COLOR gray]No movies found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]StreamIMDB Movies - Page {page} ({len(movies)} movies)[/COLOR]", {"mode": "root"})

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "si_movie_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "si_movies_latest", "page": str(page + 1)})
    end_dir("videos")


def si_tv_latest():
    params = get_params()
    page = int(params.get("page", "1"))

    from resources.lib import streamimdb_scraper
    shows = streamimdb_scraper.get_tv_shows(page)

    if not shows:
        add_dir("[COLOR gray]No TV shows found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]StreamIMDB TV Shows - Page {page} ({len(shows)} shows)[/COLOR]", {"mode": "root"})

    for s in shows:
        info = {"title": s.get("title", ""), "mediatype": "tvshow"}
        add_dir(
            s.get("title", ""),
            {"mode": "si_tv_detail", "url": s.get("url", ""), "title": s.get("title", ""), "thumb": s.get("thumb", "")},
            s.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "si_tv_latest", "page": str(page + 1)})
    end_dir("tvshows")


def si_movie_genres():
    genres = [
        ("Action", "action"),
        ("Adventure", "adventure"),
        ("Animation", "animation"),
        ("Comedy", "comedy"),
        ("Crime", "crime"),
        ("Documentary", "documentary"),
        ("Drama", "drama"),
        ("Fantasy", "fantasy"),
        ("Horror", "horror"),
        ("Mystery", "mystery"),
        ("Romance", "romance"),
        ("Sci-Fi", "sci-fi"),
        ("Thriller", "thriller"),
    ]
    for label, slug in genres:
        add_dir(label, {"mode": "si_movies_by_genre", "genre": slug, "page": "1"})
    end_dir("videos")


def si_movies_by_genre():
    params = get_params()
    genre = params.get("genre", "")
    page = int(params.get("page", "1"))

    from resources.lib import streamimdb_scraper
    movies = streamimdb_scraper.get_movie_by_genre(genre, page)

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "si_movie_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "si_movies_by_genre", "genre": genre, "page": str(page + 1)})
    end_dir("videos")


def si_search():
    kb = xbmcgui.Dialog().input("Search StreamIMDB", type=xbmcgui.INPUT_ALPHANUM)
    if not kb:
        return
    xbmc.executebuiltin("Container.Update(%s)" % build_url({"mode": "si_search_results", "query": kb, "page": "1"}))


def si_search_results():
    params = get_params()
    query = params.get("query", "")
    page = int(params.get("page", "1"))

    from resources.lib import streamimdb_scraper
    results = streamimdb_scraper.search(query, page)

    if not results:
        add_dir("[COLOR gray]No results found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]StreamIMDB Search: '{query}' ({len(results)} results)[/COLOR]", {"mode": "root"})

    for m in results:
        kind = m.get("kind", "movie")
        mode = "si_tv_detail" if kind == "tv" else "si_movie_detail"
        info = {"title": m.get("title", ""), "mediatype": "tvshow" if kind == "tv" else "video"}
        add_dir(
            m.get("title", ""),
            {"mode": mode, "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "si_search_results", "query": query, "page": str(page + 1)})
    end_dir("videos")


def si_movie_detail():
    params = get_params()
    url = params.get("url", "")
    title = params.get("title", "")
    thumb = params.get("thumb", "")

    if not url:
        return

    from resources.lib import streamimdb_scraper
    detail = streamimdb_scraper.get_detail(url)

    if not detail:
        notify("Could not load movie details", error=True)
        return

    info = {"title": detail.get("title", title), "mediatype": "video"}
    if detail.get("plot"):
        info["plot"] = detail["plot"]

    poster = detail.get("poster", thumb)
    sources = detail.get("sources", [])

    if not sources:
        notify("No video sources found", error=True)
        return

    for s in sources:
        label = s.get("label", "Source")
        add_dir(label, {"mode": "play", "url": s.get("url", ""), "title": detail.get("title", title), "thumb": poster}, poster, False, info)
    end_dir("videos")


def si_tv_detail():
    params = get_params()
    url = params.get("url", "")
    title = params.get("title", "")
    thumb = params.get("thumb", "")

    if not url:
        return

    from resources.lib import streamimdb_scraper
    detail = streamimdb_scraper.get_tv_detail(url)

    if not detail:
        notify("Could not load series details", error=True)
        return

    seasons = detail.get("seasons", {})
    if not seasons:
        notify("No seasons found", error=True)
        return

    for season_num in sorted(seasons.keys()):
        label = f"Season {season_num}"
        add_dir(
            label,
            {"mode": "si_season", "url": url, "season": str(season_num), "title": detail.get("title", title)},
            thumb,
            True,
        )
    end_dir("tvshows")


def si_season():
    params = get_params()
    url = params.get("url", "")
    season = params.get("season", "1")
    title = params.get("title", "")

    if not url:
        return

    from resources.lib import streamimdb_scraper
    episodes = streamimdb_scraper.get_episodes(url, season)

    if not episodes:
        notify("No episodes found", error=True)
        return

    for ep in episodes:
        ep_title = ep.get("title", f"Episode {ep.get('episode', '')}")
        label = f"S{season}E{ep.get('episode', '')} - {ep_title}"
        info = {"title": label, "mediatype": "episode", "season": int(season), "episode": ep.get("episode", 0)}
        add_dir(
            label,
            {"mode": "play", "url": ep.get("url", ""), "title": label, "thumb": ep.get("thumb", "")},
            ep.get("thumb", ""),
            False,
            info,
        )
    end_dir("episodes")


# ===================== SOURCE 4: FREETV STUDIO (freetv.studio) =====================

def ftv_index():
    """FreeTV Studio main menu"""
    add_dir("🌍 All Channels", {"mode": "ftv_channels", "category": "all", "page": "1"})
    add_dir("📺 By Country", {"mode": "ftv_countries"})
    add_dir("📂 By Category", {"mode": "ftv_categories"})
    add_dir("📻 Radio", {"mode": "ftv_radio", "page": "1"})
    add_dir("🔄 Auto-Merge TV List (IPTV)", {"mode": "ftv_auto_merge"})
    end_dir("videos")


def ftv_countries():
    from resources.lib import tv_scraper
    countries = tv_scraper.get_countries()
    for c in countries:
        add_dir(c.get("name", c.get("code", "")), {"mode": "ftv_channels", "category": c.get("code", "").lower(), "page": "1"})
    end_dir("videos")


def ftv_categories():
    from resources.lib import tv_scraper
    categories = tv_scraper.get_categories()
    for c in categories:
        add_dir(c.get("name", c.get("slug", "")), {"mode": "ftv_channels", "category": c.get("slug", ""), "page": "1"})
    end_dir("videos")


def ftv_channels():
    params = get_params()
    category = params.get("category", "all")
    page = int(params.get("page", "1"))

    from resources.lib import tv_scraper

    if category == "all":
        channels = tv_scraper.get_all_channels(page)
    else:
        # Try as country code first, then as category
        channels = tv_scraper.get_channels_by_country(category.upper())
        if not channels:
            channels = tv_scraper.get_channels_by_category(category)

    if not channels:
        add_dir("[COLOR gray]No channels found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]FreeTV Studio - {category.upper()} ({len(channels)} channels)[/COLOR]", {"mode": "root"})

    for ch in channels:
        info = {"title": ch.get("name", ""), "mediatype": "video"}
        add_dir(
            ch.get("name", ""),
            {"mode": "play", "url": ch.get("url", ""), "title": ch.get("name", ""), "thumb": ch.get("logo", "")},
            ch.get("logo", ""),
            False,
            info,
        )

    if len(channels) >= 50:
        add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "ftv_channels", "category": category, "page": str(page + 1)})

    end_dir("videos")


def ftv_radio():
    params = get_params()
    page = int(params.get("page", "1"))

    from resources.lib import tv_scraper
    stations = tv_scraper.get_radio()

    if not stations:
        add_dir("[COLOR gray]No radio stations found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]FreeTV Studio Radio ({len(stations)} stations)[/COLOR]", {"mode": "root"})

    for st in stations:
        info = {"title": st.get("name", ""), "mediatype": "music"}
        add_dir(
            st.get("name", ""),
            {"mode": "play", "url": st.get("url", ""), "title": st.get("name", ""), "thumb": st.get("logo", "")},
            st.get("logo", ""),
            False,
            info,
        )
    end_dir("videos")


def ftv_auto_merge():
    """Auto-merge TV list from multiple IPTV sources"""
    from resources.lib import tv_scraper
    xbmcgui.Dialog().notification("MovieHub", "Merging TV lists...", xbmcgui.NOTIFICATION_INFO, 3000)

    merged = tv_scraper.auto_merge_playlist()

    if not merged:
        notify("Could not merge TV list", error=True)
        return

    add_dir(f"[COLOR yellow]Auto-Merged TV List ({len(merged)} channels)[/COLOR]", {"mode": "root"})

    for ch in merged[:500]:  # Limit to 500 for performance
        info = {"title": ch.get("name", ""), "mediatype": "video"}
        add_dir(
            ch.get("name", ""),
            {"mode": "play", "url": ch.get("url", ""), "title": ch.get("name", ""), "thumb": ch.get("logo", "")},
            ch.get("logo", ""),
            False,
            info,
        )
    end_dir("videos")


# ===================== UNIVERSAL SEARCH =====================

def universal_search():
    kb = xbmcgui.Dialog().input("Universal Search (All Sources)", type=xbmcgui.INPUT_ALPHANUM)
    if not kb:
        return
    xbmc.executebuiltin("Container.Update(%s)" % build_url({"mode": "universal_search_results", "query": kb, "page": "1"}))


def universal_search_results():
    params = get_params()
    query = params.get("query", "")
    page = int(params.get("page", "1"))

    all_results = []

    # Search HDMovie2
    try:
        from resources.lib import hdm2_scraper
        for r in hdm2_scraper.search(query, page):
            r["title"] = "[HDMovie2] " + r.get("title", "")
            all_results.append(r)
    except Exception:
        pass

    # Search MovieHub
    try:
        from resources.lib import moviehub_scraper
        for r in moviehub_scraper.search(query, page):
            r["title"] = "[MovieHub] " + r.get("title", "")
            all_results.append(r)
    except Exception:
        pass

    # Search StreamIMDB
    try:
        from resources.lib import streamimdb_scraper
        for r in streamimdb_scraper.search(query, page):
            r["title"] = "[StreamIMDB] " + r.get("title", "")
            all_results.append(r)
    except Exception:
        pass

    if not all_results:
        add_dir("[COLOR gray]No results found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]Universal Search: '{query}' ({len(all_results)} results)[/COLOR]", {"mode": "root"})

    for m in all_results:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "play", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            False,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "universal_search_results", "query": query, "page": str(page + 1)})
    end_dir("videos")


# ===================== PLAYBACK =====================

def play():
    params = get_params()
    url = params.get("url", "")
    title = params.get("title", "")
    thumb = params.get("thumb", "")

    if not url:
        return

    from resources.lib import resolver
    resolved = resolver.resolve(url)

    if not resolved:
        notify("Could not resolve stream", error=True)
        xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())
        return

    li = xbmcgui.ListItem(path=resolved.get("url", url), label=title)
    li.setArt({"thumb": thumb, "icon": thumb})
    li.setInfo("video", {"title": title, "mediatype": "video"})
    li.setProperty("IsPlayable", "true")

    if resolved.get("headers"):
        for k, v in resolved.get("headers", {}).items():
            li.setProperty(k, v)

    xbmcplugin.setResolvedUrl(_handle, True, li)


# ===================== FAVORITES =====================

def favorites():
    fav_list = _get_favorites()
    if not fav_list:
        add_dir("[COLOR gray]No favorites yet[/COLOR]", {"mode": "root"})
        end_dir("videos")
        return

    for fav in fav_list:
        info = {"title": fav.get("name", ""), "mediatype": "video"}
        add_dir(
            fav.get("name", ""),
            {"mode": "play", "url": fav.get("url", ""), "title": fav.get("name", ""), "thumb": fav.get("logo", "")},
            fav.get("logo", ""),
            False,
            info,
        )
    end_dir("videos")


def _get_favorites():
    import json
    fav_path = os.path.join(xbmc.translatePath("special://profile/addon_data/" + ADDON_ID), "favorites.json")
    try:
        if os.path.exists(fav_path):
            with open(fav_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


# ===================== IPTV PLAYER =====================

def iptv_player():
    from resources.lib import tv_scraper

    m3u_url = get_setting("iptv_m3u_url", "")
    if m3u_url:
        channels = tv_scraper.parse_m3u(m3u_url)
    else:
        channels = tv_scraper.get_all_channels(1)

    if not channels:
        notify("No channels found", error=True)
        return

    for ch in channels[:200]:
        info = {"title": ch.get("name", ""), "mediatype": "video"}
        add_dir(
            ch.get("name", ""),
            {"mode": "play", "url": ch.get("url", ""), "title": ch.get("name", ""), "thumb": ch.get("logo", "")},
            ch.get("logo", ""),
            False,
            info,
        )
    end_dir("videos")


# ===================== ROUTER =====================

def run():
    params = get_params()
    mode = params.get("mode", "root")

    handlers = {
        "root": root,
        # HDMovie2
        "hdm2_index": hdm2_index,
        "hdm2_latest": hdm2_latest,
        "hdm2_genres": hdm2_genres,
        "hdm2_years": hdm2_years,
        "hdm2_browse_year": hdm2_browse_year,
        "hdm2_search": hdm2_search,
        "hdm2_search_results": hdm2_search_results,
        "hdm2_detail": hdm2_detail,
        # MovieHub
        "mh_index": mh_index,
        "mh_latest": mh_latest,
        "mh_genres": mh_genres,
        "mh_years": mh_years,
        "mh_browse_year": mh_browse_year,
        "mh_search": mh_search,
        "mh_search_results": mh_search_results,
        "mh_detail": mh_detail,
        # StreamIMDB
        "si_index": si_index,
        "si_movies_latest": si_movies_latest,
        "si_tv_latest": si_tv_latest,
        "si_movie_genres": si_movie_genres,
        "si_movies_by_genre": si_movies_by_genre,
        "si_search": si_search,
        "si_search_results": si_search_results,
        "si_movie_detail": si_movie_detail,
        "si_tv_detail": si_tv_detail,
        "si_season": si_season,
        # FreeTV Studio
        "ftv_index": ftv_index,
        "ftv_countries": ftv_countries,
        "ftv_categories": ftv_categories,
        "ftv_channels": ftv_channels,
        "ftv_radio": ftv_radio,
        "ftv_auto_merge": ftv_auto_merge,
        # Universal
        "universal_search": universal_search,
        "universal_search_results": universal_search_results,
        "favorites": favorites,
        "iptv_player": iptv_player,
        "play": play,
        "settings": lambda: _addon.openSettings(),
    }

    handler = handlers.get(mode, root)
    try:
        handler()
    except Exception as e:
        notify(f"Error: {e}", error=True)
        end_dir()


if __name__ == "__main__":
    run()
