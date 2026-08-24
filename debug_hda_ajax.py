# -*- coding: utf-8 -*-
"""
Test HDMoviesApp AJAX player endpoint
"""

import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url, referer=None, data=None):
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
    }
    if referer:
        hdrs["Referer"] = referer
    if data:
        data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, headers=hdrs, data=data)
    resp = urllib.request.urlopen(req, context=ctx, timeout=20)
    return resp.read().decode("utf-8", errors="ignore")

# Get the movie page first to extract necessary data
movie_url = 'https://hdmoviesapp.com/191940-dhurandhar.html'
print(f"Fetching movie page: {movie_url}")

html = fetch(movie_url)

# Extract dle_login_hash
dle_hash = re.search(r"var dle_login_hash = '([^']+)'", html)
print(f"dle_login_hash: {dle_hash.group(1) if dle_hash else 'NOT FOUND'}")

# Extract post ID
post_id = re.search(r'data-post="(\d+)"', html)
print(f"Post ID: {post_id.group(1) if post_id else 'NOT FOUND'}")

# Extract IMDB ID
imdb_id = re.search(r'data-imdb="([^"]+)"', html)
print(f"IMDB ID: {imdb_id.group(1) if imdb_id else 'NOT FOUND'}")

# Try different AJAX endpoints
base = "https://hdmoviesapp.com"
endpoints = [
    "/engine/ajax/controller.php?mod=player",
    "/engine/ajax/player.php",
    "/engine/ajax/controller.php",
    "/engine/ajax/play.php",
    "/engine/ajax/embed.php",
]

for ep in endpoints:
    url = base + ep
    print(f"\n\nTesting: {url}")
    try:
        # Try POST with different data formats
        data_formats = [
            {"mod": "player", "post_id": post_id.group(1) if post_id else "191940"},
            {"action": "player", "post_id": post_id.group(1) if post_id else "191940"},
            {"mod": "player", "id": post_id.group(1) if post_id else "191940", "imdb": imdb_id.group(1) if imdb_id else "tt33014583"},
        ]
        for data in data_formats:
            try:
                resp = fetch(url, referer=movie_url, data=data)
                if resp and len(resp) > 50:
                    print(f"  Data: {data}")
                    print(f"  Response length: {len(resp)}")
                    print(f"  First 500 chars: {resp[:500]}")
                    break
            except Exception as e:
                print(f"  Data {data}: {str(e)[:50]}")
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")
