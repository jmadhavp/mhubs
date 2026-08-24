# -*- coding: utf-8 -*-
"""Generic movie site scraper (dooplay WordPress, JS search -> sitemap)."""
import re
import urllib.parse
import os

from scraper import SiteScraper
from common import log, clean_text
from sites._utils import (slug_to_title, title_from_text, thumb_after, clean_movie,
                           is_media_embed, host_label)

BASE = "https://hdmovie2a.bar"
SITEMAP = BASE + "/movies-sitemap.xml"


class Movies(SiteScraper):
    id = "movies"
    name = "Movies"
    base_url = BASE
    latest_url = BASE + "/movies/"

    def __init__(self):
        super().__init__()
        self._sitemap_cache = None

    # ------------------------------------------------------------------
    def _sitemap_urls(self):
        if self._sitemap_cache is not None:
            return self._sitemap_cache
        try:
            xml = self._get(SITEMAP)
            urls = re.findall(r"<loc>([^<]+)</loc>", xml)
            self._sitemap_cache = urls
        except Exception as e:
            log("sitemap error: %s" % e, "error")
            self._sitemap_cache = []
        return self._sitemap_cache

    def _extract_poster_links(self, html):
        movies = []
        seen = set()
        # Strategy: extract movie items as complete containers (article / div)
        # so that the poster <img> belongs to the same container as its <a> link.
        # This fixes the issue where thumb_after() picks the next movie's poster.
        containers = []

        # Try to find article-based containers (WordPress dooplay theme)
        containers = re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL)
        if not containers:
            # Try div.poster / div.item / div.movie / div.card containers
            containers = re.findall(
                r'<div[^>]*class="[^"]*(?:poster|item|movie|card|col)[^"]*"[^>]*>.*?</div>',
                html, re.DOTALL
            )
        if not containers:
            # Fallback: split by <a class="poster-link"> boundaries using lookahead
            containers = re.split(r'(?=<a class="poster-link")', html)
            containers = [c.strip() for c in containers if c.strip()]

        for container in containers:
            a = re.search(
                r'<a class="poster-link" href="([^"]+)"[^>]*aria-label="([^"]*)"',
                container
            )
            if not a:
                continue
            url = self._abs(a.group(1), BASE)
            if url in seen:
                continue
            seen.add(url)
            title = clean_text(a.group(2)) or slug_to_title(url)
            year = ""
            my = re.search(r"\((\d{4})\)", title)
            if my:
                year = my.group(1)
                title = title.replace("(%s)" % year, "").strip()
            # Extract poster from within the SAME container
            img_m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', container, re.I)
            thumb = img_m.group(1) if img_m else ""
            movies.append(clean_movie(url, title, thumb, year))

        return movies

    # ------------------------------------------------------------------
    def _page_url(self, url, page):
        """Build a paginated URL. Page 1 == the base url; page N == /page/N/."""
        if not page or page <= 1:
            return url
        base = re.sub(r"/page/\d+/?", "", url)
        if not base.endswith("/"):
            base += "/"
        return "%spage/%d/" % (base, page)

    def search(self, *args, **kwargs):
        query = args[0] if args else kwargs.get("query", "")
        page = 1
        if len(args) >= 2 and isinstance(args[1], int):
            page = args[1]
        if "page" in kwargs and kwargs.get("page") is not None:
            try:
                page = int(kwargs.get("page"))
            except Exception:
                page = 1
        if not page or page < 1:
            page = 1
        per_page = kwargs.get("per_page", 50)
        try:
            per_page = int(per_page)
        except Exception:
            per_page = 50
        if per_page < 1:
            per_page = 50

        q = query.lower()
        start = (page - 1) * per_page
        end = start + per_page
        out = []
        match_i = 0
        for u in self._sitemap_urls():
            if q in u.lower():
                if match_i >= start and match_i < end:
                    out.append(clean_movie(u, slug_to_title(u), "", ""))
                match_i += 1
                if match_i >= end:
                    break
        return out

    def latest(self, page=1):
        url = self._page_url(self.latest_url, page)
        try:
            html = self._get(url)
        except Exception as e:
            log("latest error: %s" % e, "error")
            return []
        return self._extract_poster_links(html)

    def genres(self):
        return [
            ("Bollywood", BASE + "/genre/bollywood/"),
            ("Hollywood", BASE + "/genre/hollywood/"),
            ("Hindi Dubbed", BASE + "/genre/hindi-dubbed/"),
            ("Netflix", BASE + "/genre/netflix/"),
            ("South Hindi Dubbed", BASE + "/genre/south-hindi-dubbed/"),
            ("Web Series", BASE + "/genre/web-series/"),
            ("Action", BASE + "/genre/action/"),
        ]

    def browse(self, url, page=1):
        url = self._page_url(url, page)
        try:
            html = self._get(url)
        except Exception as e:
            log("browse error: %s" % e, "error")
            return []
        movies = self._extract_poster_links(html)
        if not movies:
            # fallback: any /movies/ link
            for m in re.finditer(r'href="(%s/movies/[^"]+/)"' % re.escape(BASE), html):
                u = m.group(1)
                movies.append(clean_movie(u, slug_to_title(u), "", ""))
        return movies

    # ------------------------------------------------------------------
    def get_sources(self, movie_url):
        try:
            html = self._get(movie_url)
        except Exception as e:
            log("sources error: %s" % e, "error")
            return []
        sources = []
        seen = set()

        # Cleanly extract movie title from entry-title or h1
        movie_title = ""
        tm = re.search(r'<h1[^>]*>([^<]+)<', html, re.I)
        if tm:
            movie_title = clean_text(tm.group(1))
        if not movie_title:
            movie_title = slug_to_title(movie_url)

        base_label = movie_title or "Stream"

        idx = 0
        raw_embeds = []

        # 1. Primary player links (hdm2.ink / play?v= URLs)
        for emb in re.findall(r'https?://[^\s"\'<>]+\bplay\?[^\s"\'<>]+', html):
            raw_embeds.append(emb)

        # 2. Data attributes (data-source, data-first-source, data-embed, data-link)
        for emb in re.findall(r'data-(?:source|first-source|embed|link)=["\']([^"\']+)["\']', html):
            emb = self._abs(emb, movie_url)
            if is_media_embed(emb):
                raw_embeds.append(emb)

        # 3. Iframes
        for ifr in re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.I):
            ifr = self._abs(ifr, movie_url)
            if is_media_embed(ifr):
                raw_embeds.append(ifr)

        for emb in raw_embeds:
            if not emb or emb in seen:
                continue
            # Skip promo or invalid links
            emb_low = emb.lower()
            if any(x in emb_low for x in ["youtube.com/embed/cb7ab7qirpk", "facebook.com", "twitter.com"]):
                continue
            seen.add(emb)
            idx += 1
            host = host_label(emb)
            label = "%s [%s %d]" % (base_label, host, idx)
            sources.append({"label": label, "url": emb, "host": host, "referer": movie_url})

        return sources
