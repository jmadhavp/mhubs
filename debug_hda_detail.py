# -*- coding: utf-8 -*-
"""
Debug HDMoviesApp detail page to find player/embed structure
"""

import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    req = urllib.request.Request(url, headers=hdrs)
    resp = urllib.request.urlopen(req, context=ctx, timeout=20)
    return resp.read().decode("utf-8", errors="ignore"), resp.geturl()

# Test a movie detail page
url = 'https://hdmoviesapp.com/191940-dhurandhar.html'
print(f"Fetching: {url}")

html, final_url = fetch(url)
print(f"Final URL: {final_url}")
print(f"Response length: {len(html)} chars")

# Look for iframes
iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html, re.I)
print(f"\nIframes: {len(iframes)}")
for i in iframes[:10]:
    print(f"  {i}")

# Look for data attributes
data_attrs = re.findall(r'data-(?:src|url|embed|link|video|source)="([^"]+)"', html, re.I)
print(f"\nData attributes: {len(data_attrs)}")
for d in data_attrs[:10]:
    print(f"  {d}")

# Look for player divs
player_divs = re.findall(r'<div[^>]*(?:id|class)="[^"]*(?:player|video|embed|watch)[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL | re.I)
print(f"\nPlayer divs: {len(player_divs)}")
for p in player_divs[:3]:
    print(f"  {p[:200]}...")

# Look for m3u8/mp4
m3u8 = re.findall(r'(https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*)', html)
mp4 = re.findall(r'(https?://[^"\'\s<>]+\.mp4[^"\'\s<>]*)', html)
print(f"\nm3u8: {len(m3u8)}, mp4: {len(mp4)}")

# Look for any embed URLs
embed_urls = re.findall(r'(https?://[^"\'\s<>]*(?:embed|player|stream|watch)[^"\'\s<>]*)', html)
print(f"\nEmbed URLs: {len(embed_urls)}")
for e in embed_urls[:10]:
    print(f"  {e}")

# Look for buttons/links that might trigger player
buttons = re.findall(r'<(?:a|button)[^>]*href="([^"]+)"[^>]*>([^<]*)</(?:a|button)>', html)
print(f"\nButtons: {len(buttons)}")
for b in buttons[:10]:
    print(f"  {b[1].strip()[:30]} -> {b[0][:60]}")

# Show first 2000 chars around player section
print("\n\nFirst 3000 chars of HTML:")
print(html[:3000])
