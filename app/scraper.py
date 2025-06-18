import json
import time
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# Output file
DATA_FILE = Path("data/tds_data.json")
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

COURSE_URL = "https://tds.s-anand.net/#/2025-01/"
DISCOURSE_URL = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34"

def classify_resource(url: str) -> str:
    """Heuristic to classify course content links"""
    if "quiz" in url.lower():
        return "quiz"
    if "video" in url.lower():
        return "video"
    if "assignment" in url.lower():
        return "assignment"
    return "resource"

def scrape_course_content(driver):
    print("🔍 Scraping course content...")
    driver.get(COURSE_URL)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    course_data = {"weeks": {}}
    week_blocks = soup.find_all("div", class_="week-container")

    for block in week_blocks:
        week_title = block.find("h2")
        if not week_title:
            continue
        week_title = week_title.text.strip()

        links = block.find_all("a", href=True)
        resources = []
        for a in links:
            href = a["href"]
            title = a.text.strip()
            if href and title:
                resources.append({
                    "title": title,
                    "url": href,
                    "type": classify_resource(href)
                })

        if resources:
            course_data["weeks"][week_title] = resources

    return course_data

def scrape_discourse(driver):
    print("🗨️ Scraping Discourse posts...")
    all_posts = []
    page = 0

    while True:
        page += 1
        driver.get(f"{DISCOURSE_URL}?page={page}")
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        rows = soup.select("tr.topic-list-item")
        if not rows:
            break

        for row in rows:
            link = row.find("a", class_="title")
            if not link:
                continue

            href = link.get("href", "")
            title = link.text.strip()
            if not href or not title:
                continue

            tags = [tag.text for tag in row.select("a.discourse-tag")]
            date_span = row.find("span", class_="relative-date")
            date = date_span.get("title") if date_span else ""

            all_posts.append({
                "title": title,
                "url": f"https://discourse.onlinedegree.iitm.ac.in{href}",
                "tags": tags,
                "date": date
            })

    return all_posts

def save_data(course_content, discourse_posts):
    data = {
        "last_updated": datetime.now().isoformat(),
        "course_content": course_content,
        "discourse_posts": discourse_posts,
        "metadata": {
            "course_url": COURSE_URL,
            "discourse_url": DISCOURSE_URL,
            "date_range": {
                "start": "2025-01-01T00:00:00",
                "end": "2025-04-14T00:00:00"
            }
        }
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Data saved to {DATA_FILE}")

if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        course = scrape_course_content(driver)
        posts = scrape_discourse(driver)
        save_data(course, posts)
    finally:
        driver.quit()
