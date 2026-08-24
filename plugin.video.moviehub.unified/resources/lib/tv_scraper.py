# -*- coding: utf-8 -*-
"""
TV Scraper - Live TV channels with auto-merge and IPTV support
"""

import re
import urllib.request
import urllib.parse
import ssl
import json
import os

FREE_TV_API = "https://freetv.studio/api"

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def _fetch(url, headers=None):
    """Fetch URL content"""
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        resp = urllib.request.urlopen(req, context=_ctx, timeout=15)
        return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def get_channels(category="all"):
    """Get TV channels by category"""
    channels = []

    # Try FreeTV Studio API
    try:
        url = f"{FREE_TV_API}/channels"
        if category != "all":
            url += f"?category={category}"
        data = _fetch(url)
        if data:
            result = json.loads(data)
            for ch in result.get("channels", []):
                channels.append({
                    "name": ch.get("name", ""),
                    "url": ch.get("stream_url", ch.get("url", "")),
                    "logo": ch.get("logo", ch.get("icon", "")),
                    "category": ch.get("category", ""),
                    "country": ch.get("country", ""),
                })
    except Exception:
        pass

    # Fallback to static list if API fails
    if not channels:
        channels = _get_default_channels(category)

    return channels


def get_radio():
    """Get radio stations"""
    stations = []
    try:
        url = f"{FREE_TV_API}/radio"
        data = _fetch(url)
        if data:
            result = json.loads(data)
            for st in result.get("stations", []):
                stations.append({
                    "name": st.get("name", ""),
                    "url": st.get("stream_url", st.get("url", "")),
                    "logo": st.get("logo", st.get("icon", "")),
                })
    except Exception:
        pass

    if not stations:
        stations = _get_default_radio()

    return stations


def auto_merge_playlist():
    """Auto-merge TV lists from multiple IPTV sources"""
    merged = []
    seen_urls = set()

    # Source 1: FreeTV Studio API
    try:
        channels = get_channels("all")
        for ch in channels:
            if ch.get("url") and ch["url"] not in seen_urls:
                seen_urls.add(ch["url"])
                merged.append(ch)
    except Exception:
        pass

    # Source 2: Parse M3U playlists from known sources
    m3u_sources = [
        "https://iptv-org.github.io/iptv/index.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/all.m3u",
    ]

    for m3u_url in m3u_sources:
        try:
            channels = parse_m3u(m3u_url)
            for ch in channels:
                if ch.get("url") and ch["url"] not in seen_urls:
                    seen_urls.add(ch["url"])
                    merged.append(ch)
        except Exception:
            continue

    # Source 3: Add default channels
    defaults = _get_default_channels("all")
    for ch in defaults:
        if ch.get("url") and ch["url"] not in seen_urls:
            seen_urls.add(ch["url"])
            merged.append(ch)

    return merged


def parse_m3u(m3u_url):
    """Parse M3U playlist"""
    channels = []
    try:
        content = _fetch(m3u_url)
        if not content:
            return channels

        name = ""
        logo = ""
        group = ""

        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#EXTINF:"):
                # Parse channel info
                name_m = re.search(r'[^,]+,(.*)$', line)
                if name_m:
                    name = name_m.group(1).strip()

                logo_m = re.search(r'tvg-logo="([^"]*)"', line)
                if logo_m:
                    logo = logo_m.group(1)

                group_m = re.search(r'group-title="([^"]*)"', line)
                if group_m:
                    group = group_m.group(1)
            elif line and not line.startswith("#"):
                # This is the stream URL
                if name:
                    channels.append({
                        "name": name,
                        "url": line,
                        "logo": logo,
                        "category": group,
                    })
                name = ""
                logo = ""
                group = ""
    except Exception:
        pass

    return channels


def get_default_channels():
    """Get default TV channels"""
    return _get_default_channels("all")


def _get_default_channels(category="all"):
    """Default TV channels list"""
    all_channels = [
        # News
        {"name": "BBC World News", "url": "https://vs-hls-push-ww-live.akamaized.net/x=4/i=urn:bbc:pips:service:bbc_news_channel_hd/t=3840/v=pv14/b=5070016/main.m3u8", "logo": "", "category": "news", "country": "uk"},
        {"name": "CNN International", "url": "https://cnn-cnninternational-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "news", "country": "us"},
        {"name": "Al Jazeera English", "url": "https://live-hls-web-aje.getaj.net/AJE/01.m3u8", "logo": "", "category": "news", "country": "qa"},
        {"name": "France 24 English", "url": "https://www.youtube.com/embed/Ap-UM1O9tI8", "logo": "", "category": "news", "country": "fr"},
        {"name": "DW News", "url": "https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/index.m3u8", "logo": "", "category": "news", "country": "de"},
        {"name": "RT News", "url": "https://rt-glb.rttv.com/dvr/rtnews/playlist.m3u8", "logo": "", "category": "news", "country": "ru"},
        {"name": "CGTN", "url": "https://news.cgtn.com/resource/live/english/cgtn-news.m3u8", "logo": "", "category": "news", "country": "cn"},
        {"name": "NHK World Japan", "url": "https://nhkwlive-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp-en/index.m3u8", "logo": "", "category": "news", "country": "jp"},
        {"name": "Sky News", "url": "https://siloh.pluto.tv/lilo/production/SkyNews/master.m3u8", "logo": "", "category": "news", "country": "uk"},
        {"name": "Bloomberg", "url": "https://bloomberg-bloomberg-5-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "news", "country": "us"},

        # Sports
        {"name": "Red Bull TV", "url": "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "Stadium", "url": "https://stadium-ringofrock-1.sinclair.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "Olympic Channel", "url": "https://ott-live.olympicchannel.com/out/u/OC1.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "FIFA TV", "url": "https://fifa-fifa-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "sports", "country": "int"},

        # Entertainment
        {"name": "Pluto TV Movies", "url": "https://siloh.pluto.tv/lilo/production/PlutoTV/master.m3u8", "logo": "", "category": "entertainment", "country": "us"},
        {"name": "Retro Crush", "url": "https://amg01201-cinedigmenterta-retrocrush-cineverse-x70vj.amagi.tv/playlist/amg01201-cinedigmenterta-retrocrush-cineverse/playlist.m3u8", "logo": "", "category": "entertainment", "country": "us"},
        {"name": "Gravitas Movies", "url": "https://gravitas-movies-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "movies", "country": "us"},
        {"name": "Action Movies", "url": "https://amg01076-wavveinternationalfast-actionmovies-plex-tk8g5.amagi.tv/playlist/amg01076-wavveinternationalfast-actionmovies-plex/playlist.m3u8", "logo": "", "category": "movies", "country": "us"},

        # Music
        {"name": "MTV Block Party", "url": "https://pluto.tv/en/live-tv/5d93b4a446f26600016a67d8", "logo": "", "category": "music", "country": "us"},
        {"name": "Qello Concerts", "url": "https://cdn-ue1-prod.tsv2.amagi.tv/playlist/amg00733-qelloconcertsllc-qello-cineverse/playlist.m3u8", "logo": "", "category": "music", "country": "us"},
        {"name": "Stingray Music", "url": "https://dai.google.com/linear/hls/pa/event/2G_7Aq1qRkWkLQh13-yE-g/master.m3u8", "logo": "", "category": "music", "country": "us"},

        # Kids
        {"name": "PBS Kids", "url": "https://2-fss2-streamhoster.pluto.tv/lilo/production/PBSKids/master.m3u8", "logo": "", "category": "kids", "country": "us"},
        {"name": "Cartoon Network", "url": "https://amg00793-amg00793c1-tubi-us-2276.playouts.now.amagi.tv/playlist/amg00793-amg00793-tubi-cartoon-network/playlist.m3u8", "logo": "", "category": "kids", "country": "us"},
        {"name": "Moonbug Kids", "url": "https://moonbug-rokuus.amagi.tv/playlist.m3u8", "logo": "", "category": "kids", "country": "us"},

        # Documentary
        {"name": "Documentary+", "url": "https://documentaryplus-documentaryplus-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "documentary", "country": "us"},
        {"name": "Love Nature", "url": "https://dai2-xumoodgeous.google.com/linear/hls/pa/event/9C4Q_5QaT5y9U5QaT5y9U5/master.m3u8", "logo": "", "category": "documentary", "country": "us"},
        {"name": "Xplore", "url": "https://xplore-xplore-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "documentary", "country": "us"},

        # Indian Channels
        {"name": "NDTV India", "url": "https://ndtvindiaelemarchana.akamaized.net/hls/live/2003678/ndtvindia/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "Republic TV", "url": "https://weblive.republicworld.com/liveorigin/republictv/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "India Today", "url": "https://indiatodayelemarchana.akamaized.net/hls/live/2003678/indiatoday/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "Times Now", "url": "https://timesnow-lh.akamaihd.net/i/TNDelivery@344381/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "Star Plus", "url": "https://starplus.akamaized.net/hls/live/2003678/starplus/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Zee TV", "url": "https://zee5.akamaized.net/hls/live/2003678/zeetv/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Sony TV", "url": "https://sony.akamaized.net/hls/live/2003678/sonytv/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Colors TV", "url": "https://colors.akamaized.net/hls/live/2003678/colorstv/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
    ]

    if category == "all":
        return all_channels
    return [ch for ch in all_channels if ch.get("category") == category]


def _get_default_radio():
    """Default radio stations"""
    return [
        {"name": "SomaFM Groove Salad", "url": "https://ice1.somafm.com/groovesalad-128-mp3", "logo": ""},
        {"name": "SomaFM DEF CON", "url": "https://ice1.somafm.com/defcon-128-mp3", "logo": ""},
        {"name": "SomaFM Drone Zone", "url": "https://ice1.somafm.com/dronezone-128-mp3", "logo": ""},
        {"name": "SomaFM Secret Agent", "url": "https://ice1.somafm.com/secretagent-128-mp3", "logo": ""},
        {"name": "SomaFM Beat Blender", "url": "https://ice1.somafm.com/beatblender-128-mp3", "logo": ""},
        {"name": "SomaFM Vaporwaves", "url": "https://ice1.somafm.com/vaporwaves-128-mp3", "logo": ""},
        {"name": "SomaFM Space Station", "url": "https://ice1.somafm.com/spacestation-128-mp3", "logo": ""},
        {"name": "SomaFM Deep Space One", "url": "https://ice1.somafm.com/deepspaceone-128-mp3", "logo": ""},
        {"name": "SomaFM Mission Control", "url": "https://ice1.somafm.com/missioncontrol-128-mp3", "logo": ""},
        {"name": "SomaFM PopTron", "url": "https://ice1.somafm.com/poptron-128-mp3", "logo": ""},
        {"name": "SomaFM Lush", "url": "https://ice1.somafm.com/lush-128-mp3", "logo": ""},
        {"name": "SomaFM Fluid", "url": "https://ice1.somafm.com/fluid-128-mp3", "logo": ""},
        {"name": "SomaFM Suburbs of Goa", "url": "https://ice1.somafm.com/suburbsofgoa-128-mp3", "logo": ""},
        {"name": "SomaFM The Trip", "url": "https://ice1.somafm.com/thetrip-128-mp3", "logo": ""},
        {"name": "SomaFM Black Rock FM", "url": "https://ice1.somafm.com/blackrockfm-128-mp3", "logo": ""},
        {"name": "SomaFM Agent Danger", "url": "https://ice1.somafm.com/agentdanger-128-mp3", "logo": ""},
        {"name": "SomaFM Sonic Universe", "url": "https://ice1.somafm.com/sonicuniverse-128-mp3", "logo": ""},
        {"name": "SomaFM Illinois Street Lounge", "url": "https://ice1.somafm.com/illinoisstreetlounge-128-mp3", "logo": ""},
        {"name": "SomaFM Seventh Voyage", "url": "https://ice1.somafm.com/seventhvoyage-128-mp3", "logo": ""},
        {"name": "SomaFM Left Coast 70s", "url": "https://ice1.somafm.com/leftcoast70s-128-mp3", "logo": ""},
        {"name": "SomaFM cliqhop idm", "url": "https://ice1.somafm.com/cliqhop-128-mp3", "logo": ""},
        {"name": "SomaFM Dub Step Beyond", "url": "https://ice1.somafm.com/dubstepbeyond-128-mp3", "logo": ""},
        {"name": "SomaFM Folk Forward", "url": "https://ice1.somafm.com/folkforward-128-mp3", "logo": ""},
        {"name": "SomaFM Boot Liquor", "url": "https://ice1.somafm.com/bootliquor-128-mp3", "logo": ""},
        {"name": "SomaFM Digitalis", "url": "https://ice1.somafm.com/digitalis-128-mp3", "logo": ""},
        {"name": "SomaFM Iceland Airwaves", "url": "https://ice1.somafm.com/icelandairwaves-128-mp3", "logo": ""},
        {"name": "SomaFM South by Soma", "url": "https://ice1.somafm.com/southbysoma-128-mp3", "logo": ""},
        {"name": "SomaFM SF 10-33", "url": "https://ice1.somafm.com/sf10-33-128-mp3", "logo": ""},
        {"name": "SomaFM Earwaves", "url": "https://ice1.somafm.com/earwaves-128-mp3", "logo": ""},
        {"name": "SomaFM Heavyweight Reggae", "url": "https://ice1.somafm.com/heavyweightreggae-256-mp3", "logo": ""},
        {"name": "SomaFM Metal Detector", "url": "https://ice1.somafm.com/metaldetector-128-mp3", "logo": ""},
        {"name": "SomaFM Covers", "url": "https://ice1.somafm.com/covers-128-mp3", "logo": ""},
        {"name": "SomaFM n5MD Radio", "url": "https://ice1.somafm.com/n5md-128-mp3", "logo": ""},
        {"name": "SomaFM Department Store Christmas", "url": "https://ice1.somafm.com/departmentstorechristmas-128-mp3", "logo": ""},
        {"name": "SomaFM Tiki Time", "url": "https://ice1.somafm.com/tikitime-128-mp3", "logo": ""},
        {"name": "SomaFM Synphaera", "url": "https://ice1.somafm.com/synphaera-128-mp3", "logo": ""},
        {"name": "SomaFM Dark Zone", "url": "https://ice1.somafm.com/darkzone-128-mp3", "logo": ""},
        {"name": "SomaFM Jolly Ol' Soul", "url": "https://ice1.somafm.com/jollyolsoul-128-mp3", "logo": ""},
        {"name": "SomaFM Somafm Live", "url": "https://ice1.somafm.com/somafmlive-128-mp3", "logo": ""},
        {"name": "SomaFM Secret Agent", "url": "https://ice1.somafm.com/secretagent-256-mp3", "logo": ""},
        {"name": "SomaFM Groove Salad", "url": "https://ice1.somafm.com/groovesalad-256-mp3", "logo": ""},
        {"name": "SomaFM Drone Zone", "url": "https://ice1.somafm.com/dronezone-256-mp3", "logo": ""},
        {"name": "SomaFM DEF CON", "url": "https://ice1.somafm.com/defcon-256-mp3", "logo": ""},
        {"name": "SomaFM Beat Blender", "url": "https://ice1.somafm.com/beatblender-256-mp3", "logo": ""},
        {"name": "SomaFM Vaporwaves", "url": "https://ice1.somafm.com/vaporwaves-256-mp3", "logo": ""},
        {"name": "SomaFM Space Station", "url": "https://ice1.somafm.com/spacestation-256-mp3", "logo": ""},
        {"name": "SomaFM Deep Space One", "url": "https://ice1.somafm.com/deepspaceone-256-mp3", "logo": ""},
        {"name": "SomaFM Mission Control", "url": "https://ice1.somafm.com/missioncontrol-256-mp3", "logo": ""},
        {"name": "SomaFM PopTron", "url": "https://ice1.somafm.com/poptron-256-mp3", "logo": ""},
        {"name": "SomaFM Lush", "url": "https://ice1.somafm.com/lush-256-mp3", "logo": ""},
        {"name": "SomaFM Fluid", "url": "https://ice1.somafm.com/fluid-256-mp3", "logo": ""},
        {"name": "SomaFM Suburbs of Goa", "url": "https://ice1.somafm.com/suburbsofgoa-256-mp3", "logo": ""},
        {"name": "SomaFM The Trip", "url": "https://ice1.somafm.com/thetrip-256-mp3", "logo": ""},
        {"name": "SomaFM Black Rock FM", "url": "https://ice1.somafm.com/blackrockfm-256-mp3", "logo": ""},
        {"name": "SomaFM Agent Danger", "url": "https://ice1.somafm.com/agentdanger-256-mp3", "logo": ""},
        {"name": "SomaFM Sonic Universe", "url": "https://ice1.somafm.com/sonicuniverse-256-mp3", "logo": ""},
        {"name": "SomaFM Illinois Street Lounge", "url": "https://ice1.somafm.com/illinoisstreetlounge-256-mp3", "logo": ""},
        {"name": "SomaFM Seventh Voyage", "url": "https://ice1.somafm.com/seventhvoyage-256-mp3", "logo": ""},
        {"name": "SomaFM Left Coast 70s", "url": "https://ice1.somafm.com/leftcoast70s-256-mp3", "logo": ""},
        {"name": "SomaFM cliqhop idm", "url": "https://ice1.somafm.com/cliqhop-256-mp3", "logo": ""},
        {"name": "SomaFM Dub Step Beyond", "url": "https://ice1.somafm.com/dubstepbeyond-256-mp3", "logo": ""},
        {"name": "SomaFM Folk Forward", "url": "https://ice1.somafm.com/folkforward-256-mp3", "logo": ""},
        {"name": "SomaFM Boot Liquor", "url": "https://ice1.somafm.com/bootliquor-256-mp3", "logo": ""},
        {"name": "SomaFM Digitalis", "url": "https://ice1.somafm.com/digitalis-256-mp3", "logo": ""},
        {"name": "SomaFM Iceland Airwaves", "url": "https://ice1.somafm.com/icelandairwaves-256-mp3", "logo": ""},
        {"name": "SomaFM South by Soma", "url": "https://ice1.somafm.com/southbysoma-256-mp3", "logo": ""},
        {"name": "SomaFM SF 10-33", "url": "https://ice1.somafm.com/sf10-33-256-mp3", "logo": ""},
        {"name": "SomaFM Earwaves", "url": "https://ice1.somafm.com/earwaves-256-mp3", "logo": ""},
        {"name": "SomaFM Heavyweight Reggae", "url": "https://ice1.somafm.com/heavyweightreggae-256-mp3", "logo": ""},
        {"name": "SomaFM Metal Detector", "url": "https://ice1.somafm.com/metaldetector-256-mp3", "logo": ""},
        {"name": "SomaFM Covers", "url": "https://ice1.somafm.com/covers-256-mp3", "logo": ""},
        {"name": "SomaFM n5MD Radio", "url": "https://ice1.somafm.com/n5md-256-mp3", "logo": ""},
        {"name": "SomaFM Department Store Christmas", "url": "https://ice1.somafm.com/departmentstorechristmas-256-mp3", "logo": ""},
        {"name": "SomaFM Tiki Time", "url": "https://ice1.somafm.com/tikitime-256-mp3", "logo": ""},
        {"name": "SomaFM Synphaera", "url": "https://ice1.somafm.com/synphaera-256-mp3", "logo": ""},
        {"name": "SomaFM Dark Zone", "url": "https://ice1.somafm.com/darkzone-256-mp3", "logo": ""},
        {"name": "SomaFM Jolly Ol' Soul", "url": "https://ice1.somafm.com/jollyolsoul-256-mp3", "logo": ""},
        {"name": "SomaFM Somafm Live", "url": "https://ice1.somafm.com/somafmlive-256-mp3", "logo": ""},
    ]
