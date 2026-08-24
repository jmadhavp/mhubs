# -*- coding: utf-8 -*-
"""Shared helpers for the site scrapers."""
import re
import urllib.parse


def slug_to_title(url):
    """Derive a human title from a url slug.

    e.g. https://x.com/movies/92-veera-dheera-sooran-part-2.html
         -> 'Veera Dheera Sooran Part 2'
    """
    path = urllib.parse.urlparse(url).path
    seg = path.rstrip("/").split("/")[-1]
    seg = re.sub(r"\.html?$", "", seg)
    seg = re.sub(r"^\d+-", "", seg)          # leading id e.g. 92-
    seg = seg.replace("-", " ")
    # title case but keep common acronyms upper
    title = seg.title()
    return title.strip()


def title_from_text(text, fallback_url):
    text = text.strip()
    if text:
        return text
    return slug_to_title(fallback_url)


def thumb_after(html, pos, limit=4000):
    """Find the first <img src> within `limit` chars after position `pos`."""
    chunk = html[pos:pos + limit]
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', chunk, re.I)
    if m:
        return m.group(1)
    return ""


def year_from_text(text):
    m = re.search(r"(19|20)\d{2}", text)
    return m.group(0) if m else ""


def clean_movie(url, title, thumb="", year=""):
    return {
        "title": title,
        "url": url,
        "thumb": thumb,
        "year": year,
    }


IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg")


def is_media_embed(url):
    """Return True if the url looks like a player/embed we should try to resolve."""
    if not url or not url.startswith("http"):
        return False
    low = url.lower()
    if any(low.endswith(e) for e in IMG_EXT):
        return False
    return True


def host_label(url):
    try:
        return urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return url
