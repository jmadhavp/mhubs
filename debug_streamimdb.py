# -*- coding: utf-8 -*-
"""
Debug - StreamIMDB site structure
"""

import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=" * 60)
print("  StreamIMDB Site Debug")
print("=" * 60)

# Test homepage
print("\n1. Testing homepage...")
try:
    req = urllib.request.Request('https://streamimdb.ru/', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    final_url = resp.geturl()
    print(f"  Final URL: {final_url}")
    print(f"  Response length: {len(html)} chars")
    
    # Look for navigation links
    nav_links = re.findall(r'href="([^"]*(?:movie|tv|genre|category)[^"]*)"', html, re.I)
    print(f"  Navigation links: {len(nav_links)}")
    for l in set(nav_links[:10]):
        print(f"    - {l}")
    
    # Look for movie/tv content links
    movie_links = re.findall(r'href="(/movie/[^"]+)"', html)
    tv_links = re.findall(r'href="(/tv/[^"]+)"', html)
    print(f"  Movie links: {len(movie_links)}")
    print(f"  TV links: {len(tv_links)}")
    
    if movie_links:
        print(f"  Example movie: {movie_links[0]}")
    if tv_links:
        print(f"  Example TV: {tv_links[0]}")
        
except Exception as e:
    print(f"  Error: {e}")

# Test /movies (plural)
print("\n2. Testing /movies...")
try:
    req = urllib.request.Request('https://streamimdb.ru/movies', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    final_url = resp.geturl()
    print(f"  Final URL: {final_url}")
    print(f"  Response length: {len(html)} chars")
    
    movie_links = re.findall(r'href="(/movie/[^"]+)"', html)
    print(f"  Movie links: {len(movie_links)}")
    if movie_links:
        print(f"  Example: {movie_links[0]}")
except Exception as e:
    print(f"  Error: {e}")

# Test /movie/ (singular with trailing slash)
print("\n3. Testing /movie/...")
try:
    req = urllib.request.Request('https://streamimdb.ru/movie/', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    final_url = resp.geturl()
    print(f"  Final URL: {final_url}")
    print(f"  Response length: {len(html)} chars")
except Exception as e:
    print(f"  Error: {e}")

# Look for any page with movie content
print("\n4. Testing search on StreamIMDB...")
try:
    query = "batman"
    encoded = urllib.parse.quote(query)
    url = f"https://streamimdb.ru/?s={encoded}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    final_url = resp.geturl()
    print(f"  Final URL: {final_url}")
    print(f"  Response length: {len(html)} chars")
    
    movie_links = re.findall(r'href="(/movie/[^"]+)"', html)
    tv_links = re.findall(r'href="(/tv/[^"]+)"', html)
    print(f"  Movie links: {len(movie_links)}")
    print(f"  TV links: {len(tv_links)}")
    
    if movie_links:
        print(f"  Example: {movie_links[0]}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 60)
print("  Debug Complete")
print("=" * 60)
