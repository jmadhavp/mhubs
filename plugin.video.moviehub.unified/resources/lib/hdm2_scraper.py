# -*- coding: utf-8 -*-
"""
HDMovie2 Scraper - Updated for Kodi 19+ (Python 3)
"""

import re
import urllib.request
import urllib.parse
import ssl

BASE = "https://hdmovie2a.bar"
SITEMAP = BASE + "/movies-sitemap.xml"

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
    """Get latest movies"""
    if page <= 1:
        url = BASE + "/movies/"
    else:
        url = BASE + f"/movies/page/{page}/"

    html = _fetch(url)
    if not html:
        return []

    movies = []
    seen = set()

    # Extract movie containers
    containers = re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL)
    if not containers:
        containers = re.split(r'(?=<a class="poster-link")', html)

    for container in containers:
        a = re.search(r'<a class="poster-link" href="([^"]+)"[^>]*aria-label="([^"]*)"', container)
        if not a:
            continue
        url = _abs(a.group(1))
        if url in seen:
            continue
        seen.add(url)
        title = a.group(2).strip()
        if not title:
            title = _slug_to_title(url)
        img_m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', container, re.I)
        thumb = img_m.group(1) if img_m else ""
        movies.append({"title": title, "url": url, "thumb": thumb})

    return movies


def get_genre(genre, page=1):
    """Get movies by genre"""
    if page <= 1:
        url = BASE + f"/genre/{genre}/"
    else:
        url = BASE + f"/genre/{genre}/page/{page}/"

    html = _fetch(url)
    if not html:
        return []

    movies = []
    seen = set()

    for container in re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL):
        a = re.search(r'<a class="poster-link" href="([^"]+)"[^>]*aria-label="([^"]*)"', container)
        if not a:
            continue
        url = _abs(a.group(1))
        if url in seen:
            continue
        seen.add(url)
        title = a.group(2).strip() or _slug_to_title(url)
        img_m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', container, re.I)
        thumb = img_m.group(1) if img_m else ""
        movies.append({"title": title, "url": url, "thumb": thumb})

    return movies


def get_by_year(year, page=1):
    """Get movies by year"""
    if page <= 1:
        url = BASE + f"/release/{year}/"
    else:
        url = BASE + f"/release/{year}/page/{page}/"

    html = _fetch(url)
    if not html:
        return []

    movies = []
    seen = set()

    for container in re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL):
        a = re.search(r'<a class="poster-link" href="([^"]+)"[^>]*aria-label="([^"]*)"', container)
        if not a:
            continue
        url = _abs(a.group(1))
        if url in seen:
            continue
        seen.add(url)
        title = a.group(2).strip() or _slug_to_title(url)
        img_m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', container, re.I)
        thumb = img_m.group(1) if img_m else ""
        movies.append({"title": title, "url": url, "thumb": thumb})

    return movies


def search(query, page=1):
    """Search movies via sitemap"""
    xml = _fetch(SITEMAP)
    if not xml:
        return []

    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    q = query.lower()
    results = []
    for u in urls:
        if q in u.lower():
            title = _slug_to_title(u)
            results.append({"title": title, "url": u, "thumb": ""})
    return results


def get_detail(url):
    """Get movie details and sources"""
    html = _fetch(url)
    if not html:
        return None

    # Extract title
    title = ""
    tm = re.search(r'<h1[^>]*>([^<]+)<', html, re.I)
    if tm:
        title = _clean_text(tm.group(1))

    # Extract poster
    poster = ""
    pm = re.search(r'<img[^>]+class="[^"]*poster[^"]*"[^>]+src=["\']([^"\']+)["\']', html, re.I)
    if not pm:
        pm = re.search(r'property="og:image"[^>]*content="([^"]+)"', html)
    if pm:
        poster = pm.group(1)

    # Extract plot
    plot = ""
    dm = re.search(r'class="[^"]*description[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if dm:
        plot = _clean_text(dm.group(1))

    # Extract sources
    sources = []
    seen = set()

    # hdm2.ink sources
    for emb in re.findall(r'https://hdm2\.ink/play\?v=[^"\'\s<>]+', html):
        if emb not in seen:
            seen.add(emb)
            sources.append({"label": "HD Source (hdm2.ink)", "url": emb, "host": "hdm2.ink"})

    # data-source / data-embed
    for emb in re.findall(r'data-(?:source|embed|link)=["\']([^"\']+)["\']', html):
        emb = _abs(emb, url)
        if emb.startswith("http") and emb not in seen:
            seen.add(emb)
            host = urllib.parse.urlparse(emb).netloc.replace("www.", "")
            sources.append({"label": f"Source ({host})", "url": emb, "host": host})

    # iframes
    for ifr in re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.I):
        ifr = _abs(ifr, url)
        if ifr.startswith("http") and ifr not in seen:
            seen.add(ifr)
            host = urllib.parse.urlparse(ifr).netloc.replace("www.", "")
            sources.append({"label": f"Source ({host})", "url": ifr, "host": host})

    return {"title": title, "poster": poster, "plot": plot, "sources": sources}


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
