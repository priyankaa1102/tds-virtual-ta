import json
import os
import time
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Constants
COURSE_URL = "https://tds.s-anand.net/#/2025-01/"
DISCOURSE_URL = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34"
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "tds_data.json"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

def classify_resource(url):
    if "youtube" in url:
        return "video"
    elif url.endswith(".pdf"):
        return "pdf"
    elif "colab" in url:
        return "notebook"
    elif url.endswith(".html"):
        return "html"
    return "link"

def scrape_course_content(driver):
    print("Scraping course content...")
    driver.get(COURSE_URL)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    course_data = {"weeks": {}}
    weeks = soup.find_all('div', class_='week-container')

    for week in weeks:
        week_title = week.find('h2').text.strip() if week.find('h2') else "Untitled"
        links = week.find_all('a', href=True)
        course_data["weeks"][week_title] = [
            {
                "title": link.text.strip(),
                "url": link["href"],
                "type": classify_resource(link["href"])
            }
            for link in links if link.text.strip()
        ]
    return course_data

def scrape_discourse(driver):
    print("Scraping Discourse posts...")
    all_posts = []
    driver.get(DISCOURSE_URL)
    time.sleep(5)

    while True:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        rows = soup.find_all('tr', class_='topic-list-item')

        for row in rows:
            try:
                title_el = row.find('a', class_='title')
                if not title_el:
                    continue

                title = title_el.text.strip()
                url = "https://discourse.onlinedegree.iitm.ac.in" + title_el['href']
                tags = [tag.text.strip() for tag in row.find_all('a', class_='discourse-tag')]
                date_el = row.find('span', class_='relative-date')
                date = date_el['title'] if date_el else None

                all_posts.append({
                    "title": title,
                    "url": url,
                    "tags": tags,
                    "date": date
                })
            except Exception as e:
                print(f"Error parsing a row: {e}")

        next_button = soup.find('a', class_='next')
        if next_button and 'href' in next_button.attrs:
            next_url = "https://discourse.onlinedegree.iitm.ac.in" + next_button['href']
            driver.get(next_url)
            time.sleep(3)
        else:
            break

    return all_posts

def save_data(course_content, discourse_posts):
    print(f"Saving data to {DATA_FILE}")
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({
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
        }, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("Starting scrape...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        course_content = scrape_course_content(driver)
        discourse_posts = scrape_discourse(driver)
        save_data(course_content, discourse_posts)
        print("✅ Scraping complete!")
    finally:
        driver.quit()
