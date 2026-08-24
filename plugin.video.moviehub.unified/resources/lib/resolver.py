# -*- coding: utf-8 -*-
"""
Universal Resolver - Updated for Kodi 19+ (Python 3)
"""

import re
import urllib.request
import urllib.parse
import html
import ssl

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
        resp = urllib.request.urlopen(req, context=_ctx, timeout=20)
        return resp.read().decode("utf-8", errors="ignore"), resp.geturl()
    except Exception:
        return "", url


def resolve(url):
    """Main resolve function"""
    if not url:
        return None

    # Already direct media file
    low = url.lower().split("?")[0].split("#")[0]
    if low.endswith(".m3u8"):
        return {"url": url, "kind": "m3u8", "headers": {}}
    if low.endswith(".mp4"):
        return {"url": url, "kind": "mp4", "headers": {}}
    if low.endswith(".mkv"):
        return {"url": url, "kind": "mkv", "headers": {}}

    # YouTube
    yt = _resolve_youtube(url)
    if yt:
        return yt

    # hdm2.ink
    if "hdm2.ink" in url:
        return _resolve_hdm2ink(url)

    # prvs.top / abyss.to
    if "prvs.top" in url or "abyss.to" in url:
        return _resolve_prvs(url)

    # Generic scan
    return _generic_resolve(url)


def _resolve_youtube(url):
    """Resolve YouTube URLs"""
    url_unquoted = urllib.parse.unquote(url)
    m = re.search(r'(?:youtube\.com/(?:embed/|watch\?v=)|youtu\.be/)[%5B\[]*([A-Za-z0-9_-]{6,})', url_unquoted, re.I)
    if m:
        vid = m.group(1)
        return {
            "url": f"plugin://plugin.video.youtube/play/?video_id={vid}",
            "kind": "youtube",
            "headers": {},
        }
    return None


def _resolve_hdm2ink(url):
    """Resolve hdm2.ink embed URLs"""
    for ref in ("https://hdm2.ink/", "https://hdmovie2a.bar/"):
        page, final = _fetch(url, headers={"Referer": ref, "Origin": "https://hdm2.ink"})
        if page and "data-stream-url" in page:
            m = re.search(r'data-stream-url=["\']([^"\']+)["\']', page)
            if m:
                raw = html.unescape(m.group(1))
                stream = raw if raw.startswith("http") else "https://hdm2.ink" + raw
                resp, _ = _fetch(stream, headers={"Referer": final or url, "Origin": "https://hdm2.ink"})
                if resp and (resp.lstrip().startswith("#EXTM3U") or "#EXT" in resp):
                    return {"url": stream, "kind": "m3u8", "headers": {"Referer": final or url, "Origin": "https://hdm2.ink"}}
    return None


def _resolve_prvs(url):
    """Resolve prvs.top / abyss.to embed URLs"""
    page, final = _fetch(url, headers={"Referer": "https://hdmovie2a.bar/"})
    if not page:
        return None

    # Look for data-stream-url
    m = re.search(r'data-stream-url=["\']([^"\']+)["\']', page)
    if m:
        stream = html.unescape(m.group(1))
        if not stream.startswith("http"):
            stream = "https://prvs.top" + stream
        return {"url": stream, "kind": "m3u8", "headers": {"Referer": final or url}}

    # Generic scan for m3u8
    for m in re.findall(r'[^\s"\'<>]+\.m3u8[^\s"\'<>]*', page):
        return {"url": m, "kind": "m3u8", "headers": {"Referer": final or url}}

    return None


def _generic_resolve(url):
    """Generic URL resolution by scanning page for media"""
    page, final = _fetch(url)
    if not page:
        return None

    # Scan for m3u8
    for m in re.findall(r'[^\s"\'<>]+\.m3u8[^\s"\'<>]*', page):
        if m.startswith("http"):
            return {"url": m, "kind": "m3u8", "headers": {"Referer": final or url}}

    # Scan for mp4
    for m in re.findall(r'[^\s"\'<>]+\.mp4[^\s"\'<>]*', page):
        if m.startswith("http"):
            return {"url": m, "kind": "mp4", "headers": {"Referer": final or url}}

    # Scan for file: variable
    for m in re.findall(r'(?:file|src|url)\s*[:=]\s*["\']([^"\']+)["\']', page, re.I):
        if m.startswith("http") and not m.endswith((".css", ".js", ".png", ".jpg")):
            return {"url": m, "kind": "mp4", "headers": {"Referer": final or url}}

    # Follow iframes
    for ifr in re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', page, re.I):
        if ifr.startswith("http"):
            result = resolve(ifr)
            if result:
                return result

    return {"url": url, "kind": "unresolved", "headers": {}}
