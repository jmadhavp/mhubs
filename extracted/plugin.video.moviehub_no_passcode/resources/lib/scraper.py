# -*- coding: utf-8 -*-
"""
scraper.py - Base scraper class + site registry.

Each partner site implements the SiteScraper interface.  The addon (main.py)
discovers enabled sites through `get_enabled_sites()` and calls the standard
methods: search(), latest(), genres(), browse() and get_sources().
"""
import os
import importlib

from common import Net, log, clean_title, clean_text, parseDOM, parse_attr


class SiteScraper:
    #: unique id (matches the enable_<id> setting)
    id = ""
    #: human readable name
    name = ""
    #: base url of the site
    base_url = ""
    #: search path template, {q} = urlencoded query
    search_url = ""
    #: latest / home path
    latest_url = ""
    #: whether the site is server-rendered (True) or JS/SPA (best-effort)
    js_rendered = False

    def __init__(self):
        self.net = Net()

    # ---- helpers -------------------------------------------------------
    def _get(self, url, headers=None):
        return self.net.get(url, headers=headers)[0]

    def _abs(self, link, base=None):
        from urllib.parse import urljoin, urlparse
        if not link:
            return ""
        if link.startswith("//"):
            return "https:" + link
        if link.startswith("http"):
            return link
        base = base or self.base_url
        return urljoin(base, link)

    # ---- interface (override in subclasses) ---------------------------
    def search(self, *args, **kwargs):
        """Override in subclasses. Accepts query as first positional arg
        or as keyword arg 'query', plus optional page as second positional arg."""
        raise NotImplementedError

    def latest(self, page=1):
        raise NotImplementedError

    def genres(self):
        """Return list of (label, url)."""
        return []

    def browse(self, url, page=1):
        """Browse a genre/category url -> list of movies."""
        raise NotImplementedError

    def get_sources(self, movie_url):
        """Return list of {label, url, host} source dicts."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
_SITES = {}


def _discover():
    here = os.path.dirname(os.path.abspath(__file__))
    sites_dir = os.path.join(here, "sites")
    for fn in os.listdir(sites_dir):
        if fn.endswith(".py") and not fn.startswith("_"):
            mod = importlib.import_module("sites.%s" % fn[:-3])
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if isinstance(obj, type) and issubclass(obj, SiteScraper) and obj is not SiteScraper:
                    try:
                        inst = obj()
                        if inst.id:
                            _SITES[inst.id] = inst
                    except Exception as e:
                        log("Failed to load site %s: %s" % (attr, e), "error")


def get_all_sites():
    if not _SITES:
        _discover()
    return _SITES


def get_enabled_sites():
    from common import get_setting
    sites = get_all_sites()
    out = []
    for sid, inst in sites.items():
        if get_setting("enable_%s" % sid, True):
            out.append(inst)
    return out


def get_site(sid):
    return get_all_sites().get(sid)
