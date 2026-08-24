# -*- coding: utf-8 -*-
"""
MovieHub Unified - All-in-one Entertainment Addon for Kodi 19+

Combines Movies, TV Series, and Live TV channels into one addon.
Features auto-updating TV list via IPTV player.
"""

import os
import sys
import urllib.parse

# Make resources/lib importable
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
    return {}


# ===================== MOVIES SECTION =====================

def movies_index():
    """Movies main menu"""
    add_dir("[COLOR gold]🔍 Search Movies[/COLOR]", {"mode": "movies_search"})
    add_dir("🆕 Latest Movies", {"mode": "movies_latest", "source": "all", "page": "1"})
    add_dir("🎬 Movies (HDMovie2)", {"mode": "movies_latest", "source": "hdm2", "page": "1"})
    add_dir("🎭 Genres", {"mode": "movies_genres"})
    add_dir("📅 Years", {"mode": "movies_years"})
    end_dir("videos")


def movies_latest():
    """Show latest movies from selected source"""
    params = get_params()
    source = params.get("source", "all")
    page = int(params.get("page", "1"))

    if source == "hdm2":
        from resources.lib import hdm2_scraper
        movies = hdm2_scraper.get_latest(page)
    elif source == "streamimdb":
        from resources.lib import streamimdb_scraper
        movies = streamimdb_scraper.get_latest(page)
        if not movies:
            notify("StreamIMDB is currently unavailable")
    else:
        # Combine both sources - HDMovie2 is primary
        from resources.lib import hdm2_scraper
        from resources.lib import streamimdb_scraper
        movies = []
        movies.extend(hdm2_scraper.get_latest(page))
        try:
            si_movies = streamimdb_scraper.get_latest(page)
            if si_movies:
                for m in si_movies:
                    m["title"] = "[StreamIMDB] " + m.get("title", "")
                movies.extend(si_movies)
        except Exception:
            pass

    if not movies:
        add_dir("[COLOR gray]No movies found[/COLOR]", {"mode": "root"})
        end_dir("videos")
        return

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "movies_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "movies_latest", "source": source, "page": str(page + 1)})
    end_dir("videos")


def movies_genres():
    """Show movie genres"""
    genres = [
        ("Action", "action"),
        ("Adventure", "adventure"),
        ("Animation", "animation"),
        ("Bollywood", "bollywood"),
        ("Comedy", "comedy"),
        ("Crime", "crime"),
        ("Documentary", "documentary"),
        ("Drama", "drama"),
        ("Family", "family"),
        ("Fantasy", "fantasy"),
        ("Hindi Dubbed", "hindi-dubbed"),
        ("Hollywood", "hollywood"),
        ("Horror", "horror"),
        ("Musical", "musical"),
        ("Mystery", "mystery"),
        ("Romance", "romance"),
        ("Sci-Fi", "sci-fi"),
        ("South Hindi Dubbed", "south-hindi-dubbed"),
        ("Thriller", "thriller"),
        ("War", "war"),
        ("Web Series", "web-series"),
    ]
    for label, slug in genres:
        add_dir(label, {"mode": "movies_browse_genre", "genre": slug, "page": "1"})
    end_dir("videos")


def movies_browse_genre():
    """Browse movies by genre"""
    params = get_params()
    genre = params.get("genre", "")
    page = int(params.get("page", "1"))

    from resources.lib import hdm2_scraper
    movies = hdm2_scraper.get_genre(genre, page)

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "movies_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "movies_browse_genre", "genre": genre, "page": str(page + 1)})
    end_dir("videos")


def movies_years():
    """Browse movies by year"""
    for year in range(2026, 2009, -1):
        add_dir(str(year), {"mode": "movies_browse_year", "year": str(year), "page": "1"})
    end_dir("videos")


def movies_browse_year():
    """Browse movies by year"""
    params = get_params()
    year = params.get("year", "")
    page = int(params.get("page", "1"))

    from resources.lib import hdm2_scraper
    movies = hdm2_scraper.get_by_year(year, page)

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "movies_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "movies_browse_year", "year": year, "page": str(page + 1)})
    end_dir("videos")


def movies_search():
    """Search movies"""
    kb = xbmcgui.Dialog().input("Search Movies", type=xbmcgui.INPUT_ALPHANUM)
    if not kb:
        return
    xbmc.executebuiltin("Container.Update(%s)" % build_url({"mode": "movies_search_results", "query": kb, "page": "1"}))


def movies_search_results():
    """Show search results"""
    params = get_params()
    query = params.get("query", "")
    page = int(params.get("page", "1"))

    from resources.lib import hdm2_scraper
    from resources.lib import streamimdb_scraper
    movies = []
    
    # Search HDMovie2
    try:
        hdm2_results = hdm2_scraper.search(query, page)
        for r in hdm2_results:
            r["title"] = "[HDMovie2] " + r.get("title", "")
        movies.extend(hdm2_results)
    except Exception:
        pass
    
    # Search StreamIMDB
    try:
        si_results = streamimdb_scraper.search(query, page)
        for r in si_results:
            r["title"] = "[StreamIMDB] " + r.get("title", "")
        movies.extend(si_results)
    except Exception:
        pass

    if not movies:
        add_dir("[COLOR gray]No results found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]Found {len(movies)} results for '{query}'[/COLOR]", {"mode": "root"})

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "video"}
        add_dir(
            m.get("title", ""),
            {"mode": "movies_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "movies_search_results", "query": query, "page": str(page + 1)})
    end_dir("videos")


def movies_detail():
    """Show movie details and sources"""
    params = get_params()
    url = params.get("url", "")
    title = params.get("title", "")
    thumb = params.get("thumb", "")

    if not url:
        return

    # Try hdm2 first, then streamimdb
    from resources.lib import hdm2_scraper
    from resources.lib import streamimdb_scraper

    detail = hdm2_scraper.get_detail(url)
    if not detail or not detail.get("sources"):
        detail = streamimdb_scraper.get_detail(url)

    if not detail:
        notify("Could not load movie details", error=True)
        return

    info = {"title": detail.get("title", title), "mediatype": "video"}
    poster = detail.get("poster", thumb)
    sources = detail.get("sources", [])

    if not sources:
        notify("No video sources found", error=True)
        return

    for s in sources:
        label = s.get("label", s.get("name", "Source"))
        play_url = s.get("url", "")
        add_dir(label, {"mode": "play", "url": play_url, "title": detail.get("title", title), "thumb": poster}, poster, False, info)
    end_dir("videos")


# ===================== TV SERIES SECTION =====================

def series_index():
    """TV Series main menu"""
    add_dir("[COLOR gold]🔍 Search Series[/COLOR]", {"mode": "series_search"})
    add_dir("🆕 Latest TV Shows", {"mode": "series_latest", "page": "1"})
    add_dir("📺 Web Series (HDMovie2)", {"mode": "web_series", "page": "1"})
    add_dir("🎭 Series Genres", {"mode": "series_genres"})
    end_dir("tvshows")


def web_series():
    """Show web series from HDMovie2"""
    params = get_params()
    page = int(params.get("page", "1"))

    from resources.lib import hdm2_scraper
    movies = hdm2_scraper.get_genre("web-series", page)

    for m in movies:
        info = {"title": m.get("title", ""), "mediatype": "tvshow"}
        add_dir(
            m.get("title", ""),
            {"mode": "movies_detail", "url": m.get("url", ""), "title": m.get("title", ""), "thumb": m.get("thumb", "")},
            m.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "web_series", "page": str(page + 1)})
    end_dir("tvshows")


def series_latest():
    """Show latest TV series"""
    params = get_params()
    page = int(params.get("page", "1"))

    from resources.lib import streamimdb_scraper
    shows = streamimdb_scraper.get_tv_shows(page)

    for s in shows:
        info = {"title": s.get("title", ""), "mediatype": "tvshow"}
        add_dir(
            s.get("title", ""),
            {"mode": "series_detail", "url": s.get("url", ""), "title": s.get("title", ""), "thumb": s.get("thumb", "")},
            s.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "series_latest", "page": str(page + 1)})
    end_dir("tvshows")


def series_genres():
    """Show TV series genres"""
    genres = [
        ("Action", "action"),
        ("Animation", "animation"),
        ("Comedy", "comedy"),
        ("Crime", "crime"),
        ("Drama", "drama"),
        ("Fantasy", "fantasy"),
        ("Horror", "horror"),
        ("Mystery", "mystery"),
        ("Romance", "romance"),
        ("Sci-Fi", "sci-fi"),
        ("Thriller", "thriller"),
    ]
    for label, slug in genres:
        add_dir(label, {"mode": "series_browse_genre", "genre": slug, "page": "1"})
    end_dir("tvshows")


def series_browse_genre():
    """Browse series by genre"""
    params = get_params()
    genre = params.get("genre", "")
    page = int(params.get("page", "1"))

    from resources.lib import streamimdb_scraper
    shows = streamimdb_scraper.get_tv_by_genre(genre, page)

    for s in shows:
        info = {"title": s.get("title", ""), "mediatype": "tvshow"}
        add_dir(
            s.get("title", ""),
            {"mode": "series_detail", "url": s.get("url", ""), "title": s.get("title", ""), "thumb": s.get("thumb", "")},
            s.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "series_browse_genre", "genre": genre, "page": str(page + 1)})
    end_dir("tvshows")


def series_search():
    """Search TV series"""
    kb = xbmcgui.Dialog().input("Search TV Series", type=xbmcgui.INPUT_ALPHANUM)
    if not kb:
        return
    xbmc.executebuiltin("Container.Update(%s)" % build_url({"mode": "series_search_results", "query": kb, "page": "1"}))


def series_search_results():
    """Show series search results"""
    params = get_params()
    query = params.get("query", "")
    page = int(params.get("page", "1"))

    from resources.lib import streamimdb_scraper
    from resources.lib import hdm2_scraper
    shows = []
    
    # Search StreamIMDB for TV shows
    try:
        si_results = streamimdb_scraper.search_tv(query, page)
        for r in si_results:
            r["title"] = "[StreamIMDB] " + r.get("title", "")
        shows.extend(si_results)
    except Exception:
        pass
    
    # Also search HDMovie2 for web series
    try:
        hdm2_results = hdm2_scraper.search(query, page)
        for r in hdm2_results:
            if "series" in r.get("url", "").lower() or "web" in r.get("url", "").lower():
                r["title"] = "[HDMovie2] " + r.get("title", "")
                shows.append(r)
    except Exception:
        pass

    if not shows:
        add_dir("[COLOR gray]No results found[/COLOR]", {"mode": "root"})
    else:
        add_dir(f"[COLOR yellow]Found {len(shows)} results for '{query}'[/COLOR]", {"mode": "root"})

    for s in shows:
        info = {"title": s.get("title", ""), "mediatype": "tvshow"}
        add_dir(
            s.get("title", ""),
            {"mode": "series_detail", "url": s.get("url", ""), "title": s.get("title", ""), "thumb": s.get("thumb", "")},
            s.get("thumb", ""),
            True,
            info,
        )
    add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "series_search_results", "query": query, "page": str(page + 1)})
    end_dir("tvshows")


def series_detail():
    """Show TV series details with seasons"""
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
            {"mode": "series_season", "url": url, "season": str(season_num), "title": detail.get("title", title)},
            thumb,
            True,
        )
    end_dir("tvshows")


def series_season():
    """Show episodes in a season"""
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


# ===================== TV CHANNELS SECTION =====================

def tv_channels_index():
    """TV Channels main menu"""
    add_dir("🌍 All Channels", {"mode": "tv_channels_list", "category": "all"})
    add_dir("📺 By Country", {"mode": "tv_countries"})
    add_dir("📂 By Category", {"mode": "tv_categories"})
    add_dir("📻 Radio", {"mode": "tv_radio"})
    add_dir("⭐ Favorites", {"mode": "tv_favorites"})
    add_dir("🔄 Auto-Merge TV List (IPTV)", {"mode": "tv_auto_merge"})
    add_dir("📋 Simple IPTV Player", {"mode": "tv_iptv_player"})
    end_dir("videos")


def tv_countries():
    """Show TV channel countries"""
    countries = tv_countries_list()
    for label, country_id in countries:
        add_dir(label, {"mode": "tv_channels_list", "category": country_id, "page": "1"})
    end_dir("videos")


def tv_categories():
    """Show TV channel categories"""
    categories = tv_category_list()
    for label, cat_id in categories:
        add_dir(label, {"mode": "tv_channels_list", "category": cat_id, "page": "1"})
    end_dir("videos")


def tv_channels_list():
    """Show TV channels by category/country with pagination"""
    params = get_params()
    category = params.get("category", "all")
    page = int(params.get("page", "1"))

    from resources.lib import tv_scraper
    channels = tv_scraper.get_channels(category, page)

    for ch in channels:
        info = {"title": ch.get("name", ""), "mediatype": "video"}
        add_dir(
            ch.get("name", ""),
            {"mode": "play", "url": ch.get("url", ""), "title": ch.get("name", ""), "thumb": ch.get("logo", "")},
            ch.get("logo", ""),
            False,
            info,
        )

    # Add next page option
    per_page = 50
    if len(channels) >= per_page:
        add_dir("[COLOR gold]>> Next Page[/COLOR]", {"mode": "tv_channels_list", "category": category, "page": str(page + 1)})

    end_dir("videos")


def tv_radio():
    """Show radio stations"""
    from resources.lib import tv_scraper
    stations = tv_scraper.get_radio()

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


def tv_favorites():
    """Show favorite TV channels"""
    favorites = _get_favorites()
    if not favorites:
        add_dir("[COLOR gray]No favorites yet. Right-click a channel to add.[/COLOR]", {})
        end_dir("videos")
        return

    for fav in favorites:
        info = {"title": fav.get("name", ""), "mediatype": "video"}
        add_dir(
            fav.get("name", ""),
            {"mode": "play", "url": fav.get("url", ""), "title": fav.get("name", ""), "thumb": fav.get("logo", "")},
            fav.get("logo", ""),
            False,
            info,
        )
    end_dir("videos")


def tv_auto_merge():
    """Auto-merge TV list from multiple IPTV sources"""
    from resources.lib import tv_scraper
    xbmcgui.Dialog().notification("MovieHub", "Merging TV lists...", xbmcgui.NOTIFICATION_INFO, 3000)

    merged = tv_scraper.auto_merge_playlist()

    if not merged:
        notify("Could not merge TV list", error=True)
        return

    for ch in merged:
        info = {"title": ch.get("name", ""), "mediatype": "video"}
        add_dir(
            ch.get("name", ""),
            {"mode": "play", "url": ch.get("url", ""), "title": ch.get("name", ""), "thumb": ch.get("logo", "")},
            ch.get("logo", ""),
            False,
            info,
        )
    end_dir("videos")


def tv_iptv_player():
    """Simple IPTV player with merged playlist"""
    from resources.lib import tv_scraper

    m3u_url = get_setting("iptv_m3u_url", "")
    if m3u_url:
        channels = tv_scraper.parse_m3u(m3u_url)
    else:
        channels = tv_scraper.get_default_channels()

    if not channels:
        notify("No channels found", error=True)
        return

    for ch in channels:
        info = {"title": ch.get("name", ""), "mediatype": "video"}
        add_dir(
            ch.get("name", ""),
            {"mode": "play", "url": ch.get("url", ""), "title": ch.get("name", ""), "thumb": ch.get("logo", "")},
            ch.get("logo", ""),
            False,
            info,
        )
    end_dir("videos")


# ===================== PLAYBACK =====================

def play():
    """Play a video"""
    params = get_params()
    url = params.get("url", "")
    title = params.get("title", "")
    thumb = params.get("thumb", "")

    if not url:
        return

    # Resolve the URL if needed
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

def _get_favorites():
    """Get saved favorites"""
    import json
    fav_path = os.path.join(xbmc.translatePath("special://profile/addon_data/" + ADDON_ID), "favorites.json")
    try:
        if os.path.exists(fav_path):
            with open(fav_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_favorite(channel):
    """Add a channel to favorites"""
    import json
    favorites = _get_favorites()
    if not any(f.get("url") == channel.get("url") for f in favorites):
        favorites.append(channel)
        fav_path = os.path.join(xbmc.translatePath("special://profile/addon_data/" + ADDON_ID), "favorites.json")
        try:
            os.makedirs(os.path.dirname(fav_path), exist_ok=True)
            with open(fav_path, "w", encoding="utf-8") as f:
                json.dump(favorites, f, ensure_ascii=False, indent=2)
            notify("Added to favorites")
        except Exception:
            notify("Failed to save favorite", error=True)


# ===================== COUNTRIES & CATEGORIES =====================

def tv_countries_list():
    """Return list of TV countries"""
    return [
        ("United States", "us"),
        ("United Kingdom", "uk"),
        ("India", "in"),
        ("Canada", "ca"),
        ("Australia", "au"),
        ("Germany", "de"),
        ("France", "fr"),
        ("Italy", "it"),
        ("Spain", "es"),
        ("Brazil", "br"),
        ("Mexico", "mx"),
        ("Japan", "jp"),
        ("South Korea", "kr"),
        ("China", "cn"),
        ("Russia", "ru"),
        ("Turkey", "tr"),
        ("Pakistan", "pk"),
        ("Bangladesh", "bd"),
        ("Nepal", "np"),
        ("Sri Lanka", "lk"),
    ]


def tv_category_list():
    """Return list of TV categories"""
    return [
        ("Entertainment", "entertainment"),
        ("News", "news"),
        ("Sports", "sports"),
        ("Movies", "movies"),
        ("Kids", "kids"),
        ("Music", "music"),
        ("Documentary", "documentary"),
        ("Lifestyle", "lifestyle"),
        ("Cooking", "cooking"),
        ("Travel", "travel"),
        ("Science", "science"),
        ("Technology", "technology"),
        ("Business", "business"),
        ("Education", "education"),
        ("Comedy", "comedy"),
        ("Drama", "drama"),
    ]


# ===================== ROOT =====================

def root():
    """Root menu"""
    add_dir("🎬 Movies", {"mode": "movies_index"})
    add_dir("📺 TV Series", {"mode": "series_index"})
    add_dir("📡 Live TV Channels", {"mode": "tv_channels_index"})
    add_dir("⭐ My Favorites", {"mode": "tv_favorites"})
    add_dir("[COLOR gray]⚙ Settings[/COLOR]", {"mode": "settings"})
    end_dir("videos")


# ===================== ROUTER =====================

def run():
    """Main router"""
    params = get_params()
    mode = params.get("mode", "root")

    handlers = {
        "root": root,
        "movies_index": movies_index,
        "movies_latest": movies_latest,
        "movies_genres": movies_genres,
        "movies_browse_genre": movies_browse_genre,
        "movies_years": movies_years,
        "movies_browse_year": movies_browse_year,
        "movies_search": movies_search,
        "movies_search_results": movies_search_results,
        "movies_detail": movies_detail,
        "series_index": series_index,
        "series_latest": series_latest,
        "series_genres": series_genres,
        "series_browse_genre": series_browse_genre,
        "series_search": series_search,
        "series_search_results": series_search_results,
        "series_detail": series_detail,
        "series_season": series_season,
        "web_series": web_series,
        "tv_channels_index": tv_channels_index,
        "tv_countries": tv_countries,
        "tv_categories": tv_categories,
        "tv_channels_list": tv_channels_list,
        "tv_radio": tv_radio,
        "tv_favorites": tv_favorites,
        "tv_auto_merge": tv_auto_merge,
        "tv_iptv_player": tv_iptv_player,
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
