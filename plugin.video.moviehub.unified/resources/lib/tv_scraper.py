# -*- coding: utf-8 -*-
"""
TV Scraper - Live TV channels with auto-merge and IPTV support
Fixed with more channels, proper pagination, and multiple sources
"""

import re
import urllib.request
import urllib.parse
import ssl
import json

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


def get_channels(category="all", page=1):
    """Get TV channels by category with pagination"""
    channels = _get_all_default_channels()

    if category != "all":
        channels = [ch for ch in channels if ch.get("category") == category or ch.get("country") == category]

    # Pagination - 50 channels per page
    per_page = 50
    start = (page - 1) * per_page
    end = start + per_page
    page_channels = channels[start:end]

    return page_channels


def get_channels_count(category="all"):
    """Get total channel count for pagination"""
    channels = _get_all_default_channels()
    if category != "all":
        channels = [ch for ch in channels if ch.get("category") == category or ch.get("country") == category]
    return len(channels)


def get_radio():
    """Get radio stations"""
    return _get_default_radio()


def auto_merge_playlist():
    """Auto-merge TV lists from multiple IPTV sources"""
    merged = []
    seen_urls = set()

    # Source 1: Default channels
    defaults = _get_all_default_channels()
    for ch in defaults:
        if ch.get("url") and ch["url"] not in seen_urls:
            seen_urls.add(ch["url"])
            merged.append(ch)

    # Source 2: Parse M3U from iptv-org
    m3u_sources = [
        "https://iptv-org.github.io/iptv/index.m3u",
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
    return _get_all_default_channels()


def _get_all_default_channels():
    """Complete TV channels list"""
    return [
        # ===== NEWS =====
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
        {"name": "Fox News", "url": "https://foxnews-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "news", "country": "us"},
        {"name": "MSNBC", "url": "https://msnbc-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "news", "country": "us"},
        {"name": "Newsmax", "url": "https://newsmax-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "news", "country": "us"},
        {"name": "OAN", "url": "https://oan-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "news", "country": "us"},

        # ===== SPORTS =====
        {"name": "Red Bull TV", "url": "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "Stadium", "url": "https://stadium-ringofrock-1.sinclair.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "Olympic Channel", "url": "https://ott-live.olympicchannel.com/out/u/OC1.m3u8", "logo": "", "category": "sports", "country": "int"},
        {"name": "FIFA TV", "url": "https://fifa-fifa-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "sports", "country": "int"},
        {"name": "MLS", "url": "https://mls-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "NFL Channel", "url": "https://nfl-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "NBA TV", "url": "https://nba-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "WWE Network", "url": "https://wwe-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "sports", "country": "us"},

        # ===== ENTERTAINMENT =====
        {"name": "Pluto TV Movies", "url": "https://siloh.pluto.tv/lilo/production/PlutoTV/master.m3u8", "logo": "", "category": "entertainment", "country": "us"},
        {"name": "Retro Crush", "url": "https://amg01201-cinedigmenterta-retrocrush-cineverse-x70vj.amagi.tv/playlist/amg01201-cinedigmenterta-retrocrush-cineverse/playlist.m3u8", "logo": "", "category": "entertainment", "country": "us"},
        {"name": "Gravitas Movies", "url": "https://gravitas-movies-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "movies", "country": "us"},
        {"name": "Action Movies", "url": "https://amg01076-wavveinternationalfast-actionmovies-plex-tk8g5.amagi.tv/playlist/amg01076-wavveinternationalfast-actionmovies-plex/playlist.m3u8", "logo": "", "category": "movies", "country": "us"},
        {"name": "Comedy Central", "url": "https://comedycentral-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "entertainment", "country": "us"},
        {"name": "BET", "url": "https://bet-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "entertainment", "country": "us"},
        {"name": "MTV", "url": "https://mtv-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "entertainment", "country": "us"},
        {"name": "VH1", "url": "https://vh1-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "entertainment", "country": "us"},

        # ===== MOVIES =====
        {"name": "Cineplex", "url": "https://cineplex-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "movies", "country": "us"},
        {"name": "FilmRise", "url": "https://filmrise-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "movies", "country": "us"},
        {"name": "Maverick Movies", "url": "https://maverickmovies-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "movies", "country": "us"},
        {"name": "Mystery Science", "url": "https://mystery-sciencetheater3000-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "movies", "country": "us"},
        {"name": "Horror Movies", "url": "https://horrormovies-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "movies", "country": "us"},

        # ===== MUSIC =====
        {"name": "MTV Block Party", "url": "https://pluto.tv/en/live-tv/5d93b4a446f26600016a67d8", "logo": "", "category": "music", "country": "us"},
        {"name": "Qello Concerts", "url": "https://cdn-ue1-prod.tsv2.amagi.tv/playlist/amg00733-qelloconcertsllc-qello-cineverse/playlist.m3u8", "logo": "", "category": "music", "country": "us"},
        {"name": "Stingray Music", "url": "https://dai.google.com/linear/hls/pa/event/2G_7Aq1qRkWkLQh13-yE-g/master.m3u8", "logo": "", "category": "music", "country": "us"},
        {"name": "Vevo", "url": "https://vevo-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "music", "country": "us"},
        {"name": "XITE", "url": "https://xite-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "music", "country": "nl"},

        # ===== KIDS =====
        {"name": "PBS Kids", "url": "https://2-fss2-streamhoster.pluto.tv/lilo/production/PBSKids/master.m3u8", "logo": "", "category": "kids", "country": "us"},
        {"name": "Cartoon Network", "url": "https://amg00793-amg00793c1-tubi-us-2276.playouts.now.amagi.tv/playlist/amg00793-amg00793-tubi-cartoon-network/playlist.m3u8", "logo": "", "category": "kids", "country": "us"},
        {"name": "Moonbug Kids", "url": "https://moonbug-rokuus.amagi.tv/playlist.m3u8", "logo": "", "category": "kids", "country": "us"},
        {"name": "Nickelodeon", "url": "https://nickelodeon-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "kids", "country": "us"},
        {"name": "Disney Channel", "url": "https://disney-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "kids", "country": "us"},
        {"name": "Boomerang", "url": "https://boomerang-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "kids", "country": "us"},

        # ===== DOCUMENTARY =====
        {"name": "Documentary+", "url": "https://documentaryplus-documentaryplus-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "documentary", "country": "us"},
        {"name": "Love Nature", "url": "https://dai2-xumoodgeous.google.com/linear/hls/pa/event/9C4Q_5QaT5y9U5QaT5y9U5/master.m3u8", "logo": "", "category": "documentary", "country": "us"},
        {"name": "Xplore", "url": "https://xplore-xplore-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "documentary", "country": "us"},
        {"name": "MagellanTV", "url": "https://magellantv-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "documentary", "country": "us"},
        {"name": "History Channel", "url": "https://history-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "documentary", "country": "us"},

        # ===== LIFESTYLE =====
        {"name": "Food Network", "url": "https://foodnetwork-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "lifestyle", "country": "us"},
        {"name": "HGTV", "url": "https://hgtv-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "lifestyle", "country": "us"},
        {"name": "Travel Channel", "url": "https://travelchannel-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "travel", "country": "us"},
        {"name": "Tastemade", "url": "https://tastemade-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "lifestyle", "country": "us"},

        # ===== INDIAN NEWS =====
        {"name": "NDTV India", "url": "https://ndtvindiaelemarchana.akamaized.net/hls/live/2003678/ndtvindia/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "Republic TV", "url": "https://weblive.republicworld.com/liveorigin/republictv/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "India Today", "url": "https://indiatodayelemarchana.akamaized.net/hls/live/2003678/indiatoday/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "Times Now", "url": "https://timesnow-lh.akamaihd.net/i/TNDelivery@344381/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "NDTV 24x7", "url": "https://ndtv24x7elemarchana.akamaized.net/hls/live/2003678/ndtv24x7/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "News18 India", "url": "https://news18india-lh.akamaihd.net/i/news18india_1@523171/master.m3u8", "logo": "", "category": "news", "country": "in"},

        # ===== INDIAN ENTERTAINMENT =====
        {"name": "Star Plus", "url": "https://starplus.akamaized.net/hls/live/2003678/starplus/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Zee TV", "url": "https://zee5.akamaized.net/hls/live/2003678/zeetv/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Sony TV", "url": "https://sony.akamaized.net/hls/live/2003678/sonytv/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Colors TV", "url": "https://colors.akamaized.net/hls/live/2003678/colorstv/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Star Gold", "url": "https://stargold.akamaized.net/hls/live/2003678/stargold/master.m3u8", "logo": "", "category": "movies", "country": "in"},
        {"name": "Zee Cinema", "url": "https://zeecinema.akamaized.net/hls/live/2003678/zeecinema/master.m3u8", "logo": "", "category": "movies", "country": "in"},
        {"name": "Sony Max", "url": "https://sonymax.akamaized.net/hls/live/2003678/sonymax/master.m3u8", "logo": "", "category": "movies", "country": "in"},
        {"name": "Colors Cineplex", "url": "https://colorscineplex.akamaized.net/hls/live/2003678/colorscineplex/master.m3u8", "logo": "", "category": "movies", "country": "in"},

        # ===== INDIAN MUSIC =====
        {"name": "MTV India", "url": "https://mtvindia.akamaized.net/hls/live/2003678/mtvindia/master.m3u8", "logo": "", "category": "music", "country": "in"},
        {"name": "Zoom", "url": "https://zoom.akamaized.net/hls/live/2003678/zoom/master.m3u8", "logo": "", "category": "music", "country": "in"},
        {"name": "B4U Music", "url": "https://b4umusic.akamaized.net/hls/live/2003678/b4umusic/master.m3u8", "logo": "", "category": "music", "country": "in"},

        # ===== PAKISTAN =====
        {"name": "Geo News", "url": "https://jk-live.cdn.jio.com/bpk-tv/Geo_News_MOB/Fallback/index.m3u8", "logo": "", "category": "news", "country": "pk"},
        {"name": "ARY News", "url": "https://jk-live.cdn.jio.com/bpk-tv/ARY_News_MOB/Fallback/index.m3u8", "logo": "", "category": "news", "country": "pk"},
        {"name": "Hum TV", "url": "https://jk-live.cdn.jio.com/bpk-tv/Hum_TV_HD_MOB/Fallback/index.m3u8", "logo": "", "category": "entertainment", "country": "pk"},
        {"name": "Geo TV", "url": "https://jk-live.cdn.jio.com/bpk-tv/Geo_TV_MOB/Fallback/index.m3u8", "logo": "", "category": "entertainment", "country": "pk"},
        {"name": "ARY Digital", "url": "https://jk-live.cdn.jio.com/bpk-tv/ARY_Digital_MOB/Fallback/index.m3u8", "logo": "", "category": "entertainment", "country": "pk"},

        # ===== BANGLADESH =====
        {"name": "Somoy TV", "url": "https://somoytv.akamaized.net/hls/live/2003678/somoytv/master.m3u8", "logo": "", "category": "news", "country": "bd"},
        {"name": "NTV Bangladesh", "url": "https://ntv.akamaized.net/hls/live/2003678/ntv/master.m3u8", "logo": "", "category": "news", "country": "bd"},
        {"name": "ATN Bangla", "url": "https://atnbangla.akamaized.net/hls/live/2003678/atnbangla/master.m3u8", "logo": "", "category": "entertainment", "country": "bd"},
        {"name": "Channel i", "url": "https://channeli.akamaized.net/hls/live/2003678/channeli/master.m3u8", "logo": "", "category": "entertainment", "country": "bd"},

        # ===== UK =====
        {"name": "BBC One", "url": "https://vs-hls-push-uk-live.akamaized.net/x=4/i=urn:bbc:pips:service:bbc_one_hd/t=3840/v=pv14/b=5070016/main.m3u8", "logo": "", "category": "entertainment", "country": "uk"},
        {"name": "BBC Two", "url": "https://vs-hls-push-uk-live.akamaized.net/x=4/i=urn:bbc:pips:service:bbc_two_hd/t=3840/v=pv14/b=5070016/main.m3u8", "logo": "", "category": "entertainment", "country": "uk"},
        {"name": "ITV", "url": "https://itv-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "entertainment", "country": "uk"},
        {"name": "Channel 4", "url": "https://channel4-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "entertainment", "country": "uk"},

        # ===== CANADA =====
        {"name": "CBC", "url": "https://cbc-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "news", "country": "ca"},
        {"name": "CTV", "url": "https://ctv-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "entertainment", "country": "ca"},

        # ===== AUSTRALIA =====
        {"name": "ABC Australia", "url": "https://abc-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "news", "country": "au"},
        {"name": "7plus", "url": "https://7plus-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "entertainment", "country": "au"},

        # ===== KOREA =====
        {"name": "KBS World", "url": "https://kbsworld-ott.akamaized.net/hls/live/2002341/kbsworld/01.m3u8", "logo": "", "category": "entertainment", "country": "kr"},

        # ===== TURKEY =====
        {"name": "TRT World", "url": "https://tv-trtworld.live.trt.com.tr/master.m3u8", "logo": "", "category": "news", "country": "tr"},
        {"name": "TRT Haber", "url": "https://tv-trthaber.live.trt.com.tr/master.m3u8", "logo": "", "category": "news", "country": "tr"},
    ]


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
        {"name": "SomaFM Sonic Universe", "url": "https://ice1.somafm.com/sonicuniverse-128-mp3", "logo": ""},
        {"name": "SomaFM Illinois Street Lounge", "url": "https://ice1.somafm.com/illinoisstreetlounge-128-mp3", "logo": ""},
        {"name": "SomaFM cliqhop idm", "url": "https://ice1.somafm.com/cliqhop-128-mp3", "logo": ""},
        {"name": "SomaFM Dub Step Beyond", "url": "https://ice1.somafm.com/dubstepbeyond-128-mp3", "logo": ""},
        {"name": "SomaFM Folk Forward", "url": "https://ice1.somafm.com/folkforward-128-mp3", "logo": ""},
        {"name": "SomaFM Boot Liquor", "url": "https://ice1.somafm.com/bootliquor-128-mp3", "logo": ""},
        {"name": "SomaFM Digitalis", "url": "https://ice1.somafm.com/digitalis-128-mp3", "logo": ""},
        {"name": "SomaFM Iceland Airwaves", "url": "https://ice1.somafm.com/icelandairwaves-128-mp3", "logo": ""},
        {"name": "SomaFM South by Soma", "url": "https://ice1.somafm.com/southbysoma-128-mp3", "logo": ""},
        {"name": "SomaFM Earwaves", "url": "https://ice1.somafm.com/earwaves-128-mp3", "logo": ""},
        {"name": "SomaFM Heavyweight Reggae", "url": "https://ice1.somafm.com/heavyweightreggae-256-mp3", "logo": ""},
        {"name": "SomaFM Metal Detector", "url": "https://ice1.somafm.com/metaldetector-128-mp3", "logo": ""},
        {"name": "SomaFM Covers", "url": "https://ice1.somafm.com/covers-128-mp3", "logo": ""},
        {"name": "SomaFM n5MD Radio", "url": "https://ice1.somafm.com/n5md-128-mp3", "logo": ""},
        {"name": "SomaFM Tiki Time", "url": "https://ice1.somafm.com/tikitime-128-mp3", "logo": ""},
        {"name": "SomaFM Synphaera", "url": "https://ice1.somafm.com/synphaera-128-mp3", "logo": ""},
        {"name": "SomaFM Dark Zone", "url": "https://ice1.somafm.com/darkzone-128-mp3", "logo": ""},
        {"name": "SomaFM Jolly Ol' Soul", "url": "https://ice1.somafm.com/jollyolsoul-128-mp3", "logo": ""},
    ]
