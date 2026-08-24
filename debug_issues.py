# -*- coding: utf-8 -*-
"""
Debug search and site structure issues
"""

import sys
import os
import urllib.request
import urllib.parse
import ssl
import re

sys.path.insert(0, r'D:\updates\plugin.video.moviehub.unified\resources\lib')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=" * 60)
print("  Debug Search & Site Issues")
print("=" * 60)

# ============================================================
# DEBUG 1: Search Issue - Why returning same results for all queries
# ============================================================
print("\n[DEBUG 1] Search Issue")
print("-" * 40)

# Check HDMovie2 sitemap
print("\n1.1 Checking HDMovie2 sitemap...")
try:
    req = urllib.request.Request('https://hdmovie2a.icu/movies-sitemap.xml', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    xml = resp.read().decode('utf-8', errors='ignore')
    urls = re.findall(r'<loc>([^<]+)</loc>', xml)
    print(f"   Sitemap URLs: {len(urls)}")
    
    # Test search for "action"
    q = "action"
    matches = [u for u in urls if q in u.lower()]
    print(f"   URLs containing '{q}': {len(matches)}")
    for u in matches[:5]:
        print(f"      - {u}")
    
    # Test search for "love"
    q = "love"
    matches = [u for u in urls if q in u.lower()]
    print(f"   URLs containing '{q}': {len(matches)}")
    for u in matches[:5]:
        print(f"      - {u}")
        
except Exception as e:
    print(f"   Sitemap error: {e}")

# Test site search directly
print("\n1.2 Testing site search directly...")
try:
    query = "action"
    encoded = urllib.parse.quote(query)
    url = f"https://hdmovie2a.icu/?s={encoded}"
    print(f"   Search URL: {url}")
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    print(f"   Response length: {len(html)} chars")
    
    # Check if it's a search results page or redirect
    print(f"   Final URL: {resp.geturl()}")
    
    # Look for search results
    articles = re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL)
    print(f"   Articles found: {len(articles)}")
    
    # Look for "not found" or similar
    if "no results" in html.lower() or "not found" in html.lower():
        print("   WARNING: No results message found")
        
except Exception as e:
    print(f"   Search error: {e}")

# ============================================================
# DEBUG 2: StreamIMDB - Find correct URL
# ============================================================
print("\n[DEBUG 2] StreamIMDB Site")
print("-" * 40)

urls_to_try = [
    'https://streamimdb.ru/',
    'https://streamimdb.ru/movies',
    'https://streamimdb.ru/movie',
    'https://streamimdb.ru/films',
    'https://streamimdb.ru/tv',
    'https://streamimdb.ru/tv-shows',
]

for url in urls_to_try:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        html = resp.read().decode('utf-8', errors='ignore')
        final_url = resp.geturl()
        print(f"   {url}")
        print(f"      -> {final_url} ({len(html)} chars)")
        
        # Look for movie/tv links
        movie_links = re.findall(r'href="(/movie/[^"]+)"', html)
        tv_links = re.findall(r'href="(/tv/[^"]+)"', html)
        if movie_links or tv_links:
            print(f"      Movies: {len(movie_links)}, TV: {len(tv_links)}")
            if movie_links:
                print(f"      Example: {movie_links[0]}")
    except Exception as e:
        print(f"   {url} -> ERROR: {str(e)[:50]}")

# ============================================================
# DEBUG 3: FreeTV Studio Channel Names
# ============================================================
print("\n[DEBUG 3] FreeTV Studio Channel Names")
print("-" * 40)

print("\n3.1 Checking channel page structure...")
try:
    url = 'https://freetv.studio/channel/arte.fr'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    
    # Look for title
    title_m = re.search(r'<title>([^<]+)</title>', html)
    if title_m:
        print(f"   Page title: {title_m.group(1)}")
    
    # Look for h1
    h1_m = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    if h1_m:
        print(f"   H1: {h1_m.group(1)}")
    
    # Look for og:title
    og_m = re.search(r'property="og:title"[^>]*content="([^"]+)"', html)
    if og_m:
        print(f"   OG Title: {og_m.group(1)}")
        
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)
print("  Debug Complete")
print("=" * 60)
