# -*- coding: utf-8 -*-
"""
cache.py - Caching system for MovieHub addon.

Provides time-based caching for sitemap data, search results, and
page content to reduce network requests and speed up browsing.
"""
import os
import json
import time
import hashlib

from common import log, get_setting

ADDON_ID = "plugin.video.moviehub"

try:
    import xbmc
    _KODI = True
except ImportError:
    _KODI = False


def _cache_dir():
    """Get the addon cache directory path."""
    if _KODI:
        try:
            from xbmc import translatePath
            profile = translatePath("special://profile/addon_data/%s/" % ADDON_ID)
            cache_path = os.path.join(profile, "cache")
        except Exception:
            cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cache")
    else:
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".moviehub_cache")
    try:
        os.makedirs(cache_path, exist_ok=True)
    except Exception:
        pass
    return cache_path


def _key(name):
    """Generate a cache key filename from a name."""
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return os.path.join(_cache_dir(), "%s.json" % h)


def get(name, max_age=3600):
    """Get a cached value. Returns None if missing or expired.
    
    Args:
        name: Cache key name
        max_age: Maximum age in seconds (default 1 hour)
    """
    try:
        path = _key(name)
        if not os.path.exists(path):
            return None
        age = time.time() - os.path.getmtime(path)
        if age > max_age:
            os.remove(path)
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("value")
    except Exception as e:
        log("cache get error: %s" % e, "debug")
        return None


def set(name, value, max_age=3600):
    """Store a value in the cache.
    
    Args:
        name: Cache key name
        value: Value to cache (must be JSON-serializable)
        max_age: Maximum age in seconds (default 1 hour)
    """
    try:
        path = _key(name)
        data = {
            "value": value,
            "created": time.time(),
            "max_age": max_age,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log("cache set error: %s" % e, "debug")
        return False


def delete(name):
    """Remove a cached item."""
    try:
        path = _key(name)
        if os.path.exists(path):
            os.remove(path)
            return True
    except Exception as e:
        log("cache delete error: %s" % e, "debug")
    return False


def clear(max_age=None):
    """Clear all cached items, or only those older than max_age seconds."""
    try:
        cache_dir = _cache_dir()
        for fn in os.listdir(cache_dir):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(cache_dir, fn)
            if max_age is not None:
                age = time.time() - os.path.getmtime(path)
                if age < max_age:
                    continue
            os.remove(path)
        log("Cache cleared (max_age=%s)" % max_age, "info")
        return True
    except Exception as e:
        log("cache clear error: %s" % e, "debug")
        return False


def get_size():
    """Get total cache size in bytes."""
    total = 0
    try:
        cache_dir = _cache_dir()
        for fn in os.listdir(cache_dir):
            path = os.path.join(cache_dir, fn)
            if os.path.isfile(path):
                total += os.path.getsize(path)
    except Exception:
        pass
    return total


def get_count():
    """Get number of cached items."""
    count = 0
    try:
        cache_dir = _cache_dir()
        for fn in os.listdir(cache_dir):
            if fn.endswith(".json"):
                count += 1
    except Exception:
        pass
    return count

