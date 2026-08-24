# -*- coding: utf-8 -*-
"""
Fetch the player.js file
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

# Fetch the player.js
player_url = 'https://allmovieland.link/player.js?v=5'
print(f"Fetching: {player_url}")

js = fetch(player_url, referer='https://hdmoviesapp.com/')
with open('D:\\updates\\player.js', 'w', encoding='utf-8') as f:
    f.write(js)
print(f"Saved to player.js, length: {len(js)}")

# Also fetch the front.scripts.min.js
front_url = 'https://hdmoviesapp.com/templates/hdmovie/js/front.scripts.min.js?v=4'
print(f"\nFetching: {front_url}")
js2 = fetch(front_url, referer='https://hdmoviesapp.com/')
with open('D:\\updates\\front_scripts.js', 'w', encoding='utf-8') as f:
    f.write(js2)
print(f"Saved to front_scripts.js, length: {len(js2)}")

# Also fetch libs.js
libs_url = 'https://hdmoviesapp.com/templates/hdmovie/js/libs.js?v=0.7'
print(f"\nFetching: {libs_url}")
js3 = fetch(libs_url, referer='https://hdmoviesapp.com/')
with open('D:\\updates\\libs.js', 'w', encoding='utf-8') as f:
    f.write(js3)
print(f"Saved to libs.js, length: {len(js3)}")
