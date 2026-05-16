import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.shl.com"
CATALOG_URL = f"{BASE_URL}/solutions/products/product-catalog/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def get_detail(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for selector in [".product-description", ".overview", "main p", ".content p"]:
            el = soup.select_one(selector)
            if el and len(el.text.strip()) > 30:
                return el.text.strip()[:500]
        return ""
    except Exception:
        return ""


def parse_page(html: str, seen_urls: set) -> list:
    soup = BeautifulSoup(html, "html.parser")
    assessments = []
    for row in soup.select("tr"):
        link_el = row.select_one("a[href*='/product-catalog/view/']")
        if not link_el:
            continue
        name = link_el.text.strip()
        href = link_el.get("href", "")
        if not href or not name:
            continue
        url = href if href.startswith("http") else "https://www.shl.com/solutions" + href
        if url in seen_urls:
            continue
        seen_urls.add(url)
        type_els = row.select(".product-catalogue__key")
        test_type = ", ".join(el.text.strip() for el in type_els) if type_els else "Unknown"
        assessments.append({"name": name, "url": url, "test_type": test_type, "remote": "", "description": ""})
    return assessments


def scrape_catalog():
    from playwright.sync_api import sync_playwright
    assessments = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(user_agent=HEADERS["User-Agent"])
        page.goto(CATALOG_URL)
        page.wait_for_timeout(6000)

        # dismiss cookie banner if it shows up
        try:
            page.click("#CybotCookiebotDialogBodyButtonAccept", timeout=3000)
            page.wait_for_timeout(2000)
        except Exception:
            pass

        page_num = 1
        while True:
            print(f"  Scraping page {page_num}...")
            html = page.content()
            if page_num == 1:
                with open("catalog_raw.html", "w", encoding="utf-8") as f:
                    f.write(html)
            new_items = parse_page(html, seen_urls)
            assessments.extend(new_items)
            print(f"    {len(new_items)} items (total: {len(assessments)})")

            try:
                next_btn = page.query_selector("li.pagination__item.-arrow.-next:not(.-disabled) a")
                if not next_btn:
                    break
                next_btn.click()
                page.wait_for_timeout(3000)
                page_num += 1
            except Exception:
                break

        browser.close()

    print(f"\nCollected {len(assessments)} assessments across {page_num} pages")

    print("Fetching product descriptions...")
    for i, a in enumerate(assessments):
        print(f"  [{i+1}/{len(assessments)}] {a['name']}")
        a["description"] = get_detail(a["url"])
        time.sleep(0.4)

    with open("catalog.json", "w", encoding="utf-8") as f:
        json.dump(assessments, f, indent=2, ensure_ascii=False)

    print(f"Done! Saved {len(assessments)} assessments to catalog.json")
    return assessments


if __name__ == "__main__":
    data = scrape_catalog()
    for item in data[:3]:
        print(json.dumps(item, indent=2))