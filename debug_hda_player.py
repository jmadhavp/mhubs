# -*- coding: utf-8 -*-
"""
Debug HDMoviesApp player options and AJAX endpoints
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
    return resp.read().decode("utf-8", errors="ignore"), resp.geturl()

# Test a movie detail page
url = 'https://hdmoviesapp.com/191940-dhurandhar.html'
html, _ = fetch(url)

# Find player options
print("=" * 60)
print("Player Options")
print("=" * 60)

player_options = re.findall(r'<li[^>]*class="[^"]*dooplay_player_option[^"]*"[^>]*>', html)
print(f"\nPlayer options: {len(player_options)}")
for opt in player_options[:5]:
    print(f"  {opt}")

# Find data attributes in player options
player_data = re.findall(r'data-(?:type|pos|postid|source)="([^"]+)"', html)
print(f"\nData attributes: {player_data[:20]}")

# Look for AJAX endpoints
ajax_urls = re.findall(r'(?:action|url)\s*:\s*["\']([^"\']+)["\']', html)
print(f"\nAJAX URLs: {len(ajax_urls)}")
for a in ajax_urls[:10]:
    print(f"  {a}")

# Look for dle_ajax or similar
dle_ajax = re.findall(r'dle_ajax[^"\']*', html)
print(f"\ndle_ajax calls: {len(dle_ajax)}")

# Look for player AJAX function
player_ajax = re.findall(r'(?:player|play)_(?:ajax|url|action)\s*[:=]\s*["\']([^"\']+)["\']', html)
print(f"\nPlayer AJAX: {player_ajax}")

# Look for any script with player config
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"\nScripts: {len(scripts)}")
for i, s in enumerate(scripts):
    if 'player' in s.lower() or 'ajax' in s.lower():
        print(f"\nScript {i} (player/ajax related):")
        print(s[:500])
        print("---")

# Look for the playcontainer content
playcontainer = re.search(r'id="playcontainer"[^>]*>(.*?)</div>', html, re.DOTALL)
if playcontainer:
    print("\n\nPlaycontainer content:")
    print(playcontainer.group(1)[:1000])

# Look for dooplay_player_response
player_response = re.search(r'id="dooplay_player_response"[^>]*>(.*?)</div>', html, re.DOTALL)
if player_response:
    print("\n\nPlayer response content:")
    print(player_response.group(1)[:1000])
