# -*- coding: utf-8 -*-
"""
resolver.py - Universal stream resolver.

Given an embed / player URL (extracted by a site scraper) this module tries
to return a *directly playable* stream URL (HLS .m3u8 or progressive .mp4).

It uses a layered strategy:
  1. If the URL is already a direct media file, return it.
  2. Try a host-specific resolver (filemoon, dood, streamwish, filelions,
     vidhide, mixdrop, streamtape, mp4upload, youtube, plus the custom
     hosts found on the partner sites: hdm2.ink, kayel/gxplayer, indistream).
  3. Fall back to a generic scanner that fetches the page (and any iframe),
     then hunts for m3u8 / mp4 / player JSON / source variables.

Everything degrades gracefully: if nothing playable is found the original
embed URL is returned marked as "unresolved" so the UI can still show it.
"""
import re
import json
import html
import urllib.parse

from common import log, Net

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
RE_M3U8 = re.compile(r'https?://[^\s"\'<>\\]+?\.m3u8(?:\?[^\s"\'<>]*)?', re.I)
RE_MP4 = re.compile(r'https?://[^\s"\'<>\\]+?\.mp4(?:\?[^\s"\'<>]*)?', re.I)
RE_SRC_VAR = re.compile(
    r'''(?:file|src|hls|url|source|video|stream|playlist|manifest)\s*[:=]\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']''',
    re.I,
)
RE_JSON_SOURCES = re.compile(r'sources\s*:\s*(\[.*?\])', re.I | re.DOTALL)
RE_FILE_VAR = re.compile(r'["\']file["\']\s*:\s*["\']([^"\']+)["\']', re.I)

QUALITY_ORDER = ["1080", "720", "480", "360", "240", "144"]


def _host(url):
    try:
        return urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _abs(url, base):
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http"):
        return url
    return urllib.parse.urljoin(base, url)


def _quality_of(url):
    for q in QUALITY_ORDER:
        if re.search(r"[._-]?%s[pP]" % q, url):
            return int(q)
    return 0


def pick_quality(urls, preferred="Auto"):
    """Given a list of media urls, return the one matching `preferred`
    resolution, else the highest available."""
    if not urls:
        return None
    if preferred and preferred != "Auto":
        wanted = re.sub(r"[^0-9]", "", preferred)
        for u in urls:
            if wanted and re.search(r"[._-]?%s[pP]" % wanted, u):
                return u
    # highest quality first
    return sorted(urls, key=_quality_of, reverse=True)[0]


# ---------------------------------------------------------------------------
# Generic scanner (the workhorse)
# ---------------------------------------------------------------------------
def _scan_html(html, base):
    found = []
    for m in RE_M3U8.findall(html or ""):
        found.append(_abs(m, base))
    for m in RE_MP4.findall(html or ""):
        found.append(_abs(m, base))
    for m in RE_SRC_VAR.findall(html or ""):
        found.append(_abs(m, base))
    for m in RE_FILE_VAR.findall(html or ""):
        u = m.replace("\\/", "/")
        if u.startswith("http"):
            found.append(u)
    # try to parse a JS "sources" array of {file:...}
    for block in RE_JSON_SOURCES.findall(html or ""):
        for fm in re.findall(r'file\s*:\s*["\']([^"\']+)["\']', block):
            u = fm.replace("\\/", "/")
            if u.startswith("http"):
                found.append(u)
    # de-dupe preserving order
    seen, out = set(), []
    for u in found:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _generic_resolve(url, net):
    """Fetch the page (and any iframe) and scan for media urls."""
    media = []
    try:
        html, final, _ = net.get(url, headers={"Referer": url})
    except Exception as e:
        log("generic fetch failed %s: %s" % (url, e), "error")
        return []
    base = final or url
    media += _scan_html(html, base)
    # follow iframes (one level)
    iframes = re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', html or "", re.I)
    for ifr in iframes[:3]:
        iu = _abs(ifr, base)
        if iu == url:
            continue
        try:
            ih, ifinal, _ = net.get(iu, headers={"Referer": base})
            media += _scan_html(ih, ifinal or iu)
        except Exception as e:
            log("iframe fetch failed %s: %s" % (iu, e), "debug")
    return media


# ---------------------------------------------------------------------------
# Host specific resolvers
# ---------------------------------------------------------------------------
def _resolve_youtube(url, net):
    url_unquoted = urllib.parse.unquote(url)
    m = re.search(r'(?:youtube\.com/(?:embed/|watch\?v=)|youtu\.be/)[%5B\[]*([A-Za-z0-9_-]{6,})', url_unquoted, re.I)
    if m:
        vid = m.group(1)
        return "plugin://plugin.video.youtube/play/?video_id=%s" % vid, "youtube"
    return None, None


def _resolve_streamtape(url, net):
    try:
        html, _, _ = net.get(url, headers={"Referer": url})
    except Exception:
        return None, None
    m = re.search(r'id="ideolink">([^<]+)<', html)
    if m:
        path = m.group(1)[::-1]
        return "https://streamtape.com/get_video?" + path, "mp4"
    return None, None


def _resolve_mixdrop(url, net):
    try:
        html, _, _ = net.get(url, headers={"Referer": url})
    except Exception:
        return None, None
    m = re.search(r'window\.link\s*=\s*["\']([^"\']+)["\']', html)
    if m and m.group(1).startswith("http"):
        return m.group(1), "mp4"
    # common pattern: <a id="download" href="...">
    m2 = re.search(r'id="download"[^>]*href=["\']([^"\']+\.mp4[^"\']*)["\']', html)
    if m2:
        return m2.group(1), "mp4"
    return None, None


def _resolve_dood(url, net):
    """DoodStream / dooood.watch / dood.to / dood.la etc."""
    try:
        html, final, _ = net.get(url, headers={"Referer": url})
    except Exception:
        return None, None
    # pass_md5 api
    m = re.search(r'/pass_md5/([^"?]+)\?token=([^"&]+)&expiry=([0-9]+)', html)
    if m:
        vid, token, expiry = m.group(1), m.group(2), m.group(3)
        host = urllib.parse.urlparse(final or url).netloc
        try:
            md5, _, _ = net.get("https://%s/pass_md5/%s?token=%s&expiry=%s" % (host, vid, token, expiry),
                                headers={"Referer": final or url})
            md5 = md5.strip()
            # build final m3u8
            final_url = "https://%s/%s/%s?token=%s&expiry=%s&o=?token=%s&expiry=%s" % (
                host, md5, vid, token, expiry, token, expiry)
            return final_url, "m3u8"
        except Exception:
            pass
    # fallback: scan
    media = _scan_html(html, final or url)
    if media:
        return pick_quality(media), "m3u8" if media[0].endswith(".m3u8") else "mp4"
    return None, None


def _resolve_filemoon(url, net):
    try:
        html, final, _ = net.get(url, headers={"Referer": url})
    except Exception:
        return None, None
    media = _scan_html(html, final or url)
    if media:
        return pick_quality(media), "m3u8" if media[0].endswith(".m3u8") else "mp4"
    # /api/source/<id> POST with d_id
    m = re.search(r'/api/source/([^"\'?]+)', html)
    if m:
        try:
            data = {"r": "", "d": urllib.parse.urlparse(final).netloc}
            js, _, _ = net.post("https://%s/api/source/%s" % (urllib.parse.urlparse(final).netloc, m.group(1)),
                                data=data, headers={"Referer": final or url,
                                                     "X-Requested-With": "XMLHttpRequest"})
            obj = json.loads(js)
            for s in obj.get("data", []):
                if s.get("file", "").endswith(".m3u8"):
                    return s["file"], "m3u8"
        except Exception:
            pass
    return None, None


def _resolve_streamwish(url, net):
    """streamwish, weshare, filelions, vidhide style hosts (similar player)."""
    try:
        html, final, _ = net.get(url, headers={"Referer": url})
    except Exception:
        return None, None
    media = _scan_html(html, final or url)
    if media:
        return pick_quality(media), "m3u8" if media[0].endswith(".m3u8") else "mp4"
    # /api/source/<id> POST
    m = re.search(r'/api/source/([^"\'?]+)', html)
    if m:
        try:
            js, _, _ = net.post("https://%s/api/source/%s" % (urllib.parse.urlparse(final).netloc, m.group(1)),
                                data={}, headers={"Referer": final or url, "X-Requested-With": "XMLHttpRequest"})
            obj = json.loads(js)
            for s in obj.get("data", []):
                if s.get("file", "").endswith(".m3u8"):
                    return s["file"], "m3u8"
        except Exception:
            pass
    return None, None


def _resolve_hdm2ink(url, net):
    """hdmovie2 -> hdm2.ink/play?v=... (indistream HLS).

    The player page embeds a <script id="player-loader"> carrying a
    ``data-stream-url`` attribute that holds the (HTML-escaped) playlist
    path. Unescaping it and fetching with the right Referer/Origin returns
    a valid HLS master playlist that plays directly inside Kodi.
    """
    try:
        page = None
        final = None
        for ref in ("https://hdm2.ink/", "https://hdmovie2a.bar/", "https://hdmovie2a.top/"):
            try:
                p, f, _ = net.get(url, headers={"Referer": ref, "Origin": "https://hdm2.ink", "Accept": "*/*"})
                if p and "Access Denied" not in p and "data-stream-url" in p:
                    page, final = p, f
                    break
            except Exception:
                continue

        if not page:
            return None, None

        m = re.search(r'data-stream-url=["\']([^"\']+)["\']', page)
        if not m:
            # fall back to a generic media scan of the page
            media = _scan_html(page, final or url)
            if media:
                return pick_quality(media), "m3u8" if media[0].endswith(".m3u8") else "mp4"
            return None, None

        raw = html.unescape(m.group(1))
        stream = raw if raw.startswith("http") else ("https://hdm2.ink" + raw)
        try:
            resp, _, _ = net.get(stream, headers={
                "Referer": final or url,
                "Origin": "https://hdm2.ink",
                "Accept": "*/*",
            })
        except Exception:
            return None, None

        if resp.lstrip().startswith("#EXTM3U") or "#EXT" in resp:
            return stream, "m3u8", {"Referer": final or url, "Origin": "https://hdm2.ink"}
        for line in resp.splitlines():
            line = line.strip()
            if line.startswith("http") and ".m3u8" in line:
                return line, "m3u8", {"Referer": final or url, "Origin": "https://hdm2.ink"}
        return None, None
    except Exception:
        return None, None


def _resolve_gxplayer(url, net):
    """watchindianmovie -> gxplayer.xyz/tv/?film=tt... (JWPlayer HLS).

    The player page is JS-driven, but the stream is reachable through a
    small API: ``api_handler.php?filmSlug=<ttid>`` returns the version
    metadata (uid / md5 / video_id / slug). Loading the ``/watch/<slug>``
    page sets the session cookie, after which the m3u8 master playlist can
    be fetched and played directly inside Kodi.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        film = qs.get("film", [None])[0]
        slug = None
        if not film:
            m = re.search(r"/watch/([^/?#]+)", url)
            if not m:
                return None, None
            slug = m.group(1)

        referer = "https://watchindianmovie.com/"

        if film:
            api = "https://watchnew.gxplayer.xyz/api_handler.php?filmSlug=%s" % urllib.parse.quote(film, safe="")
            try:
                data, _, _ = net.get(api, headers={"Referer": referer, "Accept": "application/json, */*"})
                obj = json.loads(data)
                ver = obj.get("film", {}).get("versions", [{}])[0]
                uid = ver.get("uid")
                md5 = ver.get("md5")
                vid = ver.get("video_id") or ver.get("id")
                status = ver.get("status")
                slug = ver.get("slug") or slug
            except Exception:
                return None, None

        if not (uid and md5 and vid and slug):
            return None, None

        # Load the watch page so the PHPSESSID cookie is set for the m3u8 request.
        watch = "https://watchnew.gxplayer.xyz/watch/%s?autoplay=true&s=1" % slug
        try:
            net.get(watch, headers={"Referer": referer, "Accept": "*/*"})
        except Exception:
            pass

        for c in [status, "1", "2", "0"]:
            if not c:
                continue
            m3u8 = "https://watchnew.gxplayer.xyz/m3u8/%s/%s/master.txt?s=1&id=%s&cache=%s" % (uid, md5, vid, c)
            try:
                resp, _, _ = net.get(m3u8, headers={
                    "Referer": watch,
                    "Accept": "*/*",
                })
            except Exception:
                continue
            if resp.lstrip().startswith("#EXTM3U") or "#EXT" in resp:
                return m3u8, "m3u8", {"Referer": watch}
            for line in resp.splitlines():
                line = line.strip()
                if line.startswith("http") and ".m3u8" in line:
                    return line, "m3u8", {"Referer": watch}
        return None, None
    except Exception:
        return None, None


def _resolve_hdvb(url, net):
    """HDVB / playerjs player (slash423kix, kayel, gxplayer, 1xcinema ...).

    The player page embeds a JS object with a ``file`` key pointing at the
    (often tokenised) playlist url. We extract it and try to fetch it.
    """
    try:
        html, final, _ = net.get(url, headers={"Referer": url})
    except Exception:
        return None, None
    fm = re.search(r'"file"\s*:\s*"([^"]+)"', html)
    if not fm:
        return None, None
    file_url = fm.group(1).replace("\\/", "/")
    if not file_url.startswith("http"):
        return None, None
    host = _host(final or url)
    for ref in (host, "https://slash423kix.com", url):
        try:
            resp, _, _ = net.get(file_url, headers={"Referer": ref, "Origin": ref})
            if resp.lstrip().startswith("#EXTM3U"):
                return file_url, "m3u8"
            for line in resp.splitlines():
                line = line.strip()
                if line.startswith("http") and ".m3u8" in line:
                    return line, "m3u8"
        except Exception:
            continue
    return None, None


# ---------------------------------------------------------------------------
# Resolver registry
# ---------------------------------------------------------------------------
HOST_RESOLVERS = [
    (lambda h: "youtube.com" in h or "youtu.be" in h, _resolve_youtube),
    (lambda h: "streamtape.com" in h, _resolve_streamtape),
    (lambda h: "mixdrop" in h, _resolve_mixdrop),
    (lambda h: "dood" in h, _resolve_dood),
    (lambda h: "filemoon" in h, _resolve_filemoon),
    (lambda h: any(x in h for x in ["streamwish", "weshare", "filelions", "lion", "vidhide", "vidhidehub"]),
     _resolve_streamwish),
    (lambda h: "hdm2.ink" in h or "hdm2" in h, _resolve_hdm2ink),
    (lambda h: "gxplayer" in h or "kayel" in h, _resolve_gxplayer),
    (lambda h: any(x in h for x in ["slash423kix", "1xcinema", "playerjs", "hdvb"]), _resolve_hdvb),
]


def _add_cache_buster(url):
    """Add a cache-busting parameter to prevent stale manifest issues.
    
    This helps fix seeking issues where the video freezes but audio continues,
    especially on iOS Kodi 21. The cache buster ensures fresh manifest requests.
    """
    import time
    separator = "&" if "?" in url else "?"
    return "%s%s_ncb=%d" % (url, separator, int(time.time() * 1000))


def _fix_hls_url(url):
    """Fix common HLS URL issues that cause seeking problems.
    
    - Ensure proper protocol
    - Add cache-busting for manifest freshness
    - Fix relative URLs
    """
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url.lstrip("/")
    return url


def resolve(url, net=None, preferred="Auto", referer=None):
    """Resolve a single embed/player URL to a playable stream.

    Returns a dict:
        {
          "url": <playable url or original embed>,
          "resolved": True/False,
          "kind": "m3u8" | "mp4" | "youtube" | "unresolved",
          "referer": <best referer to use when playing>,
          "headers": <extra headers for stable playback>,
        }
    """
    net = net or Net()
    url = url.strip()
    host = _host(url)
    referer = referer or host

    # 1) already direct (allow for ?query strings on the media file)
    low = url.lower().split("?")[0].split("#")[0]
    if low.endswith(".m3u8"):
        # Add cache-busting for HLS to prevent seeking freeze
        busted = _add_cache_buster(url)
        return {
            "url": busted, "resolved": True, "kind": "m3u8", "referer": referer,
            "headers": {
                "Connection": "keep-alive",
                "Keep-Alive": "timeout=30, max=1000",
            }
        }
    if low.endswith(".mp4"):
        return {"url": url, "resolved": True, "kind": "mp4", "referer": referer,
                "headers": {"Connection": "keep-alive"}}

    # 2) host specific
    for matcher, func in HOST_RESOLVERS:
        if matcher(host):
            try:
                out = func(url, net)
                if isinstance(out, tuple) and len(out) == 3:
                    res, kind, headers = out
                else:
                    res, kind = out
                    headers = {}
                if res:
                    # Add cache busting for HLS streams to fix seeking
                    final_url = _add_cache_buster(res) if kind == "m3u8" else res
                    # Merge with default keep-alive headers
                    final_headers = {
                        "Connection": "keep-alive",
                        "Keep-Alive": "timeout=30, max=1000",
                    }
                    if headers:
                        final_headers.update(headers)
                    return {"url": final_url, "resolved": True, "kind": kind,
                            "referer": headers.get("Referer", host), "headers": final_headers}
            except Exception as e:
                log("host resolver %s failed: %s" % (host, e), "debug")
            break

    # 3) generic scan
    media = _generic_resolve(url, net)
    if media:
        chosen = pick_quality(media, preferred)
        kind = "m3u8" if chosen.lower().endswith(".m3u8") else "mp4"
        final_url = _add_cache_buster(chosen) if kind == "m3u8" else chosen
        return {"url": final_url, "resolved": True, "kind": kind, "referer": host,
                "headers": {"Connection": "keep-alive", "Keep-Alive": "timeout=30, max=1000"}}

    # 4) give up - return original so UI can still show it
    return {"url": url, "resolved": False, "kind": "unresolved", "referer": host}


def resolve_all(embed_urls, preferred="Auto", net=None):
    """Resolve a list of embed urls. Returns a list of result dicts."""
    net = net or Net()
    results = []
    total = len(embed_urls)
    for i, e in enumerate(embed_urls):
        log("Resolving (%d/%d): %s" % (i + 1, total, e))
        try:
            r = resolve(e, net=net, preferred=preferred)
        except Exception as ex:
            r = {"url": e, "resolved": False, "kind": "unresolved", "referer": _host(e), "error": str(ex)}
        results.append(r)
    return results
