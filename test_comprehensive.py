# -*- coding: utf-8 -*-
"""
Comprehensive test script for MovieHub Unified addon
Tests all scrapers, search, and channel resolution
"""

import sys
import os
sys.path.insert(0, r'D:\updates\plugin.video.moviehub.unified\resources\lib')

print("=" * 60)
print("  MovieHub Unified - Comprehensive Test")
print("=" * 60)

# ============================================================
# TEST 1: HDMovie2 (hdmovie2a.icu)
# ============================================================
print("\n[TEST 1] HDMovie2 (hdmovie2a.icu)")
print("-" * 40)

from hdm2_scraper import get_latest, search, get_detail, get_genres

# Test latest
print("\n1.1 Testing get_latest(page=1)...")
try:
    movies = get_latest(1)
    print(f"   SUCCESS: Found {len(movies)} movies")
    if movies:
        print(f"   First movie: {movies[0].get('title', 'N/A')}")
        print(f"   URL: {movies[0].get('url', 'N/A')}")
except Exception as e:
    print(f"   FAILED: {e}")

# Test search
print("\n1.2 Testing search('action')...")
try:
    results = search("action")
    print(f"   SUCCESS: Found {len(results)} results")
    if results:
        print(f"   First result: {results[0].get('title', 'N/A')}")
except Exception as e:
    print(f"   FAILED: {e}")

# Test detail (if movies found)
print("\n1.3 Testing get_detail(first movie)...")
try:
    if movies:
        detail = get_detail(movies[0]['url'])
        if detail:
            print(f"   SUCCESS: Title={detail.get('title', 'N/A')}")
            print(f"   Sources: {len(detail.get('sources', []))}")
        else:
            print("   FAILED: No detail returned")
    else:
        print("   SKIPPED: No movies to test")
except Exception as e:
    print(f"   FAILED: {e}")

# ============================================================
# TEST 2: MovieHub (hdmovie2a.bar)
# ============================================================
print("\n[TEST 2] MovieHub (hdmovie2a.bar)")
print("-" * 40)

from moviehub_scraper import get_latest, search, get_detail

# Test latest
print("\n2.1 Testing get_latest(page=1)...")
try:
    movies = get_latest(1)
    print(f"   SUCCESS: Found {len(movies)} movies")
    if movies:
        print(f"   First movie: {movies[0].get('title', 'N/A')}")
        print(f"   URL: {movies[0].get('url', 'N/A')}")
except Exception as e:
    print(f"   FAILED: {e}")

# Test search
print("\n2.2 Testing search('love')...")
try:
    results = search("love")
    print(f"   SUCCESS: Found {len(results)} results")
    if results:
        print(f"   First result: {results[0].get('title', 'N/A')}")
except Exception as e:
    print(f"   FAILED: {e}")

# ============================================================
# TEST 3: StreamIMDB (streamimdb.ru)
# ============================================================
print("\n[TEST 3] StreamIMDB (streamimdb.ru)")
print("-" * 40)

from streamimdb_scraper import get_latest, get_tv_shows, search, get_detail

# Test latest movies
print("\n3.1 Testing get_latest(page=1)...")
try:
    movies = get_latest(1)
    print(f"   SUCCESS: Found {len(movies)} movies")
    if movies:
        print(f"   First movie: {movies[0].get('title', 'N/A')}")
        print(f"   URL: {movies[0].get('url', 'N/A')}")
    else:
        print("   WARNING: No movies found - checking site structure...")
        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request('https://streamimdb.ru/movie/', headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"   Site response length: {len(html)} chars")
        import re
        movie_links = re.findall(r'href="(/movie/[^"]+)"', html)
        print(f"   Movie links found: {len(movie_links)}")
        if movie_links:
            print(f"   Example: {movie_links[0]}")
except Exception as e:
    print(f"   FAILED: {e}")

# Test TV shows
print("\n3.2 Testing get_tv_shows(page=1)...")
try:
    shows = get_tv_shows(1)
    print(f"   SUCCESS: Found {len(shows)} TV shows")
    if shows:
        print(f"   First show: {shows[0].get('title', 'N/A')}")
except Exception as e:
    print(f"   FAILED: {e}")

# ============================================================
# TEST 4: FreeTV Studio (freetv.studio)
# ============================================================
print("\n[TEST 4] FreeTV Studio (freetv.studio)")
print("-" * 40)

from tv_scraper import get_all_channels, get_radio, get_countries, get_categories, get_channels_by_country

# Test channels
print("\n4.1 Testing get_all_channels(page=1)...")
try:
    channels = get_all_channels(1)
    print(f"   SUCCESS: Found {len(channels)} channels")
    if channels:
        print(f"   First channel: {channels[0].get('name', 'N/A')}")
        print(f"   URL: {channels[0].get('url', 'N/A')}")
except Exception as e:
    print(f"   FAILED: {e}")

# Test countries
print("\n4.2 Testing get_countries()...")
try:
    countries = get_countries()
    print(f"   SUCCESS: Found {len(countries)} countries")
except Exception as e:
    print(f"   FAILED: {e}")

# Test categories
print("\n4.3 Testing get_categories()...")
try:
    categories = get_categories()
    print(f"   SUCCESS: Found {len(categories)} categories")
except Exception as e:
    print(f"   FAILED: {e}")

# ============================================================
# TEST 5: Channel Resolution
# ============================================================
print("\n[TEST 5] Channel Resolution")
print("-" * 40)

from resolver import resolve

print("\n5.1 Testing resolve(FreeTV channel)...")
try:
    if channels:
        result = resolve(channels[0]['url'])
        if result:
            print(f"   SUCCESS: Resolved to {result.get('kind', 'unknown')}")
            print(f"   Stream URL: {result.get('url', 'N/A')[:80]}...")
        else:
            print("   FAILED: No result returned")
    else:
        print("   SKIPPED: No channels to test")
except Exception as e:
    print(f"   FAILED: {e}")

print("\n5.2 Testing resolve(BBC News direct)...")
try:
    result = resolve('https://freetv.studio/channel/BBCNews.uk')
    if result:
        print(f"   SUCCESS: Resolved to {result.get('kind', 'unknown')}")
        print(f"   Stream URL: {result.get('url', 'N/A')[:80]}...")
    else:
        print("   FAILED: No result returned")
except Exception as e:
    print(f"   FAILED: {e}")

# ============================================================
# TEST 6: Search Issues Diagnosis
# ============================================================
print("\n[TEST 6] Search Issues Diagnosis")
print("-" * 40)

print("\n6.1 Testing HDMovie2 search with different queries...")
test_queries = ["action", "love", "2024", "hindi"]
for q in test_queries:
    try:
        results = search(q)
        print(f"   '{q}': {len(results)} results")
    except Exception as e:
        print(f"   '{q}': FAILED - {e}")

print("\n6.2 Checking search URL construction...")
from urllib.parse import quote
test_query = "action movie"
encoded = quote(test_query)
print(f"   Query: {test_query}")
print(f"   Encoded: {encoded}")
print(f"   HDMovie2 search URL: https://hdmovie2a.icu/?s={encoded}")
print(f"   MovieHub search URL: https://hdmovie2a.bar/?s={encoded}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("  Test Complete")
print("=" * 60)
