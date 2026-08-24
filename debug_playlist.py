# -*- coding: utf-8 -*-
"""
Debug the IndStream playlist URL
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

# Get the player page
imdb_id = 'tt33014583'
player_url = f'https://slast430did.com/play/{imdb_id}'
print(f"Fetching player: {player_url}")

player_html = fetch(player_url, referer='https://hdmoviesapp.com/')

# Extract the file URL
file_m = re.search(r'"file"\s*:\s*"([^"]+)"', player_html)
if file_m:
    file_url = file_m.group(1).replace("\\", "")
    print(f"\nFile URL: {file_url}")

    # Fetch the playlist
    print(f"\nFetching playlist...")
    playlist = fetch(file_url, referer='https://slast430did.com/')
    print(f"Playlist length: {len(playlist)} chars")
    print(f"\nPlaylist content:")
    print(playlist[:2000])
else:
    print("No file URL found")
    # Save player HTML for debugging
    with open('D:\\updates\\player_debug.html', 'w', encoding='utf-8') as f:
        f.write(player_html)
    print("Saved player HTML to player_debug.html")
