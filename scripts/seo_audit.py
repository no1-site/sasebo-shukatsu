#!/usr/bin/env python3
"""Check repository SEO essentials before and during daily site monitoring.

No API keys or paid services are needed. Only local repository files are read.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://no1-site.github.io/sasebo-shukatsu/"
FILES = (
    "index.html",
    "sasebo-hakajimai-guide.html",
    "sasebo-kaiso-permit.html",
    "sasebo-hakajimai-cost.html",
    "blog.html",
    "privacy.html",
)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_text = []
        self.in_title = False
        self.description = ""
        self.canonical = ""
        self.robots = ""
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attrs.get("name", "").lower() == "description":
            self.description = attrs.get("content", "").strip()
        if tag == "meta" and attrs.get("name", "").lower() == "robots":
            self.robots = attrs.get("content", "").lower()
        if tag == "link" and attrs.get("rel", "").lower() == "canonical":
            self.canonical = attrs.get("href", "").strip()
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text.append(data)


def local_link_target(link, source):
    parts = urlsplit(link)
    if parts.scheme and parts.scheme not in ("https", "http"):
        return None
    if parts.netloc:
        if parts.scheme + "://" + parts.netloc + parts.path == BASE.rstrip("/"):
            return "index.html"
        if not link.startswith(BASE):
            return None
        path = link[len(BASE):].split("?", 1)[0].split("#", 1)[0]
    else:
        path = parts.path
        if not path:
            return None
        if path.startswith("/"):
            # Absolute site-root paths are not relative to this GitHub Pages project.
            return None

    path = unquote(path)
    if path in (".", "./", ""):
        return "index.html"
    if path.startswith("./"):
        path = path[2:]
    target = (Path(source).parent / path)
    if target.suffix == "":
        return str(target / "index.html")
    return str(target)


def main():
    problems = []
    titles = {}
    expected_urls = set()

    for filename in FILES:
        path = ROOT / filename
        if not path.is_file():
            problems.append(f"Missing page: {filename}")
            continue

        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        title = "".join(parser.title_text).strip()
        expected = BASE if filename == "index.html" else BASE + filename
        expected_urls.add(expected)

        if not title:
            problems.append(f"{filename}: missing title")
        elif title in titles:
            problems.append(f"Duplicate title: {filename} and {titles[title]}")
        else:
            titles[title] = filename

        if len(parser.description) < 35:
            problems.append(f"{filename}: missing or very short meta description")
        if parser.canonical != expected:
            problems.append(f"{filename}: canonical mismatch ({parser.canonical})")
        if "noindex" in parser.robots:
            problems.append(f"{filename}: unexpected noindex")

        for link in parser.links:
            target = local_link_target(link, filename)
            if target is not None and not (ROOT / target).is_file():
                problems.append(f"{filename}: broken internal link {link}")
        print(f"Checked page SEO: {filename}")

    try:
        tree = ET.parse(ROOT / "sitemap.xml")
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        actual_urls = {
            node.text.strip()
            for node in tree.findall(f"{ns}url/{ns}loc")
            if node.text
        }
        for url in sorted(expected_urls - actual_urls):
            problems.append(f"URL missing from sitemap: {url}")
        text_sitemap_urls = {
            line.strip()
            for line in (ROOT / "sitemap.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        if text_sitemap_urls != actual_urls:
            problems.append("sitemap.txt URLs differ from sitemap.xml; update both files together")
        print(f"Checked XML/text sitemap references: {len(actual_urls)} URLs")
    except (OSError, ET.ParseError) as exc:
        problems.append(f"Cannot validate sitemap: {exc}")

    if problems:
        print("\nSEO audit found problems:")
        for problem in problems:
            print("- " + problem)
        return 1

    print("\nSEO audit passed: titles, descriptions, canonicals, links and sitemap.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
