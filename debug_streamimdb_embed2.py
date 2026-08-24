# -*- coding: utf-8 -*-
"""
Debug StreamIMDB embed page
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

# Test the embed page
url = 'https://streamimdb.ru/embed/movie/1291608'
print(f"Fetching: {url}")

html, final_url = fetch(url, referer='https://streamimdb.ru/')
print(f"Final URL: {final_url}")
print(f"Response length: {len(html)} chars")

# Save the HTML
with open('D:\\updates\\streamimdb_embed.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Saved to streamimdb_embed.html")

# Show full HTML
print("\nFull HTML:")
print(html)
