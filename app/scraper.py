import json
import time
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# URLs
COURSE_URL = "https://tds.s-anand.net/#/2025-01/"
DISCOURSE_URL = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34"

# Data path
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "tds_data.json"

def classify_resource(href: str) -> str:
    if "slides" in href.lower():
        return "slides"
    if "video" in href.lower():
        return "video"
    if "quiz" in href.lower():
        return "quiz"
    if "assignment" in href.lower():
        return "assignment"
    return "link"

def scrape_course_content(driver) -> dict:
    print("Scraping course content...")
    driver.get(COURSE_URL)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    course_data = {"weeks": {}}

    all_h2 = soup.find_all("h2")
    for h2 in all_h2:
        week_title = h2.get_text(strip=True)
        links = h2.find_next_siblings("a")
        week_resources = []
        for link in links:
            if not link.has_attr("href"):
                continue
            title = link.get_text(strip=True)
            url = link["href"]
            res_type = classify_resource(url)
            week_resources.append({
                "title": title,
                "url": url,
                "type": res_type
            })
        if week_resources:
            course_data["weeks"][week_title] = week_resources

    return course_data

def scrape_discourse(driver) -> list:
    print("Scraping Discourse posts...")
    driver.get(DISCOURSE_URL)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    posts = []

    rows = soup.find_all("tr", class_="topic-list-item")
    for row in rows:
        title_tag = row.find("a", class_="title")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        url = "https://discourse.onlinedegree.iitm.ac.in" + title_tag["href"]
        tags = [t.get_text(strip=True) for t in row.find_all("a", class_="discourse-tag")]
        date_tag = row.find("span", class_="relative-date")
        date = date_tag["title"] if date_tag else ""

        posts.append({
            "title": title,
            "url": url,
            "tags": tags,
            "date": date
        })

    return posts

def save_data(course, posts):
    print("Saving data...")
    json_data = {
        "last_updated": datetime.now().isoformat(),
        "course_content": course,
        "discourse_posts": posts,
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
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Data saved to {DATA_FILE}")

if __name__ == "__main__":
    try:
        options = webdriver.ChromeOptions()
        # Comment this out if you want to see the browser
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        course = scrape_course_content(driver)
        posts = scrape_discourse(driver)
        save_data(course, posts)

        driver.quit()
        print("✅ Scraping complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
