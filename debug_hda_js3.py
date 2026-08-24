# -*- coding: utf-8 -*-
"""
Find the player JavaScript file
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
    return resp.read().decode("utf-8", errors="ignore")

# Get the movie page
movie_url = 'https://hdmoviesapp.com/191940-dhurandhar.html'
html = fetch(movie_url)

# Find all script src
script_srcs = re.findall(r'<script[^>]+src="([^"]+)"', html)
print("External scripts:")
for s in script_srcs:
    if 'player' in s.lower() or 'dooplay' in s.lower() or 'dle' in s.lower():
        print(f"  {s}")

# Also get all scripts
print("\nAll scripts:")
for s in script_srcs:
    print(f"  {s}")

# Fetch the player-related scripts
for s in script_srcs:
    if 'player' in s.lower() or 'dooplay' in s.lower():
        full_url = s if s.startswith('http') else 'https://hdmoviesapp.com' + s
        print(f"\n\nFetching: {full_url}")
        js = fetch(full_url, referer=movie_url)
        with open(f'D:\\updates\\js_{s.split("/")[-1]}', 'w', encoding='utf-8') as f:
            f.write(js)
        print(f"  Saved to js_{s.split('/')[-1]}, length: {len(js)}")
