# -*- coding: utf-8 -*-
"""
StreamIMDB Scraper - Updated for Kodi 19+ (Python 3)
Fixed with proper patterns and multiple URL fallbacks
"""

import re
import urllib.request
import urllib.parse
import ssl

# Try multiple possible domains
BASE_DOMAINS = [
    "https://www.streamimdb.top",
    "https://streamimdb.top",
    "https://streamimdb.to",
    "https://www.streamimdb.to",
]

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

_working_base = None


def _find_working_base():
    """Find a working base URL"""
    global _working_base
    if _working_base:
        return _working_base

    for domain in BASE_DOMAINS:
        try:
            hdrs = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            req = urllib.request.Request(domain, headers=hdrs)
            resp = urllib.request.urlopen(req, context=_ctx, timeout=10)
            if resp.status == 200:
                _working_base = domain
                return domain
        except Exception:
            continue
    _working_base = BASE_DOMAINS[0]  # Default fallback
    return _working_base


def _fetch(url, headers=None):
    """Fetch URL content with fallback"""
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        resp = urllib.request.urlopen(req, context=_ctx, timeout=20)
        return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _abs(url, base=None):
    """Make URL absolute"""
    if not base:
        base = _find_working_base()
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http"):
        return url
    return urllib.parse.urljoin(base, url)


def _extract_items(html, kind="movie"):
    """Extract items from listing page - multiple pattern support"""
    items = []
    seen = set()

    # Pattern 1: article with card structure
    for article in re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL):
        # Try h3 > a pattern
        a = re.search(r'<h3[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', article, re.I)
        if not a:
            # Try any a with title
            a = re.search(r'<a[^>]+href="([^"]+)"[^>]*title="([^"]+)"', article, re.I)
        if not a:
            continue

        url = _abs(a.group(1))
        title = _clean_text(a.group(2))

        if url in seen or not title or len(title) < 3:
            continue
        seen.add(url)

        thumb = ""
        img_m = re.search(r'<img[^>]+src="([^"]+)"', article, re.I)
        if img_m:
            thumb = img_m.group(1)

        items.append({"title": title, "url": url, "thumb": thumb, "kind": kind})

    # Pattern 2: div.movie or div.item containers
    if not items:
        for div in re.findall(r'<div[^>]*class="[^"]*(?:movie|item|card)[^"]*"[^>]*>.*?</div>', html, re.DOTALL):
            a = re.search(r'<a[^>]+href="([^"]+)"[^>]*>', div, re.I)
            if not a:
                continue
            url = _abs(a.group(1))

            title = ""
            tm = re.search(r'title="([^"]+)"', div)
            if tm:
                title = tm.group(1)
            else:
                tm = re.search(r'alt="([^"]+)"', div)
                if tm:
                    title = tm.group(1)

            if url in seen or not title or len(title) < 3:
                continue
            seen.add(url)

            thumb = ""
            img_m = re.search(r'<img[^>]+src="([^"]+)"', div, re.I)
            if img_m:
                thumb = img_m.group(1)

            items.append({"title": title, "url": url, "thumb": thumb, "kind": kind})

    # Pattern 3: Look for any links with movie/show patterns
    if not items:
        for a in re.finditer(r'<a[^>]+href="([^"]*(?:movie|tv-show|series)/[^"]+)"[^>]*>(?:\s*<[^>]+>)*([^<]+)', html):
            url = _abs(a.group(1))
            title = _clean_text(a.group(2))
            if url in seen or not title or len(title) < 3:
                continue
            seen.add(url)
            items.append({"title": title, "url": url, "thumb": "", "kind": kind})

    return items


def get_latest(page=1):
    """Get latest movies"""
    base = _find_working_base()
    if page <= 1:
        url = base + "/movies/"
    else:
        url = base + f"/movies/page/{page}/"

    html = _fetch(url)
    if not html:
        # Try alternative URL patterns
        if page <= 1:
            url = base + "/"
        else:
            url = base + f"/page/{page}/"
        html = _fetch(url)

    if not html:
        return []

    return _extract_items(html)


def get_tv_shows(page=1):
    """Get latest TV shows"""
    base = _find_working_base()
    if page <= 1:
        url = base + "/tv-shows/"
    else:
        url = base + f"/tv-shows/page/{page}/"

    html = _fetch(url)
    if not html:
        if page <= 1:
            url = base + "/tv/"
        else:
            url = base + f"/tv/page/{page}/"
        html = _fetch(url)

    if not html:
        return []

    return _extract_items(html, kind="tv")


def get_tv_by_genre(genre, page=1):
    """Get TV shows by genre"""
    base = _find_working_base()
    if page <= 1:
        url = base + f"/genre/{genre}/"
    else:
        url = base + f"/genre/{genre}/page/{page}/"

    html = _fetch(url)
    if not html:
        return []

    return _extract_items(html)


def search(query, page=1):
    """Search movies using site search"""
    base = _find_working_base()

    # Try search URL
    search_url = base + "/?s=" + urllib.parse.quote(query)
    html = _fetch(search_url)

    if html:
        results = _extract_items(html)
        if results:
            return results

    # Fallback to sitemap search
    results = []
    for sitemap in ["/sitemap.xml", "/sitemap_index.xml", "/post-sitemap.xml"]:
        xml = _fetch(base + sitemap)
        if xml:
            urls = re.findall(r"<loc>([^<]+)</loc>", xml)
            q = query.lower()
            for u in urls:
                if q in u.lower() and ("/movies/" in u or "/tv-shows/" in u):
                    title = _slug_to_title(u)
                    results.append({"title": title, "url": u, "thumb": ""})
            if results:
                break

    return results


def search_tv(query, page=1):
    """Search TV shows"""
    base = _find_working_base()

    # Try search URL with tv filter
    search_url = base + "/tv-shows/?s=" + urllib.parse.quote(query)
    html = _fetch(search_url)

    if not html:
        search_url = base + "/?s=" + urllib.parse.quote(query) + "&post_type=tv_show"
        html = _fetch(search_url)

    if html:
        results = _extract_items(html, kind="tv")
        if results:
            return results

    # Fallback to sitemap
    results = []
    xml = _fetch(base + "/sitemap.xml")
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
    if not pm:
        pm = re.search(r'<img[^>]+class="[^"]*poster[^"]*"[^>]+src=["\']([^"\']+)["\']', html, re.I)
    if pm:
        poster = pm.group(1)

    plot = ""
    dm = re.search(r'class="[^"]*(?:description|summary|plot)[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if dm:
        plot = _clean_text(dm.group(1))

    # Extract embed/player sources
    sources = []
    seen = set()

    # Pattern 1: data-source attribute
    for emb in re.findall(r'data-source="([^"]+)"', html):
        emb = _abs(emb, url)
        if emb.startswith("http") and emb not in seen:
            seen.add(emb)
            host = urllib.parse.urlparse(emb).netloc.replace("www.", "")
            sources.append({"label": f"Source ({host})", "url": emb, "host": host})

    # Pattern 2: iframes
    for ifr in re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.I):
        ifr = _abs(ifr, url)
        if ifr.startswith("http") and ifr not in seen:
            seen.add(ifr)
            host = urllib.parse.urlparse(ifr).netloc.replace("www.", "")
            sources.append({"label": f"Source ({host})", "url": ifr, "host": host})

    # Pattern 3: hdm2.ink links
    for emb in re.findall(r'(https://hdm2\.ink/play\?v=[^"\'\s<>]+)', html):
        if emb not in seen:
            seen.add(emb)
            sources.append({"label": "HD Source", "url": emb, "host": "hdm2.ink"})

    return {
        "title": title,
        "poster": poster,
        "plot": plot,
        "embed": sources[0]["url"] if sources else "",
        "sources": sources,
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

    # Extract seasons/episodes - multiple patterns
    seasons = {}

    # Pattern 1: data attributes
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

    # Pattern 2: Look for episode links
    if not seasons:
        for ep_link in re.finditer(r'href="([^"]*episode[^"]*)"[^>]*>([^<]*episode[^<]*)', html, re.I):
            ep_url = _abs(ep_link.group(1))
            ep_title = _clean_text(ep_link.group(2))
            # Try to extract season/episode numbers
            nums = re.findall(r'\d+', ep_title)
            if len(nums) >= 2:
                season = int(nums[0])
                episode = int(nums[1])
            else:
                season = 1
                episode = len(seasons.get(1, [])) + 1
            seasons.setdefault(season, []).append({
                "season": season,
                "episode": episode,
                "title": ep_title,
                "url": ep_url,
            })

    return {"title": title, "poster": poster, "seasons": seasons}


def get_episodes(url, season):
    """Get episodes for a season"""
    detail = get_tv_detail(url)
    if not detail:
        return []
    return detail.get("seasons", {}).get(int(season), [])


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
