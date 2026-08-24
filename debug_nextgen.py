# -*- coding: utf-8 -*-
"""
Debug nextgencloudfabric.com embed page
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
url = 'https://nextgencloudfabric.com/embed/movie/1291608'
print(f"Fetching: {url}")

html, final_url = fetch(url, referer='https://streamimdb.ru/')
print(f"Final URL: {final_url}")
print(f"Response length: {len(html)} chars")

# Look for m3u8
m3u8 = re.findall(r'(https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*)', html)
print(f"\nm3u8: {len(m3u8)}")
for m in m3u8[:5]:
    print(f"  {m}")

# Look for mp4
mp4 = re.findall(r'(https?://[^"\'\s<>]+\.mp4[^"\'\s<>]*)', html)
print(f"\nmp4: {len(mp4)}")
for m in mp4[:5]:
    print(f"  {m}")

# Look for file: variable
file_urls = re.findall(r'(?:file|src|url)\s*[:=]\s*["\']([^"\']+)["\']', html, re.I)
print(f"\nfile: variables: {len(file_urls)}")
for f in file_urls[:10]:
    if f.startswith('http'):
        print(f"  {f}")

# Look for iframes
iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html, re.I)
print(f"\nIframes: {len(iframes)}")
for i in iframes[:5]:
    print(f"  {i}")

# Save the HTML
with open('D:\\updates\\nextgen_page.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("\nSaved to nextgen_page.html")

# Show first 2000 chars
print("\nFirst 2000 chars:")
print(html[:2000])
