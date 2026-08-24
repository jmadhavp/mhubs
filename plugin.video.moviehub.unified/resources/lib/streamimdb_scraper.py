# -*- coding: utf-8 -*-
"""
StreamIMDB Scraper - https://streamimdb.ru
Cineby/VidAPI theme with /movie/ and /tv/ URLs
"""

import re
import urllib.request
import urllib.parse
import ssl

BASE = "https://streamimdb.ru"

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


def get_latest(page=1):
    """Get latest movies"""
    if page <= 1:
        url = BASE + "/movie/"
    else:
        url = BASE + f"/movie/page/{page}/"

    html = _fetch(url)
    if not html:
        return []

    return _extract_items(html, kind="movie")


def get_tv_shows(page=1):
    """Get latest TV shows"""
    if page <= 1:
        url = BASE + "/tv/"
    else:
        url = BASE + f"/tv/page/{page}/"

    html = _fetch(url)
    if not html:
        return []

    return _extract_items(html, kind="tv")


def get_movie_by_genre(genre, page=1):
    """Get movies by genre"""
    if page <= 1:
        url = BASE + f"/genre/{genre}/"
    else:
        url = BASE + f"/genre/{genre}/page/{page}/"

    html = _fetch(url)
    if not html:
        return []

    return _extract_items(html, kind="movie")


def search(query, page=1):
    """Search movies and TV shows"""
    q = urllib.parse.quote(query)
    url = BASE + f"/?s={q}"
    if page > 1:
        url = BASE + f"/page/{page}/?s={q}"

    html = _fetch(url)
    if not html:
        return []

    return _extract_items(html)


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
        pm = re.search(r'<img[^>]+src="([^"]+)"[^>]*class="[^"]*poster[^"]*"', html, re.I)
    if pm:
        poster = pm.group(1)

    plot = ""
    dm = re.search(r'class="[^"]*(?:description|summary|plot)[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if dm:
        plot = _clean_text(dm.group(1))

    # Extract embed sources
    sources = []
    seen = set()

    # data-embed pattern (Cineby/VidAPI)
    for m in re.finditer(r'data-embed="(/embed/(?:movie|tv)/[^"]+)"[^>]*data-title="([^"]+)"', html):
        emb = _abs(m.group(1))
        name = m.group(2)
        if emb not in seen:
            seen.add(emb)
            sources.append({"label": name or "Stream", "url": emb, "host": "streamimdb"})

    # iframe embeds
    for ifr in re.findall(r'<iframe[^>]*src="([^"]+)"', html, re.I):
        ifr = _abs(ifr, url)
        if ifr.startswith("http") and ifr not in seen:
            seen.add(ifr)
            host = urllib.parse.urlparse(ifr).netloc.replace("www.", "")
            sources.append({"label": f"Source ({host})", "url": ifr, "host": host})

    # data-source
    for emb in re.findall(r'data-source="([^"]+)"', html):
        emb = _abs(emb, url)
        if emb.startswith("http") and emb not in seen:
            seen.add(emb)
            host = urllib.parse.urlparse(emb).netloc.replace("www.", "")
            sources.append({"label": f"Source ({host})", "url": emb, "host": host})

    return {"title": title, "poster": poster, "plot": plot, "sources": sources}


def get_tv_detail(url):
    """Get TV show details with seasons"""
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

    # Pattern: /tv/<slug>/season/<n>/episode/<n>
    for ep in re.finditer(r'href="(/tv/[^"]+/season/(\d+)/episode/(\d+))"[^>]*>([^<]*)', html):
        s_num = int(ep.group(2))
        e_num = int(ep.group(3))
        ep_url = _abs(ep.group(1))
        ep_title = _clean_text(ep.group(4)) or f"Episode {e_num}"
        seasons.setdefault(s_num, []).append({
            "season": s_num,
            "episode": e_num,
            "title": ep_title,
            "url": ep_url,
        })

    # Pattern: season links
    if not seasons:
        for s_link in re.finditer(r'href="(/tv/[^"]+/season/(\d+))"[^>]*>', html):
            s_num = int(s_link.group(2))
            seasons.setdefault(s_num, [])

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

    # Pattern 1: /movie/ or /tv/ links with card structure
    for a in re.finditer(r'<a[^>]+href="((?:/movie/|/tv/)[^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
        url = _abs(a.group(1))
        content = a.group(2)

        if url in seen:
            continue

        # Extract title
        title = ""
        tm = re.search(r'alt="([^"]+)"', content)
        if tm:
            title = tm.group(1)
        else:
            tm = re.search(r'>([^<]+)</', content)
            if tm:
                title = _clean_text(tm.group(1))

        if not title or len(title) < 3:
            title = _slug_to_title(url)

        seen.add(url)

        thumb = ""
        img_m = re.search(r'<img[^>]+src="([^"]+)"', content, re.I)
        if img_m:
            thumb = img_m.group(1)

        items.append({"title": title, "url": url, "thumb": thumb, "kind": kind})

    # Pattern 2: data-embed slides
    if not items:
        for m in re.finditer(r'data-embed="(/embed/(?:movie|tv)/[^"]+)"[^>]*data-title="([^"]+)"', html):
            emb_url = _abs(m.group(1))
            title = m.group(2)
            # Convert embed URL to detail URL
            detail_url = re.sub(r"/embed/", "/", emb_url)
            if detail_url not in seen:
                seen.add(detail_url)
                items.append({"title": title, "url": detail_url, "thumb": "", "kind": kind})

    return items


def _slug_to_title(url):
    path = urllib.parse.urlparse(url).path
    seg = path.rstrip("/").split("/")[-1]
    seg = re.sub(r"^\d+-", "", seg)
    seg = seg.replace("-", " ")
    return seg.title().strip()


def _clean_text(txt):
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt
