# -*- coding: utf-8 -*-
"""
Debug StreamIMDB movie detail page - find all player options
"""

import urllib.request
import urllib.parse
import ssl
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url, referer=None):
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    if referer:
        hdrs["Referer"] = referer
    req = urllib.request.Request(url, headers=hdrs)
    resp = urllib.request.urlopen(req, context=ctx, timeout=20)
    return resp.read().decode("utf-8", errors="ignore"), resp.geturl()

# Test the movie detail page
url = 'https://streamimdb.ru/movie/3w6dy-dhurandhar'
print(f"Fetching: {url}")

html, final_url = fetch(url, referer='https://streamimdb.ru/')
print(f"Final URL: {final_url}")
print(f"Response length: {len(html)} chars")

# Look for player options
print("\n" + "=" * 60)
print("Player Options")
print("=" * 60)

# Player tabs/options
player_tabs = re.findall(r'<li[^>]*data-(?:embed|source|id)="([^"]+)"[^>]*>([^<]*)</li>', html)
print(f"\nPlayer tabs: {len(player_tabs)}")
for tab in player_tabs[:10]:
    print(f"  {tab[1].strip()} -> {tab[0]}")

# data-embed attributes
data_embeds = re.findall(r'data-embed="([^"]+)"', html)
print(f"\ndata-embed: {len(data_embeds)}")
for d in data_embeds[:10]:
    print(f"  {d}")

# data-source attributes
data_sources = re.findall(r'data-source="([^"]+)"', html)
print(f"\ndata-source: {len(data_sources)}")
for d in data_sources[:10]:
    print(f"  {d}")

# data-id attributes
data_ids = re.findall(r'data-id="([^"]+)"', html)
print(f"\ndata-id: {len(data_ids)}")
for d in data_ids[:10]:
    print(f"  {d}")

# iframes
iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html, re.I)
print(f"\nIframes: {len(iframes)}")
for i in iframes[:10]:
    print(f"  {i}")

# Save the HTML
with open('D:\\updates\\streamimdb_detail.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("\nSaved to streamimdb_detail.html")
