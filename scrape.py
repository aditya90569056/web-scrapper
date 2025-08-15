import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os

# Keywords to detect editions or book mentions
KEYWORDS = [
    "meri yojana", "मेरी योजना",
    "प्रथम संस्करण", "first edition",
    "द्वितीय संस्करण", "second edition",
    "केन्द्र सरकार", "central government",
    "खंड", "भाग"
]

def fetch_soup(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if res.status_code == 200:
            return BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
    return None

def find_internal_links(soup, base_url):
    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("/") or base_url in href:
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.add(full_url)
    return list(links)

def extract_pdfs(soup, base_url):
    pdfs = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.lower().endswith(".pdf"):
            full_url = urljoin(base_url, href)
            filename = os.path.basename(urlparse(href).path)
            pdfs.append((filename, full_url))
    return pdfs

def scan_page(url, keyword_hits):
    soup = fetch_soup(url)
    if not soup:
        return

    print(f"\n🔍 Scanning: {url}")
    text = soup.get_text(separator=" ").lower()

    matched = False
    for kw in KEYWORDS:
        if kw.lower() in text:
            keyword_hits[kw.lower()].add(url)
            print(f"   ✅ Found keyword: '{kw}' at → {url}")
            matched = True

    pdfs = extract_pdfs(soup, url)
    if pdfs:
        print(f"   📄 Found {len(pdfs)} PDF(s):")
        for fname, link in pdfs:
            print(f"      - {fname} → {link}")
        matched = True

    if not matched:
        print("   ❌ No matching keywords or PDFs found.")

def main():
    # Prompt user for URL
    user_url = input("🔗 Enter the full URL of the page to scan: ").strip()
    if not user_url.startswith("http"):
        print("❌ Invalid URL. Please include http:// or https://")
        return

    print(f"\n🌐 Starting scan at: {user_url}")
    homepage = fetch_soup(user_url)
    if not homepage:
        print("❌ Failed to fetch the provided URL.")
        return

    keyword_hits = {kw.lower(): set() for kw in KEYWORDS}

    # Step 1: Scan the front page
    scan_page(user_url, keyword_hits)

    # Step 2: Find and scan sub-pages
    internal_links = find_internal_links(homepage, user_url)
    filtered_links = [url for url in internal_links if "/organization/" in url or "/schemes/" in url]

    print(f"\n📁 Found {len(filtered_links)} subpages to scan...\n")
    for link in filtered_links:
        scan_page(link, keyword_hits)

    # Final report
    print("\n🧾 Summary: Keywords Found\n" + "-" * 50)
    any_found = False
    for kw, urls in keyword_hits.items():
        if urls:
            any_found = True
            print(f"🔹 '{kw}' found at:")
            for u in urls:
                print(f"   - {u}")
    if not any_found:
        print("❌ No keywords matched on any page.")
    print("-" * 50)

if __name__ == "__main__":
    main()
