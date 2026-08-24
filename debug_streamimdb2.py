# -*- coding: utf-8 -*-
"""
Debug StreamIMDB get_latest issue
"""

import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://streamimdb.ru/movies'
print(f"Fetching: {url}")

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, context=ctx, timeout=15)
html = resp.read().decode('utf-8', errors='ignore')
final_url = resp.geturl()
print(f"Final URL: {final_url}")
print(f"Response length: {len(html)} chars")

# Look for movie links with different patterns
print("\nLooking for movie links...")

# Pattern 1: /movie/ (with leading slash)
links1 = re.findall(r'href="(/movie/[^"]+)"', html)
print(f"Pattern /movie/: {len(links1)}")

# Pattern 2: /movies/ (plural)
links2 = re.findall(r'href="(/movies/[^"]+)"', html)
print(f"Pattern /movies/: {len(links2)}")

# Pattern 3: Any link with "movie" in it
links3 = re.findall(r'href="([^"]*movie[^"]*)"', html, re.I)
print(f"Pattern *movie*: {len(links3)}")

# Pattern 4: Look for article or card structures
articles = re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL)
print(f"Articles: {len(articles)}")

# Pattern 5: Look for any links
all_links = re.findall(r'href="([^"]+)"', html)
print(f"Total links: {len(all_links)}")

# Show some example links
print("\nExample links:")
for l in all_links[:20]:
    if not l.startswith('#') and not l.startswith('javascript'):
        print(f"  {l}")

# Show movie links if found
if links1:
    print("\nMovie links (/movie/):")
    for l in links1[:10]:
        print(f"  {l}")
