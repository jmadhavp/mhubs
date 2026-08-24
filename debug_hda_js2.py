# -*- coding: utf-8 -*-
"""
Find the actual AJAX endpoint in HDMoviesApp
"""

import urllib.request
import urllib.parse
import ssl
import re
import sys

# Force UTF-8 output
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

# Find all scripts
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)

print("Looking for player-related JavaScript...")
for i, s in enumerate(scripts):
    if any(x in s.lower() for x in ['player', 'ajax', 'stream', 'embed', 'play', 'dooplay']):
        print(f"\n{'='*60}")
        print(f"Script {i}:")
        print(f"{'='*60}")
        # Write to file to avoid encoding issues
        with open(f'D:\\updates\\script_{i}.txt', 'w', encoding='utf-8') as f:
            f.write(s)
        print(f"  (saved to script_{i}.txt, length: {len(s)})")

# Also look for the player option data
print("\n\nPlayer options HTML:")
player_opts = re.findall(r'<li[^>]*dooplay_player_option[^>]*>.*?</li>', html, re.DOTALL)
for opt in player_opts[:5]:
    with open('D:\\updates\\player_option.txt', 'w', encoding='utf-8') as f:
        f.write(opt)
    print(f"  (saved to player_option.txt)")

# Look for the full player options list
player_list = re.search(r'<ul[^>]*id="playeroptionsul[^"]*"[^>]*>(.*?)</ul>', html, re.DOTALL)
if player_list:
    with open('D:\\updates\\player_list.txt', 'w', encoding='utf-8') as f:
        f.write(player_list.group(1))
    print(f"\nPlayer list saved to player_list.txt")

# Look for the playbox
playbox = re.search(r'<div[^>]*class="[^"]*playbox[^"]*"[^>]*>.*?</div>', html, re.DOTALL)
if playbox:
    with open('D:\\updates\\playbox.txt', 'w', encoding='utf-8') as f:
        f.write(playbox.group(0))
    print(f"Playbox saved to playbox.txt")
