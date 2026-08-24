# -*- coding: utf-8 -*-
"""
StreamIMDB Scraper - Updated for Kodi 19+ (Python 3)
"""

import re
import urllib.request
import urllib.parse
import ssl

BASE = "https://www.streamimdb.top"

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


def _abs(url, base=BASE):
    """Make URL absolute"""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http"):
        return url
    return urllib.parse.urljoin(base, url)


def get_latest(page=1):
    """Get latest movies and TV shows"""
    if page <= 1:
        url = BASE + "/movies/"
    else:
        url = BASE + f"/movies/page/{page}/"

    html = _fetch(url)
    if not html:
        return []

    return _extract_items(html)


def get_tv_shows(page=1):
    """Get latest TV shows"""
    if page <= 1:
        url = BASE + "/tv-shows/"
    else:
        url = BASE + f"/tv-shows/page/{page}/"

    html = _fetch(url)
    if not html:
        return []

    return _extract_items(html, kind="tv")


def get_tv_by_genre(genre, page=1):
    """Get TV shows by genre"""
    if page <= 1:
        url = BASE + f"/genre/{genre}/"
    else:
        url = BASE + f"/genre/{genre}/page/{page}/"

    html = _fetch(url)
    if not html:
        return []

    return _extract_items(html)


def search(query, page=1):
    """Search movies"""
    results = []
    # Search via sitemap if available, or use site search
    xml = _fetch(BASE + "/sitemap.xml")
    if xml:
        urls = re.findall(r"<loc>([^<]+)</loc>", xml)
        q = query.lower()
        for u in urls:
            if q in u.lower() and "/movies/" in u:
                title = _slug_to_title(u)
                results.append({"title": title, "url": u, "thumb": ""})
    return results


def search_tv(query, page=1):
    """Search TV shows"""
    results = []
    xml = _fetch(BASE + "/sitemap.xml")
    if xml:
        urls = re.findall(r"<loc>([^<]+)</loc>", xml)
        q = query.lower()
        for u in urls:
            if q in u.lower() and "/tv-shows/" in u:
                title = _slug_to_title(u)
                results.append({"title": title, "url": u, "thumb": ""})
    return results


def get_detail(url):
    """Get movie/show details"""
    html = _fetch(url)
    if not html:
        return None

    title = ""
    tm = re.search(r'<h1[^>]*>([^<]+)<', html, re.I)
    if tm:
        title = _clean_text(tm.group(1))

    poster = ""
    pm = re.search(r'property="og:image"[^>]*content="([^"]+)"', html)
    if pm:
        poster = pm.group(1)

    plot = ""
    dm = re.search(r'class="[^"]*(?:description|summary|plot)[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if dm:
        plot = _clean_text(dm.group(1))

    # Extract embed/player
    embed = ""
    emb_m = re.search(r'data-embed=["\']([^"\']+)["\']', html)
    if emb_m:
        embed = emb_m.group(1)
    else:
        ifr = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.I)
        if ifr:
            embed = ifr.group(1)

    return {
        "title": title,
        "poster": poster,
        "plot": plot,
        "embed": embed,
        "sources": [{"label": "Play", "url": embed}] if embed else [],
    }


def get_tv_detail(url):
    """Get TV show details with seasons/episodes"""
    html = _fetch(url)
    if not html:
        return None

    title = ""
    tm = re.search(r'<h1[^>]*>([^<]+)<', html, re.I)
    if tm:
        title = _clean_text(tm.group(1))

    poster = ""
    pm = re.search(r'property="og:image"[^>]*content="([^"]+)"', html)
    if pm:
        poster = pm.group(1)

    # Extract seasons/episodes
    seasons = {}
    for ep_match in re.finditer(
        r'data-season=["\'](\d+)["\'][^>]*data-episode=["\'](\d+)["\'][^>]*data-url=["\']([^"\']+)["\']',
        html,
    ):
        season = int(ep_match.group(1))
        episode = int(ep_match.group(2))
        ep_url = ep_match.group(3)
        seasons.setdefault(season, []).append({
            "season": season,
            "episode": episode,
            "title": f"Episode {episode}",
            "url": ep_url,
        })

    return {"title": title, "poster": poster, "seasons": seasons}


def get_episodes(url, season):
    """Get episodes for a season"""
    detail = get_tv_detail(url)
    if not detail:
        return []
    return detail.get("seasons", {}).get(int(season), [])


def _extract_items(html, kind="movie"):
    """Extract items from listing page"""
    items = []
    seen = set()

    for container in re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL):
        a = re.search(r'<a[^>]+href="([^"]+)"[^>]*title="([^"]*)"', container)
        if not a:
            a = re.search(r'<a[^>]+class="[^"]*poster[^"]*"[^>]+href="([^"]+)"', container)
            if a:
                url = _abs(a.group(1))
                title = _slug_to_title(url)
            else:
                continue
        else:
            url = _abs(a.group(1))
            title = a.group(2).strip() or _slug_to_title(url)

        if url in seen:
            continue
        seen.add(url)

        img_m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', container, re.I)
        thumb = img_m.group(1) if img_m else ""

        items.append({"title": title, "url": url, "thumb": thumb, "kind": kind})

    return items


def _slug_to_title(url):
    """Convert URL slug to title"""
    path = urllib.parse.urlparse(url).path
    seg = path.rstrip("/").split("/")[-1]
    seg = re.sub(r"\.html?$", "", seg)
    seg = re.sub(r"^\d+-", "", seg)
    seg = seg.replace("-", " ")
    return seg.title().strip()


def _clean_text(txt):
    """Clean HTML text"""
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt
