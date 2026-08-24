# -*- coding: utf-8 -*-
"""
Debug StreamIMDB movie detail page to find actual player URLs
"""

import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Test movie detail page
url = 'https://streamimdb.ru/movie/3w6dy-dhurandhar'
print(f"Fetching: {url}")

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, context=ctx, timeout=15)
html = resp.read().decode('utf-8', errors='ignore')
final_url = resp.geturl()
print(f"Final URL: {final_url}")
print(f"Response length: {len(html)} chars")

# Look for player/embed URLs
print("\n" + "=" * 60)
print("Looking for player/embed URLs...")
print("=" * 60)

# YouTube links
yt_links = re.findall(r'(https?://(?:www\.)?youtube(?:-nocookie)?\.com/(?:embed|watch|v)/[^"\'\s<>]+)', html)
print(f"\nYouTube links: {len(yt_links)}")
for l in yt_links[:5]:
    print(f"  {l}")

# iframe embeds
iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html, re.I)
print(f"\nIframes: {len(iframes)}")
for i in iframes[:10]:
    print(f"  {i}")

# video/source tags
video_tags = re.findall(r'<(?:video|source)[^>]+src="([^"]+)"', html, re.I)
print(f"\nVideo/Source tags: {len(video_tags)}")
for v in video_tags[:5]:
    print(f"  {v}")

# Look for data attributes with URLs
data_urls = re.findall(r'data-(?:src|url|embed|link|video)="([^"]+)"', html, re.I)
print(f"\nData URLs: {len(data_urls)}")
for d in data_urls[:10]:
    print(f"  {d}")

# Look for m3u8/mp4 URLs
m3u8_urls = re.findall(r'(https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*)', html)
mp4_urls = re.findall(r'(https?://[^"\'\s<>]+\.mp4[^"\'\s<>]*)', html)
print(f"\nm3u8 URLs: {len(m3u8_urls)}")
for m in m3u8_urls[:5]:
    print(f"  {m}")
print(f"mp4 URLs: {len(mp4_urls)}")
for m in mp4_urls[:5]:
    print(f"  {m}")

# Look for player divs
print("\n" + "=" * 60)
print("Looking for player containers...")
print("=" * 60)

player_divs = re.findall(r'<div[^>]*id="(?:player|video-player|main-player)"[^>]*>(.*?)</div>', html, re.DOTALL | re.I)
print(f"Player divs: {len(player_divs)}")

# Look for any script with player config
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"\nScripts: {len(scripts)}")
for i, s in enumerate(scripts):
    if 'player' in s.lower() or 'embed' in s.lower() or 'source' in s.lower() or 'm3u8' in s.lower():
        print(f"\nScript {i} (player-related, first 500 chars):")
        print(s[:500])
