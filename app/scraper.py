import json
import os
import time
import requests
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Constants
DISCOURSE_URL = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34"

# Configure paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "tds_data.json"

def classify_resource(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "video"
    elif url.endswith(".pdf"):
        return "pdf"
    elif "quiz" in url.lower():
        return "quiz"
    return "link"

def scrape_course_content():
    print("Scraping course content...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get("https://tds.s-anand.net/#/2025-01/")
        time.sleep(6)  # let JS load
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        course_data = {"weeks": {}}
        week_divs = soup.find_all("div", class_="week-container")
        
        for week_div in week_divs:
            week_title = week_div.find("h2")
            week_name = week_title.text.strip() if week_title else "Untitled Week"
            links = week_div.find_all("a", href=True)

            course_data["weeks"][week_name] = [
                {
                    "title": link.text.strip(),
                    "url": link['href'],
                    "type": classify_resource(link['href'])
                }
                for link in links
            ]
        return course_data
    finally:
        driver.quit()

def scrape_discourse():
    print("Scraping Discourse posts...")
    session = requests.Session()
    all_posts = []
    page = 0

    while True:
        page += 1
        url = f"{DISCOURSE_URL}?page={page}"
        print(f"Processing {url}")
        resp = session.get(url)
        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        topic_links = soup.select("a.title")

        if not topic_links:
            break

        for link in topic_links:
            topic_url = "https://discourse.onlinedegree.iitm.ac.in" + link['href']
            all_posts.append({
                "title": link.text.strip(),
                "url": topic_url,
                "tags": [],
                "date": datetime.now().isoformat()
            })

        time.sleep(1)
    return all_posts

def save_data(course_content, discourse_posts):
    metadata = {
        "course_url": "https://tds.s-anand.net/#/2025-01/",
        "discourse_url": DISCOURSE_URL,
        "date_range": {
            "start": "2025-01-01T00:00:00",
            "end": "2025-04-14T00:00:00"
        }
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "last_updated": datetime.now().isoformat(),
            "course_content": course_content,
            "discourse_posts": discourse_posts,
            "metadata": metadata
        }, f, indent=2, ensure_ascii=False)
    print(f"✅ Data saved to {DATA_FILE}")

if __name__ == "__main__":
    try:
        course_data = scrape_course_content()
        posts_data = scrape_discourse()
        save_data(course_data, posts_data)
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
