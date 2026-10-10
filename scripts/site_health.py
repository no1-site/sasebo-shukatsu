#!/usr/bin/env python3
"""Daily public-site health checks for the Sasebo end-of-life consultation site.

Uses only Python standard library. Does not access leads, GA4, or Google Ads.
"""
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://no1-site.github.io/sasebo-shukatsu/"
PAGES = (
    BASE,
    BASE + "sasebo-hakajimai-guide.html",
    BASE + "sasebo-kaiso-permit.html",
    BASE + "sasebo-hakajimai-cost.html",
    BASE + "privacy.html",
)
SITEMAP = BASE + "sitemap.xml"
ROBOTS = BASE + "robots.txt"
HEADERS = {"User-Agent": "sasebo-shukatsu-site-health/1.0"}


def fetch(url):
    last_error = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                return response.read()
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt != 2:
                time.sleep(2)
    raise RuntimeError(str(last_error))


def main():
    problems = []

    for url in PAGES:
        try:
            body = fetch(url).lower()
            if b"<html" not in body or b"<title" not in body:
                problems.append(f"Invalid HTML or missing title: {url}")
                print(f"NG HTML: {url}")
            elif b'<meta name="robots" content="noindex' in body:
                problems.append(f"Unexpected noindex meta tag: {url}")
                print(f"NG noindex: {url}")
            else:
                print(f"OK HTML: {url}")
        except Exception as exc:
            problems.append(f"Cannot fetch HTML: {url} ({exc})")
            print(f"NG HTML: {url} ({exc})")

    try:
        root = ET.fromstring(fetch(SITEMAP))
        namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        if root.tag != namespace + "urlset":
            raise ValueError("Not a standard sitemap urlset")
        listed = {
            node.text.strip()
            for node in root.findall(f"{namespace}url/{namespace}loc")
            if node.text
        }
        missing = set(PAGES) - listed
        if missing:
            raise ValueError("Missing sitemap URLs: " + ", ".join(sorted(missing)))
        print(f"OK sitemap XML: {SITEMAP} ({len(listed)} URLs)")
    except Exception as exc:
        problems.append(f"Sitemap problem: {exc}")
        print(f"NG sitemap: {exc}")

    try:
        robots = fetch(ROBOTS).decode("utf-8")
        if SITEMAP not in robots:
            raise ValueError("Sitemap declaration is missing")
        print(f"OK robots.txt: {ROBOTS}")
    except Exception as exc:
        problems.append(f"robots.txt problem: {exc}")
        print(f"NG robots.txt: {exc}")

    if problems:
        print("\nSite health check failed:")
        for p in problems:
            print("- " + p)
        return 1

    print("\nAll public-site checks passed.")
    print("Note: This does not verify Google Search Console indexing or GA4/Ads delivery.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
