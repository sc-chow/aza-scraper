import csv
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL = "https://www.aza.org/find-a-zoo-or-aquarium?locale=en"


def fetch_page(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page.goto(url, wait_until="networkidle", timeout=60000)
        # Scroll to ensure dynamically loaded list elements are in DOM
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()
        return html


def parse_facilities(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    facilities = []

    content_area = soup.find("main") or soup.find("body") or soup
    current_section = "Accredited Zoo/Aquarium"

    # Iterate over headers, paragraphs, list items, and containers directly
    elements = content_area.find_all(["h2", "h3", "h4", "p", "li", "div"])

    for element in elements:
        # Avoid processing large parent containers that enclose full sections
        if len(element.find_all(["p", "li"])) > 1 and element.name not in ["p", "li"]:
            continue

        raw_text = element.get_text(" ", strip=True)

        # Update section headers dynamically
        if re.search(r"Certified Related Facility|Related Facilities", raw_text, re.IGNORECASE):
            current_section = "Related Facility"
            continue
        elif re.search(r"Accredited Zoos|Accredited Aquariums|AZA-Accredited", raw_text, re.IGNORECASE):
            if "through" not in raw_text.lower():  # Exclude individual facility lines
                current_section = "Accredited Zoo/Aquarium"
                continue

        # Skip entries without accreditation details
        if not re.search(r"Accredited through|Certified through", raw_text, re.IGNORECASE):
            continue

        a_tag = element.find("a", href=True)
        if not a_tag:
            continue

        name = a_tag.get_text(strip=True)
        if not name or len(name) <= 2:
            continue

        # Extract Expiration Date
        acc_match = re.search(
            r"(?:Accredited|Certified)\s+through\s+([A-Za-z]+\s+\d{4})",
            raw_text,
            re.IGNORECASE,
        )
        accredited_through = acc_match.group(1).strip() if acc_match else ""

        # Extract Location
        location = ""
        # Match text between name and accreditation note
        loc_match = re.search(
            r"^\s*" + re.escape(name) + r"\s*[\,\–\-]?\s*(.*?)\s*(?:\(?(?:Accredited|Certified)\s+through|\(also accredited|$)",
            raw_text,
            re.IGNORECASE,
        )
        if loc_match:
            location = loc_match.group(1).strip().strip(",-– ")

        # Fallback location extraction if initial regex fails
        if not location and a_tag.next_sibling:
            sibling_text = str(a_tag.next_sibling).strip()
            sibling_text = re.sub(r"^\s*,\s*", "", sibling_text)
            location = re.split(r"Accredited|Certified|\(", sibling_text, flags=re.IGNORECASE)[0].strip().rstrip(",")

        # Extract AAM Accreditation Flag
        also_aam = bool(re.search(r"American Alliance of Museums|\bAAM\b", raw_text))

        entry = {
            "name": name,
            "location": location,
            "website": a_tag["href"],
            "accredited_through": accredited_through,
            "also_aam_accredited": also_aam,
            "section": current_section,
        }

        # Deduplicate while preserving order
        if not any(f["name"] == entry["name"] and f["website"] == entry["website"] for f in facilities):
            facilities.append(entry)

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
    print(f"Successfully wrote {len(facilities)} rows to {path}")


if __name__ == "__main__":
    html = fetch_page(URL)
    facilities = parse_facilities(html)
    save_csv(facilities)