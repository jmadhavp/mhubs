# -*- coding: utf-8 -*-
"""
common.py - Shared utilities for the MovieHub Kodi addon.

This module is intentionally importable both inside Kodi and in a normal
Python interpreter so the scraping / resolving logic can be unit-tested
offline (see tests/run_tests.py).
"""
import re
import json
import time
import ssl
import socket
import urllib.parse
import urllib.request
import urllib.error
import http.cookiejar
import gzip

# ---------------------------------------------------------------------------
# Kodi detection (so the same code runs in plain Python for testing)
# ---------------------------------------------------------------------------
try:
    import xbmc
    import xbmcgui
    import xbmcaddon
    import xbmcplugin
    _KODI = True
except ImportError:
    xbmc = xbmcgui = xbmcaddon = xbmcplugin = None
    _KODI = False

ADDON_ID = "plugin.video.moviehub"


def get_addon():
    if _KODI:
        return xbmcaddon.Addon(id=ADDON_ID)
    return None


# ---------------------------------------------------------------------------
# Settings (Kodi settings.xml or a local json file when testing)
# ---------------------------------------------------------------------------
_SETTINGS_CACHE = {}
_LOCAL_SETTINGS = {}


def _local_settings_path():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "..", "settings_local.json")


def get_setting(key, default=None):
    if _KODI:
        try:
            v = get_addon().getSetting(key)
            if v == "" and default is not None:
                return default
            if isinstance(default, bool):
                return v == "true"
            if isinstance(default, int):
                try:
                    return int(v)
                except ValueError:
                    return default
            return v
        except Exception:
            return default
    else:
        import os
        p = _local_settings_path()
        if not _LOCAL_SETTINGS and os.path.exists(p):
            try:
                _LOCAL_SETTINGS.update(json.load(open(p, encoding="utf-8")))
            except Exception:
                pass
        return _LOCAL_SETTINGS.get(key, default)


def set_setting(key, value):
    if _KODI:
        try:
            get_addon().setSetting(key, str(value))
        except Exception:
            pass
    else:
        _LOCAL_SETTINGS[key] = value
        import os
        try:
            json.dump(_LOCAL_SETTINGS, open(_local_settings_path(), "w", encoding="utf-8"), indent=2)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Device identity (stable per-install id, not hardware MAC)
# ---------------------------------------------------------------------------
def get_device_id():
    """Return a stable, randomly generated device identity (100 chars).

    Unlike a hardware MAC (which can "hop" on mobile Kodi builds, breaking
    device-locking), this id is generated once and persisted in the addon's
    data directory, so a code stays locked to the same Kodi installation
    across launches. Clearing the addon's data creates a new device.
    """
    import os
    if _KODI:
        try:
            base = xbmc.translatePath("special://profile/addon_data/%s/" % ADDON_ID)
        except Exception:
            base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "device_data")
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".moviehub_data")
    path = os.path.join(base, "device_id.txt")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                val = f.read().strip()
            if val:
                return val
    except Exception:
        pass
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{};:,.<>?"
    try:
        import secrets
        rid = "".join(secrets.choice(alphabet) for _ in range(100))
    except Exception:
        import random
        rid = "".join(random.choice(alphabet) for _ in range(100))
    try:
        os.makedirs(base, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(rid)
    except Exception:
        pass
    return rid


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def log(msg, level="info"):
    msg = str(msg)
    if get_setting("enable_log", True) is False and _KODI:
        return
    if _KODI:
        lvl = xbmc.LOGINFO
        if level == "error":
            lvl = xbmc.LOGERROR
        elif level == "debug":
            lvl = xbmc.LOGDEBUG
        xbmc.log("[%s] %s" % (ADDON_ID, msg), lvl)
    else:
        print("[%s][%s] %s" % (ADDON_ID, level, msg))


def notify(message, title="MovieHub", icon=None, duration=4000):
    if _KODI:
        xbmcgui.Dialog().notification(title, message, icon or xbmcgui.NOTIFICATION_INFO, duration)
    else:
        print("[NOTIFY] %s: %s" % (title, message))


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def replaceHTMLCodes(txt):
    if not txt:
        return ""
    q = chr(34)
    apos = chr(39)
    amp = "&" + "amp;"
    quot = "&" + "quot;"
    lt = "&" + "lt;"
    gt = "&" + "gt;"
    nbsp = "&" + "nbsp;"
    apos_ent = "&" + "apos;"
    ent39 = "&" + "#39;"
    entx27 = "&" + "#x27;"
    txt = (txt.replace(amp, "&")
              .replace(quot, q)
              .replace(lt, "<")
              .replace(gt, ">")
              .replace(ent39, apos)
              .replace(apos_ent, apos)
              .replace(entx27, apos)
              .replace(nbsp, " "))
    txt = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), txt)
    return txt


def clean_text(txt):
    if not txt:
        return ""
    txt = replaceHTMLCodes(txt)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def clean_title(txt):
    txt = clean_text(txt)
    txt = re.sub(r"\s*\(\s*(\d{4})\s*\)\s*$", r" (\1)", txt)
    return txt


# ---------------------------------------------------------------------------
# Minimal HTML DOM parser (regex based, no external deps)
# Based on the classic parseDOM concept used across Kodi addons.
# ---------------------------------------------------------------------------
def parseDOM(html, tag, attrs=None, ret=False):
    """Very small parseDOM implementation.

    Returns a list of inner HTML strings for each <tag ...>...</tag> that
    matches the given attributes, or the value of the requested attribute
    when `ret` is given.
    """
    if not html:
        return []
    tag = tag.lower()
    attrs = attrs or {}
    attr_str = "".join(
        r'(?=.*\b%s\s*=\s*["\']%s["\'])' % (re.escape(k), re.escape(v)) for k, v in attrs.items()
    )
    pattern = r"<%s%s\s*[^>]*>(.*?)</%s>" % (tag, attr_str, tag)
    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
    if not ret:
        return [m for m in matches]
    out = []
    open_pattern = r"<%s%s\s*[^>]*>" % (tag, attr_str)
    for m in re.finditer(open_pattern, html, re.IGNORECASE):
        tag_html = m.group(0)
        am = re.search(r'\b%s\s*=\s*["\']([^"\']+)["\']' % re.escape(ret), tag_html, re.IGNORECASE)
        if am:
            out.append(am.group(1))
    return out


def parse_attr(html, tag, attr, attrs=None):
    return parseDOM(html, tag, attrs or {}, ret=attr)


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------
class Net:
    """A small urllib based HTTP client with cookies, retries and gzip."""

    def __init__(self, user_agent=None, timeout=25, retries=3, cookies=None):
        self.timeout = timeout or get_setting("resolve_timeout", 25)
        self.retries = retries
        self.user_agent = user_agent or get_setting(
            "user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        )
        self.cj = cookies or http.cookiejar.CookieJar()
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE
        self.last_url = ""

    def _build_opener(self):
        return urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj),
            urllib.request.HTTPSHandler(context=self._ctx),
            urllib.request.HTTPHandler(),
        )

    def request(self, url, method="GET", data=None, headers=None, allow_redirects=True,
                binary=False, retry_on=None):
        headers = headers or {}
        headers.setdefault("User-Agent", self.user_agent)
        headers.setdefault("Accept-Language", "en-US,en;q=0.9")
        if data and isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode("utf-8")
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        elif data and isinstance(data, str):
            data = data.encode("utf-8")

        last_err = None
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method=method)
                if not allow_redirects:
                    class NoRedirect(urllib.request.HTTPRedirectHandler):
                        def redirect_request(self, *args, **kwargs):
                            return None
                    opener = urllib.request.build_opener(
                        urllib.request.HTTPCookieProcessor(self.cj),
                        NoRedirect(),
                        urllib.request.HTTPSHandler(context=self._ctx),
                    )
                    resp = opener.open(req, timeout=self.timeout)
                else:
                    resp = self._build_opener().open(req, timeout=self.timeout)
                self.last_url = resp.geturl()
                final_url = resp.geturl()
                raw = resp.read()
                enc = resp.headers.get("Content-Encoding", "")
                if enc and "gzip" in enc.lower():
                    raw = gzip.decompress(raw)
                if binary:
                    return raw, final_url, resp
                return raw.decode("utf-8", "ignore"), final_url, resp
            except urllib.error.HTTPError as e:
                last_err = e
                if retry_on and e.code not in retry_on:
                    raise
                headers.setdefault("Referer", url)
                time.sleep(1 + attempt)
            except (urllib.error.URLError, socket.timeout, ssl.SSLError) as e:
                last_err = e
                time.sleep(1 + attempt)
        if last_err:
            raise last_err
        return ("", url, None)

    def get(self, url, **kw):
        return self.request(url, "GET", **kw)

    def post(self, url, data=None, **kw):
        return self.request(url, "POST", data=data, **kw)

    def get_cookies(self, domain=None):
        out = {}
        for c in self.cj:
            if domain is None or domain in c.domain:
                out[c.name] = c.value
        return out


# ---------------------------------------------------------------------------
# Progress dialog (Kodi) / no-op (CLI)
# ---------------------------------------------------------------------------
class Progress:
    def __init__(self, heading="MovieHub"):
        if _KODI:
            self.dlg = xbmcgui.DialogProgress()
            self.dlg.create(heading, "")
        else:
            self.dlg = None

    def update(self, percent, line1="", line2="", line3=""):
        if self.dlg:
            # Kodi 20+ only accepts 2 arguments (percent, line)
            # Combine all lines with newlines for compatibility
            combined = "\n".join([l for l in (line1, line2, line3) if l])
            self.dlg.update(int(percent), combined)

    def close(self):
        if self.dlg:
            self.dlg.close()

    def is_canceled(self):
        return self.dlg.iscanceled() if self.dlg else False


def yesno(heading, message):
    if _KODI:
        return xbmcgui.Dialog().yesno(heading, message)
    return False


def select(heading, options):
    if _KODI:
        return xbmcgui.Dialog().select(heading, options)
    print(heading)
    for i, o in enumerate(options):
        print("  [%d] %s" % (i, o))
    return -1


def human_size(num):
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(num) < 1024.0:
            return "%.1f%s" % (num, unit)
        num /= 1024.0
    return "%.1fTB" % num
