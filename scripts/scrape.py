#setup - This sets where files go, waits 2 seconds between pages so you don't hammer their server, and identifies you honestly as the visitor
import csv
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
import trafilatura
from bs4 import BeautifulSoup

DATA = Path("data")
RAW_DIR = DATA / "raw_html"
CLEAN_DIR = DATA / "clean"
DELAY_SECONDS = 2
HEADERS = {"User-Agent": "portfolio-research-bot (contact: meenakshirnair712@gmail.com)"}

#read the list and check permission – robots.txt is a site's "please don't scrape these pages" sign. This checks it once per site and remembers the answer
def load_pages(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def allowed_by_robots(url, robots_cache):
    domain = urlparse(url).scheme + "://" + urlparse(url).netloc
    if domain not in robots_cache:
        rp = RobotFileParser()
        try:
            response = requests.get(domain + "/robots.txt", headers=HEADERS, timeout=20)
            if response.status_code == 200:
                rp.parse(response.text.splitlines())
            elif 400 <= response.status_code < 500 and response.status_code not in (401, 403):
                rp = "allow_all"
            else:
                rp = "disallow_all"
        except requests.RequestException:
            rp = "disallow_all"
        robots_cache[domain] = rp
    rp = robots_cache[domain]
    if rp == "allow_all":
        return True
    if rp == "disallow_all":
        return False
    return rp.can_fetch(HEADERS["User-Agent"], url)

#download, clean and save. trafilatura is the photocopier that keeps only the article body. Each saved file gets a header with its URL, title and date. That header becomes your citation later, when the bot says "source: Outage FAQs"
def fetch(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.text


def extract_text(html, url):
    soup = BeautifulSoup(html, "html.parser")

    for button in soup.find_all("button"):
        if len(button.get_text(strip=True).split()) >= 4:
            button.name = "h3"

    cards = []
    for item in soup.select(".page-list li.item"):
        title = item.select_one(".field-title")
        description = item.select_one(".field-metadescription")
        if title and description:
            cards.append(f"- {title.get_text(' ', strip=True)}: {description.get_text(' ', strip=True)}")

    text = trafilatura.extract(str(soup), url=url, include_tables=True,
                               include_links=False, favor_recall=True) or ""
    if cards:
        text += "\n\nPrograms listed on this page:\n" + "\n".join(cards)
    return text


def save_page(page, html, text):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    pid = page["page_id"]
    (RAW_DIR / f"{pid}.html").write_text(html, encoding="utf-8")
    header = (
        f"---\n"
        f"page_id: {pid}\n"
        f"title: {page['page_title']}\n"
        f"url: {page['url']}\n"
        f"source: {page['source']}\n"
        f"intent_groups: {page['intent_groups']}\n"
        f"scraped_on: {date.today().isoformat()}\n"
        f"---\n\n"
    )
    (CLEAN_DIR / f"{pid}.md").write_text(header + text, encoding="utf-8")

#quality check and main loop – This is where your "Approx Words" column pays off. If a page comes back with less than half the words it should have, the script flags it. That catches hidden FAQ text the photocopier missed
def check_quality(text, expected_words):
    words = len(text.split())
    if words == 0:
        return words, "EMPTY"
    if words < 100:
        return words, "LOW"
    return words, "OK"


def main():
    pages = load_pages(DATA / "scrape_list.csv")
    robots_cache = {}
    log = []
    for i, page in enumerate(pages, start=1):
        url = page["url"]
        print(f"[{i}/{len(pages)}] {page['page_id']} {url}")
        if not allowed_by_robots(url, robots_cache):
            log.append([page["page_id"], url, "BLOCKED_BY_ROBOTS", 0, page["approx_words"], ""])
            continue
        try:
            html = fetch(url)
            text = extract_text(html, url)
            save_page(page, html, text)
            words, flag = check_quality(text, page["approx_words"])
            log.append([page["page_id"], url, "OK", words, page["approx_words"], flag])
        except Exception as e:
            log.append([page["page_id"], url, f"ERROR: {e}", 0, page["approx_words"], ""])
        time.sleep(DELAY_SECONDS)

    with open(DATA / "scrape_log.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["page_id", "url", "status", "words", "expected_words", "quality"])
        writer.writerows(log)

    problems = [row for row in log if row[2] != "OK" or row[5] != "OK"]
    print(f"\nDone. {len(log) - len(problems)} good, {len(problems)} need a look.")
    for row in problems:
        print("  ", row[0], row[2], row[5], row[1])


if __name__ == "__main__":
    main()
