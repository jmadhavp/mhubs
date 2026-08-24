# -*- coding: utf-8 -*-
"""
Find the actual AJAX endpoint in HDMoviesApp
"""

import urllib.request
import urllib.parse
import ssl
import re

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

# Find all scripts
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)

print("Looking for player-related JavaScript...")
for i, s in enumerate(scripts):
    if any(x in s.lower() for x in ['player', 'ajax', 'stream', 'embed', 'play']):
        print(f"\n{'='*60}")
        print(f"Script {i}:")
        print(f"{'='*60}")
        print(s[:2000])
        print("...")
