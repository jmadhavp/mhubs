# -*- coding: utf-8 -*-
"""
FreeTV Studio Scraper - https://freetv.studio
Live TV channels with countries, categories, and radio
"""

import re
import urllib.request
import urllib.parse
import ssl
import json

BASE = "https://freetv.studio"

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def _fetch(url, headers=None):
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        resp = urllib.request.urlopen(req, context=_ctx, timeout=20)
        return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _abs(url, base=BASE):
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http"):
        return url
    return urllib.parse.urljoin(base, url)


def _extract_rsc_data(html):
    """Extract RSC (React Server Components) data from page"""
    # Look for RSC payload in script tags
    for script in re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL):
        # Look for channel data patterns
        if '"channels"' in script or '"stream_url"' in script or '"name"' in script:
            try:
                # Try to find JSON objects with channel data
                for m in re.finditer(r'\{[^{}]*"name"[^{}]*\}', script):
                    try:
                        data = json.loads(m.group(0))
                        if data.get("name"):
                            return data
                    except Exception:
                        continue
            except Exception:
                pass
    return None


def get_countries():
    """Get list of countries"""
    html = _fetch(BASE + "/countries")
    if not html:
        return _get_default_countries()

    countries = []
    seen = set()

    # Parse country links
    for a in re.finditer(r'href="/country/([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
        code = a.group(1).upper()
        name_m = re.search(r'>([^<]+)<', a.group(2))
        name = name_m.group(1).strip() if name_m else code
        if code not in seen:
            seen.add(code)
            countries.append({"code": code, "name": name})

    if not countries:
        return _get_default_countries()

    return countries


def get_categories():
    """Get list of categories"""
    html = _fetch(BASE + "/categories")
    if not html:
        return _get_default_categories()

    categories = []
    seen = set()

    for a in re.finditer(r'href="/category/([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
        slug = a.group(1)
        name_m = re.search(r'>([^<]+)<', a.group(2))
        name = name_m.group(1).strip() if name_m else slug.title()
        if slug not in seen:
            seen.add(slug)
            categories.append({"slug": slug, "name": name})

    if not categories:
        return _get_default_categories()

    return categories


def get_channels_by_country(country_code, category=None, page=1):
    """Get channels by country"""
    path = f"/country/{country_code.upper()}"
    if category:
        path += f"?cat={category}"

    html = _fetch(BASE + path)
    if not html:
        return []

    return _parse_channel_cards(html)


def get_channels_by_category(category_slug, page=1):
    """Get channels by category"""
    html = _fetch(BASE + f"/category/{category_slug}")
    if not html:
        return []

    return _parse_channel_cards(html)


def get_all_channels(page=1):
    """Get all channels from homepage"""
    html = _fetch(BASE + "/")
    if not html:
        return _get_default_channels()

    channels = _parse_channel_cards(html)
    if not channels:
        return _get_default_channels()

    # Pagination
    per_page = 50
    start = (page - 1) * per_page
    end = start + per_page
    return channels[start:end]


def get_radio(page=1):
    """Get radio stations"""
    html = _fetch(BASE + "/radio")
    if not html:
        return _get_default_radio()

    channels = _parse_channel_cards(html)
    if not channels:
        return _get_default_radio()

    return channels


def get_channel_stream(url):
    """Get stream URL for a channel"""
    html = _fetch(url)
    if not html:
        return None

    # Look for stream URL in page
    for pattern in [
        r'(?:stream_url|src|file)\s*[:=]\s*"([^"]+)"',
        r'(?:source|video)[^>]+src="([^"]+)"',
        r'<iframe[^>]*src="([^"]+)"',
    ]:
        m = re.search(pattern, html, re.I)
        if m:
            stream_url = m.group(1)
            if stream_url.startswith("http"):
                return stream_url

    return url


def _parse_channel_cards(html):
    """Parse channel cards from HTML"""
    channels = []
    seen = set()

    # Pattern 1: /channel/ links
    for a in re.finditer(r'<a[^>]+href="(/channel/[^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
        url = _abs(a.group(1))
        content = a.group(2)

        if url in seen:
            continue

        name = ""
        img_m = re.search(r'alt="([^"]+)"', content)
        if img_m:
            name = img_m.group(1)
        else:
            name_m = re.search(r'>([^<]+)<', content)
            if name_m:
                name = name_m.group(1).strip()

        if not name or len(name) < 2:
            # Try to extract from URL
            name = url.split("/")[-1].replace("-", " ").replace(".", " ").title()

        seen.add(url)

        logo = ""
        img_m = re.search(r'<img[^>]+src="([^"]+)"', content, re.I)
        if img_m:
            logo = img_m.group(1)

        channels.append({"name": name, "url": url, "logo": logo})

    # Pattern 2: Any channel/watch/live links
    if not channels:
        for a in re.finditer(r'<a[^>]+href="([^"]*(?:channel|watch|live)[^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
            url = _abs(a.group(1))
            content = a.group(2)

            if url in seen:
                continue

            name = ""
            img_m = re.search(r'alt="([^"]+)"', content)
            if img_m:
                name = img_m.group(1)
            else:
                name_m = re.search(r'>([^<]+)<', content)
                if name_m:
                    name = name_m.group(1).strip()

            if not name or len(name) < 2:
                continue

            seen.add(url)

            logo = ""
            img_m = re.search(r'<img[^>]+src="([^"]+)"', content, re.I)
            if img_m:
                logo = img_m.group(1)

            channels.append({"name": name, "url": url, "logo": logo})

    return channels


def _get_default_countries():
    return [
        {"code": "US", "name": "United States"},
        {"code": "UK", "name": "United Kingdom"},
        {"code": "IN", "name": "India"},
        {"code": "CA", "name": "Canada"},
        {"code": "AU", "name": "Australia"},
        {"code": "DE", "name": "Germany"},
        {"code": "FR", "name": "France"},
        {"code": "IT", "name": "Italy"},
        {"code": "ES", "name": "Spain"},
        {"code": "BR", "name": "Brazil"},
        {"code": "MX", "name": "Mexico"},
        {"code": "JP", "name": "Japan"},
        {"code": "KR", "name": "South Korea"},
        {"code": "CN", "name": "China"},
        {"code": "RU", "name": "Russia"},
        {"code": "TR", "name": "Turkey"},
        {"code": "PK", "name": "Pakistan"},
        {"code": "BD", "name": "Bangladesh"},
        {"code": "NP", "name": "Nepal"},
        {"code": "LK", "name": "Sri Lanka"},
    ]


def _get_default_categories():
    return [
        {"slug": "entertainment", "name": "Entertainment"},
        {"slug": "news", "name": "News"},
        {"slug": "sports", "name": "Sports"},
        {"slug": "movies", "name": "Movies"},
        {"slug": "kids", "name": "Kids"},
        {"slug": "music", "name": "Music"},
        {"slug": "documentary", "name": "Documentary"},
        {"slug": "lifestyle", "name": "Lifestyle"},
        {"slug": "cooking", "name": "Cooking"},
        {"slug": "travel", "name": "Travel"},
        {"slug": "science", "name": "Science"},
        {"slug": "technology", "name": "Technology"},
        {"slug": "business", "name": "Business"},
        {"slug": "education", "name": "Education"},
        {"slug": "comedy", "name": "Comedy"},
        {"slug": "drama", "name": "Drama"},
        {"slug": "religious", "name": "Religious"},
        {"slug": "regional", "name": "Regional"},
    ]


def _get_default_channels():
    """Default channels when site is unavailable"""
    return [
        {"name": "BBC World News", "url": "https://vs-hls-push-ww-live.akamaized.net/x=4/i=urn:bbc:pips:service:bbc_news_channel_hd/t=3840/v=pv14/b=5070016/main.m3u8", "logo": "", "category": "news", "country": "uk"},
        {"name": "CNN International", "url": "https://cnn-cnninternational-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "news", "country": "us"},
        {"name": "Al Jazeera English", "url": "https://live-hls-web-aje.getaj.net/AJE/01.m3u8", "logo": "", "category": "news", "country": "qa"},
        {"name": "France 24 English", "url": "https://www.youtube.com/embed/Ap-UM1O9tI8", "logo": "", "category": "news", "country": "fr"},
        {"name": "DW News", "url": "https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/index.m3u8", "logo": "", "category": "news", "country": "de"},
        {"name": "NHK World Japan", "url": "https://nhkwlive-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp-en/index.m3u8", "logo": "", "category": "news", "country": "jp"},
        {"name": "Sky News", "url": "https://siloh.pluto.tv/lilo/production/SkyNews/master.m3u8", "logo": "", "category": "news", "country": "uk"},
        {"name": "Bloomberg", "url": "https://bloomberg-bloomberg-5-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "news", "country": "us"},
        {"name": "CGTN", "url": "https://news.cgtn.com/resource/live/english/cgtn-news.m3u8", "logo": "", "category": "news", "country": "cn"},
        {"name": "RT News", "url": "https://rt-glb.rttv.com/dvr/rtnews/playlist.m3u8", "logo": "", "category": "news", "country": "ru"},
        {"name": "Red Bull TV", "url": "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "Stadium", "url": "https://stadium-ringofrock-1.sinclair.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "Olympic Channel", "url": "https://ott-live.olympicchannel.com/out/u/OC1.m3u8", "logo": "", "category": "sports", "country": "int"},
        {"name": "FIFA TV", "url": "https://fifa-fifa-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "sports", "country": "int"},
        {"name": "NFL Channel", "url": "https://nfl-xumo.amagi.tv/playlist.m3u8", "logo": "", "category": "sports", "country": "us"},
        {"name": "Pluto TV Movies", "url": "https://siloh.pluto.tv/lilo/production/PlutoTV/master.m3u8", "logo": "", "category": "entertainment", "country": "us"},
        {"name": "PBS Kids", "url": "https://2-fss2-streamhoster.pluto.tv/lilo/production/PBSKids/master.m3u8", "logo": "", "category": "kids", "country": "us"},
        {"name": "Moonbug Kids", "url": "https://moonbug-rokuus.amagi.tv/playlist.m3u8", "logo": "", "category": "kids", "country": "us"},
        {"name": "Documentary+", "url": "https://documentaryplus-documentaryplus-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "documentary", "country": "us"},
        {"name": "Xplore", "url": "https://xplore-xplore-1-eu.rakuten.wurl.com/manifest/playlist.m3u8", "logo": "", "category": "documentary", "country": "us"},
        {"name": "NDTV India", "url": "https://ndtvindiaelemarchana.akamaized.net/hls/live/2003678/ndtvindia/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "Republic TV", "url": "https://weblive.republicworld.com/liveorigin/republictv/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "India Today", "url": "https://indiatodayelemarchana.akamaized.net/hls/live/2003678/indiatoday/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "Times Now", "url": "https://timesnow-lh.akamaihd.net/i/TNDelivery@344381/master.m3u8", "logo": "", "category": "news", "country": "in"},
        {"name": "Star Plus", "url": "https://starplus.akamaized.net/hls/live/2003678/starplus/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Zee TV", "url": "https://zee5.akamaized.net/hls/live/2003678/zeetv/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Sony TV", "url": "https://sony.akamaized.net/hls/live/2003678/sonytv/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Colors TV", "url": "https://colors.akamaized.net/hls/live/2003678/colorstv/master.m3u8", "logo": "", "category": "entertainment", "country": "in"},
        {"name": "Geo News", "url": "https://jk-live.cdn.jio.com/bpk-tv/Geo_News_MOB/Fallback/index.m3u8", "logo": "", "category": "news", "country": "pk"},
        {"name": "Hum TV", "url": "https://jk-live.cdn.jio.com/bpk-tv/Hum_TV_HD_MOB/Fallback/index.m3u8", "logo": "", "category": "entertainment", "country": "pk"},
        {"name": "ARY Digital", "url": "https://jk-live.cdn.jio.com/bpk-tv/ARY_Digital_MOB/Fallback/index.m3u8", "logo": "", "category": "entertainment", "country": "pk"},
        {"name": "KBS World", "url": "https://kbsworld-ott.akamaized.net/hls/live/2003459/kbsworld/01.m3u8", "logo": "", "category": "entertainment", "country": "kr"},
        {"name": "TRT World", "url": "https://tv-trtworld.live.trt.com.tr/master.m3u8", "logo": "", "category": "news", "country": "tr"},
    ]


def _get_default_radio():
    return [
        {"name": "SomaFM Groove Salad", "url": "https://ice1.somafm.com/groovesalad-128-mp3", "logo": ""},
        {"name": "SomaFM DEF CON", "url": "https://ice1.somafm.com/defcon-128-mp3", "logo": ""},
        {"name": "SomaFM Drone Zone", "url": "https://ice1.somafm.com/dronezone-128-mp3", "logo": ""},
        {"name": "SomaFM Secret Agent", "url": "https://ice1.somafm.com/secretagent-128-mp3", "logo": ""},
        {"name": "SomaFM Beat Blender", "url": "https://ice1.somafm.com/beatblender-128-mp3", "logo": ""},
        {"name": "SomaFM Vaporwaves", "url": "https://ice1.somafm.com/vaporwaves-128-mp3", "logo": ""},
        {"name": "SomaFM Space Station", "url": "https://ice1.somafm.com/spacestation-128-mp3", "logo": ""},
        {"name": "SomaFM Deep Space One", "url": "https://ice1.somafm.com/deepspaceone-128-mp3", "logo": ""},
        {"name": "SomaFM PopTron", "url": "https://ice1.somafm.com/poptron-128-mp3", "logo": ""},
        {"name": "SomaFM Lush", "url": "https://ice1.somafm.com/lush-128-mp3", "logo": ""},
        {"name": "SomaFM Fluid", "url": "https://ice1.somafm.com/fluid-128-mp3", "logo": ""},
        {"name": "SomaFM Suburbs of Goa", "url": "https://ice1.somafm.com/suburbsofgoa-128-mp3", "logo": ""},
        {"name": "SomaFM The Trip", "url": "https://ice1.somafm.com/thetrip-128-mp3", "logo": ""},
        {"name": "SomaFM Sonic Universe", "url": "https://ice1.somafm.com/sonicuniverse-128-mp3", "logo": ""},
        {"name": "SomaFM Dub Step Beyond", "url": "https://ice1.somafm.com/dubstepbeyond-128-mp3", "logo": ""},
        {"name": "SomaFM Folk Forward", "url": "https://ice1.somafm.com/folkforward-128-mp3", "logo": ""},
        {"name": "SomaFM Metal Detector", "url": "https://ice1.somafm.com/metaldetector-128-mp3", "logo": ""},
        {"name": "SomaFM Heavyweight Reggae", "url": "https://ice1.somafm.com/heavyweightreggae-256-mp3", "logo": ""},
    ]
