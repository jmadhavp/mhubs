# -*- coding: utf-8 -*-
"""
MovieHub Scraper - https://hdmovie2a.bar
Original MovieHub site with dooplay WordPress theme
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
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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


def _extract_listing(html):
    """Extract movies from listing page"""
    items = []
    seen = set()

    # Pattern 1: article.card with poster-link
    for article in re.findall(r'<article[^>]*class="[^"]*card[^"]*"[^>]*>.*?</article>', html, re.DOTALL):
        a = re.search(r'<a[^>]*class="[^"]*poster-link[^"]*"[^>]+href="([^"]+)"[^>]*aria-label="([^"]*)"', article)
        if not a:
            a = re.search(r'<a[^>]+href="([^"]+)"[^>]*aria-label="([^"]*)"', article)
        if not a:
            continue

        url = _abs(a.group(1))
        title = a.group(2).strip() or _slug_to_title(url)

        if url in seen or not title:
            continue
        seen.add(url)

        thumb = ""
        img_m = re.search(r'<img[^>]+src="([^"]+)"', article, re.I)
        if img_m:
            thumb = img_m.group(1)

        year = ""
        ym = re.search(r"\((\d{4})\)", title)
        if ym:
            year = ym.group(1)

        items.append({"title": title, "url": url, "thumb": thumb, "year": year})

    # Pattern 2: h3.card-title > a
    if not items:
        for article in re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL):
            a = re.search(r'<h3[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', article, re.I)
            if not a:
                continue
            url = _abs(a.group(1))
            title = _clean_text(a.group(2))
            if url in seen or not title:
                continue
            seen.add(url)
            thumb = ""
            img_m = re.search(r'<img[^>]+src="([^"]+)"', article, re.I)
            if img_m:
                thumb = img_m.group(1)
            items.append({"title": title, "url": url, "thumb": thumb, "year": ""})

    return items


def get_latest(page=1):
    if page <= 1:
        url = BASE + "/movies/"
    else:
        url = BASE + f"/movies/page/{page}/"

    html = _fetch(url)
    if not html:
        return []
    return _extract_listing(html)


def get_genre(genre, page=1):
    if page <= 1:
        url = BASE + f"/genre/{genre}/"
    else:
        url = BASE + f"/genre/{genre}/page/{page}/"

    html = _fetch(url)
    if not html:
        return []
    return _extract_listing(html)


def search(query, page=1):
    q = urllib.parse.quote(query)
    url = BASE + f"/?s={q}"
    if page > 1:
        url = BASE + f"/page/{page}/?s={q}"

    html = _fetch(url)
    if not html:
        return []

    results = _extract_listing(html)
    if results:
        return results

    # Fallback to sitemap
    xml = _fetch(SITEMAP)
    if not xml:
        return []
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    sitemap_results = []
    for u in urls:
        if query.lower() in u.lower():
            sitemap_results.append({"title": _slug_to_title(u), "url": u, "thumb": "", "year": ""})
    return sitemap_results


def get_detail(url):
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
        pm = re.search(r'<img[^>]+class="[^"]*poster[^"]*"[^>]+src="([^"]+)"', html, re.I)
    if pm:
        poster = pm.group(1)

    plot = ""
    dm = re.search(r'class="[^"]*(?:description|summary|plot|wp-content)[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if dm:
        plot = _clean_text(dm.group(1))

    sources = []
    seen = set()

    # data-source with title
    for m in re.finditer(r'<a[^>]*data-source="([^"]+)"[^>]*>.*?<span class="title">([^<]+)</span>', html, re.DOTALL):
        emb = m.group(1).replace("&amp;", "&")
        name = m.group(2).strip()
        if emb not in seen:
            seen.add(emb)
            sources.append({"label": name or "Stream", "url": emb, "host": "hdm2.ink"})

    # hdm2.ink play links
    for emb in re.findall(r'(https://hdm2\.ink/play\?v=[^"\'\s<>]+)', html):
        if emb not in seen:
            seen.add(emb)
            sources.append({"label": "HD Source", "url": emb, "host": "hdm2.ink"})

    # data-source generic
    for emb in re.findall(r'data-source="([^"]+)"', html):
        emb = _abs(emb, url)
        if emb.startswith("http") and emb not in seen:
            seen.add(emb)
            host = urllib.parse.urlparse(emb).netloc.replace("www.", "")
            sources.append({"label": f"Source ({host})", "url": emb, "host": host})

    # iframes
    for ifr in re.findall(r'<iframe[^>]*src="([^"]+)"', html, re.I):
        ifr = _abs(ifr, url)
        if ifr.startswith("http") and ifr not in seen:
            seen.add(ifr)
            host = urllib.parse.urlparse(ifr).netloc.replace("www.", "")
            sources.append({"label": f"Source ({host})", "url": ifr, "host": host})

    return {"title": title, "poster": poster, "plot": plot, "sources": sources}


def get_genres():
    return [
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


def _slug_to_title(url):
    path = urllib.parse.urlparse(url).path
    seg = path.rstrip("/").split("/")[-1]
    seg = re.sub(r"\.html?$", "", seg)
    seg = re.sub(r"^\d+-", "", seg)
    seg = seg.replace("-", " ")
    return seg.title().strip()


def _clean_text(txt):
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt
