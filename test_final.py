# -*- coding: utf-8 -*-
"""
Final test after all fixes
"""

import sys
sys.path.insert(0, r'D:\updates\plugin.video.moviehub.unified\resources\lib')

print("=" * 60)
print("  Final Test - After All Fixes")
print("=" * 60)

# ============================================================
# TEST 1: Search in HDMovie2
# ============================================================
print("\n[TEST 1] HDMovie2 Search (hdmovie2a.icu)")
print("-" * 40)

from hdm2_scraper import search, get_latest

print("\n1.1 Testing search('action')...")
results = search("action")
print(f"   Found: {len(results)} results")
for r in results[:5]:
    print(f"      - {r.get('title', 'N/A')}")

print("\n1.2 Testing search('love')...")
results = search("love")
print(f"   Found: {len(results)} results")
for r in results[:5]:
    print(f"      - {r.get('title', 'N/A')}")

print("\n1.3 Testing search('2024')...")
results = search("2024")
print(f"   Found: {len(results)} results")
for r in results[:5]:
    print(f"      - {r.get('title', 'N/A')}")

# ============================================================
# TEST 2: Search in MovieHub
# ============================================================
print("\n[TEST 2] MovieHub Search (hdmovie2a.bar)")
print("-" * 40)

from moviehub_scraper import search

print("\n2.1 Testing search('action')...")
results = search("action")
print(f"   Found: {len(results)} results")
for r in results[:5]:
    print(f"      - {r.get('title', 'N/A')}")

print("\n2.2 Testing search('hindi')...")
results = search("hindi")
print(f"   Found: {len(results)} results")
for r in results[:5]:
    print(f"      - {r.get('title', 'N/A')}")

# ============================================================
# TEST 3: StreamIMDB
# ============================================================
print("\n[TEST 3] StreamIMDB (streamimdb.ru)")
print("-" * 40)

from streamimdb_scraper import get_latest, get_tv_shows, search

print("\n3.1 Testing get_latest(page=1)...")
movies = get_latest(1)
print(f"   Found: {len(movies)} movies")
for m in movies[:5]:
    print(f"      - {m.get('title', 'N/A')} -> {m.get('url', 'N/A')}")

print("\n3.2 Testing get_tv_shows(page=1)...")
shows = get_tv_shows(1)
print(f"   Found: {len(shows)} TV shows")
for s in shows[:5]:
    print(f"      - {s.get('title', 'N/A')}")

print("\n3.3 Testing search('batman')...")
results = search("batman")
print(f"   Found: {len(results)} results")
for r in results[:5]:
    print(f"      - {r.get('title', 'N/A')}")

# ============================================================
# TEST 4: FreeTV Studio
# ============================================================
print("\n[TEST 4] FreeTV Studio (freetv.studio)")
print("-" * 40)

from tv_scraper import get_all_channels, get_radio, get_countries, get_categories

print("\n4.1 Testing get_all_channels(page=1)...")
channels = get_all_channels(1)
print(f"   Found: {len(channels)} channels")
for ch in channels[:10]:
    print(f"      - {ch.get('name', 'N/A')} -> {ch.get('url', 'N/A')}")

print("\n4.2 Testing get_radio()...")
radio = get_radio()
print(f"   Found: {len(radio)} radio stations")
for r in radio[:5]:
    print(f"      - {r.get('name', 'N/A')}")

# ============================================================
# TEST 5: Channel Resolution
# ============================================================
print("\n[TEST 5] Channel Resolution")
print("-" * 40)

from resolver import resolve

print("\n5.1 Testing resolve(first channel)...")
if channels:
    result = resolve(channels[0]['url'])
    if result:
        print(f"   SUCCESS: {result.get('kind', 'unknown')}")
        print(f"   URL: {result.get('url', 'N/A')[:80]}...")
    else:
        print("   FAILED")

print("\n5.2 Testing resolve(BBC News)...")
result = resolve('https://freetv.studio/channel/BBCNews.uk')
if result:
    print(f"   SUCCESS: {result.get('kind', 'unknown')}")
    print(f"   URL: {result.get('url', 'N/A')[:80]}...")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("  Test Complete")
print("=" * 60)
