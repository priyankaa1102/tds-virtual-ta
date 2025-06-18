import json
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import requests

# Constants
COURSE_URL = "https://tds.s-anand.net/#/2025-01/"
DISCOURSE_URL = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34"
START_DATE = "2025-01-01"
END_DATE = "2025-04-14"

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "tds_data.json"
DATA_DIR.mkdir(exist_ok=True)

def classify_resource(href):
    if 'pdf' in href:
        return 'pdf'
    elif 'youtube' in href:
        return 'video'
    elif 'quiz' in href:
        return 'quiz'
    return 'link'

def scrape_course_content():
    print("Scraping course content...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get(COURSE_URL)
        time.sleep(6)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        course_data = {"weeks": {}}
        week_containers = soup.find_all("div", class_="week-container")

        for week_div in week_containers:
            heading = week_div.find("h2")
            if not heading:
                continue
            week_title = heading.get_text(strip=True)
            resources = []
            for link in week_div.find_all("a", href=True):
                resources.append({
                    "title": link.get_text(strip=True),
                    "url": link["href"],
                    "type": classify_resource(link["href"])
                })
            course_data["weeks"][week_title] = resources
        return course_data
    finally:
        driver.quit()

def scrape_discourse():
    print("Scraping Discourse posts...")
    all_posts = []
    page = 0
    session = requests.Session()
    
    while True:
        page += 1
        print(f"Discourse page {page}")
        res = session.get(f"{DISCOURSE_URL}?page={page}")
        if res.status_code != 200:
            break

        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.find_all("tr", class_="topic-list-item")
        if not rows:
            break

        for row in rows:
            try:
                a_tag = row.find("a", class_="title")
                if not a_tag:
                    continue
                url = f"https://discourse.onlinedegree.iitm.ac.in{a_tag['href']}"
                title = a_tag.get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in row.find_all("a", class_="discourse-tag")]
                date_span = row.find("span", class_="relative-date")
                date = date_span["title"] if date_span else None
                all_posts.append({
                    "title": title,
                    "url": url,
                    "tags": tags,
                    "date": date
                })
            except Exception as e:
                print(f"Error parsing row: {e}")
        time.sleep(1)
    return all_posts

def save_data(course, discourse):
    print(f"Saving data to {DATA_FILE}")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": datetime.now().isoformat(),
            "course_content": course,
            "discourse_posts": discourse,
            "metadata": {
                "course_url": COURSE_URL,
                "discourse_url": DISCOURSE_URL,
                "date_range": {
                    "start": START_DATE + "T00:00:00",
                    "end": END_DATE + "T00:00:00"
                }
            }
        }, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    try:
        course = scrape_course_content()
        discourse = scrape_discourse()
        save_data(course, discourse)
    except Exception as e:
        print(f"Scraping failed: {e}")
