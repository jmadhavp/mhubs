# -*- coding: utf-8 -*-
"""
Debug - Check sitemap from both domains
"""

import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Test sitemap from .icu
print("Testing sitemap from hdmovie2a.icu...")
try:
    req = urllib.request.Request('https://hdmovie2a.icu/movies-sitemap.xml', headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    xml = resp.read().decode('utf-8', errors='ignore')
    final_url = resp.geturl()
    urls = re.findall(r'<loc>([^<]+)</loc>', xml)
    print(f"  Final URL: {final_url}")
    print(f"  URLs found: {len(urls)}")
    if urls:
        print(f"  First URL: {urls[0]}")
except Exception as e:
    print(f"  Error: {e}")

# Test search URL from .icu
print("\nTesting search from hdmovie2a.icu...")
try:
    query = "action"
    encoded = urllib.parse.quote(query)
    url = f"https://hdmovie2a.icu/?s={encoded}"
    print(f"  Search URL: {url}")
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    final_url = resp.geturl()
    print(f"  Final URL: {final_url}")
    print(f"  Response length: {len(html)} chars")
    
    # Check for redirect to .bar
    if "hdmovie2a.bar" in final_url:
        print("  REDIRECTED to .bar domain!")
    
    # Look for search results
    articles = re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL)
    print(f"  Articles found: {len(articles)}")
    
    # Look for "no results"
    if "no results" in html.lower() or "nothing found" in html.lower():
        print("  'No results' message found")
        
except Exception as e:
    print(f"  Error: {e}")

# Test direct site search
print("\nTesting direct site search on hdmovie2a.bar...")
try:
    query = "action"
    encoded = urllib.parse.quote(query)
    url = f"https://hdmovie2a.bar/?s={encoded}"
    print(f"  Search URL: {url}")
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    final_url = resp.geturl()
    print(f"  Final URL: {final_url}")
    print(f"  Response length: {len(html)} chars")
    
    articles = re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL)
    print(f"  Articles found: {len(articles)}")
    
    if articles:
        # Extract titles
        for a in articles[:3]:
            title_m = re.search(r'aria-label="([^"]*)"', a)
            if title_m:
                print(f"    - {title_m.group(1)}")
        
except Exception as e:
    print(f"  Error: {e}")
