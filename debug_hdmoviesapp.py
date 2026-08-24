# -*- coding: utf-8 -*-
"""
Reverse engineer hdmoviesapp.com
"""

import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url, referer=None):
    hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    if referer:
        hdrs['Referer'] = referer
    req = urllib.request.Request(url, headers=hdrs)
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        return resp.read().decode('utf-8', errors='ignore'), resp.geturl()
    except Exception as e:
        return "", url

print("=" * 60)
print("Reverse Engineering hdmoviesapp.com")
print("=" * 60)

# Test homepage
print("\n1. Testing homepage...")
html, final_url = fetch('https://hdmoviesapp.com/')
print(f"   Final URL: {final_url}")
print(f"   Response length: {len(html)} chars")

# Look for navigation
nav_links = re.findall(r'href="([^"]+)"', html)
print(f"\n   All links: {len(nav_links)}")

# Find unique path prefixes
paths = set()
for l in nav_links:
    if l.startswith('/') and not l.startswith('//'):
        parts = l.strip('/').split('/')
        if parts[0]:
            paths.add(parts[0])
print(f"   Path prefixes: {sorted(paths)[:20]}")

# Look for movie links
movie_patterns = [
    r'href="([^"]*/movie/[^"]*)"',
    r'href="([^"]*/watch/[^"]*)"',
    r'href="([^"]*/play/[^"]*)"',
    r'href="([^"]*-movie-[^"]*)"',
    r'href="([^"]*\d{4}[^"]*)"',  # Year-based URLs
]

for pattern in movie_patterns:
    links = re.findall(pattern, html, re.I)
    if links:
        print(f"\n   Pattern {pattern}: {len(links)} links")
        for l in links[:5]:
            print(f"      - {l}")

# Look for article/item containers
articles = re.findall(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
print(f"\n   Articles: {len(articles)}")

divs = re.findall(r'<div[^>]*class="[^"]*(?:movie|item|card|post)[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
print(f"   Movie divs: {len(divs)}")

# Look for search form
search_forms = re.findall(r'<form[^>]*action="([^"]*)"[^>]*>.*?</form>', html, re.DOTALL | re.I)
print(f"\n   Search forms: {len(search_forms)}")
for f in search_forms[:3]:
    print(f"      {f[:200]}")

# Look for search input
search_inputs = re.findall(r'<input[^>]*name="([^"]*)"[^>]*>', html, re.I)
print(f"   Input names: {search_inputs}")

# Look for pagination
pagination = re.findall(r'href="([^"]*[?:]page=\d+[^"]*)"', html)
print(f"\n   Pagination links: {len(pagination)}")
for p in pagination[:5]:
    print(f"      {p}")

# Test a specific movie page if found
print("\n2. Looking for sample movie URLs...")
sample_urls = re.findall(r'href="([^"]+)"', html)
movie_urls = [u for u in sample_urls if any(x in u.lower() for x in ['movie', 'watch', '2024', '2025', '2026'])]
print(f"   Potential movie URLs: {len(movie_urls)}")
for u in movie_urls[:10]:
    print(f"      {u}")
