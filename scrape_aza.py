"""
Scraper for the AZA "Find a Zoo or Aquarium" accredited facilities list.
https://www.aza.org/find-a-zoo-or-aquarium?locale=en

The page is static server-rendered HTML (no JS needed), so requests +
BeautifulSoup is sufficient.

Each entry on the page follows this pattern:
    **[Name](url), Location**
    Accredited through <Month> <Year>
    (optional: *(also accredited by the American Alliance of Museums)*)

There are two sections: "Currently Accredited Zoos and Aquariums" and
"Current Accredited Related Facilities". This script captures both and
tags each row with which section it came from.

Output: aza_accredited_facilities.csv
"""

import csv
import re
import time
import requests
from bs4 import BeautifulSoup

URL = "https://www.aza.org/find-a-zoo-or-aquarium?locale=en"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Referer": "https://www.google.com/",
}


def fetch_page(url: str) -> str:
    # A plain session (rather than a one-off request) plus a first hit to
    # the homepage helps pick up any cookies the site sets before it will
    # serve the actual listing page.
    session = requests.Session()
    session.headers.update(HEADERS)
    session.get("https://www.aza.org/", timeout=30)
    time.sleep(1)
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_facilities(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # Get the main content area text, preserving line breaks between
    # block-level elements so our regex can work line-by-line.
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    main = soup.get_text(separator="\n")
    lines = [l.strip() for l in main.split("\n") if l.strip()]

    # Also build a lookup of link text -> href from the raw soup,
    # since get_text() strips URLs.
    link_map = {}
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        if text:
            link_map[text] = a["href"]

    facilities = []
    section = "Accredited Zoo/Aquarium"
    name_line_re = re.compile(r"^(.*?),\s*([A-Za-z .'\-]+)$")
    accredited_re = re.compile(r"^Accredited [Tt]hrough\s+(.+)$")

    i = 0
    while i < len(lines):
        line = lines[i]

        if "Current Accredited Related Facilities" in line:
            section = "Related Facility"
            i += 1
            continue

        # Stop once we hit the "Donate Now" footer content
        if line.startswith("Donate Now"):
            break

        m = accredited_re.match(line)
        if m and facilities:
            facilities[-1]["accredited_through"] = m.group(1).strip()
            i += 1
            continue

        if "(also accredited by the American Alliance of Museums)" in line and facilities:
            facilities[-1]["also_aam_accredited"] = True
            i += 1
            continue

        nm = name_line_re.match(line)
        if nm:
            name, location = nm.group(1).strip(), nm.group(2).strip()
            # Skip obvious false positives (nav links, etc.) shorter checks
            if len(name) > 2 and len(location) < 40:
                url = link_map.get(name, "")
                facilities.append(
                    {
                        "name": name,
                        "location": location,
                        "website": url,
                        "accredited_through": "",
                        "also_aam_accredited": False,
                        "section": section,
                    }
                )
        i += 1

    return facilities


def save_csv(facilities: list[dict], path: str = "aza_accredited_facilities.csv"):
    fieldnames = [
        "name",
        "location",
        "website",
        "accredited_through",
        "also_aam_accredited",
        "section",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(facilities)
    print(f"Wrote {len(facilities)} rows to {path}")


if __name__ == "__main__":
    html = fetch_page(URL)
    facilities = parse_facilities(html)
    save_csv(facilities)