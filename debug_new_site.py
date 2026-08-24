# -*- coding: utf-8 -*-
"""
Debug StreamIMDB embed page and hdmoviesapp.com
"""

import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Test StreamIMDB embed page
print("=" * 60)
print("Testing StreamIMDB embed page")
print("=" * 60)

embed_url = 'https://streamimdb.ru/embed/movie/1291608'
print(f"\nFetching: {embed_url}")

try:
    req = urllib.request.Request(embed_url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://streamimdb.ru/'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    final_url = resp.geturl()
    print(f"Final URL: {final_url}")
    print(f"Response length: {len(html)} chars")

    # Look for stream URLs
    m3u8_urls = re.findall(r'(https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*)', html)
    mp4_urls = re.findall(r'(https?://[^"\'\s<>]+\.mp4[^"\'\s<>]*)', html)
    print(f"\nm3u8 URLs: {len(m3u8_urls)}")
    for m in m3u8_urls[:5]:
        print(f"  {m}")
    print(f"mp4 URLs: {len(mp4_urls)}")
    for m in mp4_urls[:5]:
        print(f"  {m}")

    # Look for iframes
    iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html, re.I)
    print(f"\nIframes: {len(iframes)}")
    for i in iframes[:5]:
        print(f"  {i}")

    # Look for file/source URLs in scripts
    file_urls = re.findall(r'(?:file|src|url)\s*[:=]\s*["\']([^"\']+)["\']', html)
    print(f"\nFile URLs in scripts: {len(file_urls)}")
    for f in file_urls[:10]:
        if f.startswith('http'):
            print(f"  {f}")

    # Show first 1000 chars of HTML
    print("\n\nFirst 1000 chars of embed page:")
    print(html[:1000])

except Exception as e:
    print(f"Error: {e}")

# Test hdmoviesapp.com
print("\n\n" + "=" * 60)
print("Testing hdmoviesapp.com")
print("=" * 60)

urls_to_try = [
    'https://hdmoviesapp.com/',
    'https://hdmoviesapp.com/movies',
    'https://hdmoviesapp.com/latest',
]

for url in urls_to_try:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        html = resp.read().decode('utf-8', errors='ignore')
        final_url = resp.geturl()
        print(f"\n{url}")
        print(f"  -> {final_url} ({len(html)} chars)")

        # Look for movie links
        movie_links = re.findall(r'href="([^"]*(?:movie|watch|play)[^"]*)"', html, re.I)
        print(f"  Movie links: {len(movie_links)}")
        for l in movie_links[:5]:
            print(f"    - {l}")

        # Look for article/div containers
        articles = re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL)
        print(f"  Articles: {len(articles)}")

    except Exception as e:
        print(f"\n{url} -> ERROR: {str(e)[:80]}")
