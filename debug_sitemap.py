# -*- coding: utf-8 -*-
"""
Debug - Check actual sitemap content and search URLs
"""

import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("Checking actual sitemap content...")

# Check HDMovie2 sitemap
req = urllib.request.Request('https://hdmovie2a.icu/movies-sitemap.xml', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, context=ctx, timeout=15)
xml = resp.read().decode('utf-8', errors='ignore')
urls = re.findall(r'<loc>([^<]+)</loc>', xml)

print(f"Total URLs in sitemap: {len(urls)}")
print("\nFirst 10 URLs:")
for u in urls[:10]:
    print(f"  {u}")

# Test search query
q = "action"
matches = [u for u in urls if q in u.lower()]
print(f"\nURLs containing '{q}': {len(matches)}")
for u in matches[:10]:
    print(f"  {u}")

# Check what's in the URLs
print("\nAnalyzing URL patterns...")
domains = set()
for u in urls:
    parsed = urllib.parse.urlparse(u)
    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) >= 2:
        domains.add(path_parts[0])
print(f"Path prefixes: {domains}")
