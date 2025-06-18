import json
import os
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Configure paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "tds_data.json"

def scrape_course_content():
    print("Scraping course content...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        driver.get("https://tds.s-anand.net/#/2025-01/")
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        course_data = {"weeks": {}}
        weeks = soup.find_all('div', class_='week-container') or \
               soup.find_all('div', {'id': lambda x: x and 'week' in x.lower()})
        
        for week in weeks:
            week_title = week.find('h2').text.strip() if week.find('h2') else "Untitled"
            course_data["weeks"][week_title] = [
                {
                    "title": res.text.strip(),
                    "url": res['href'],
                    "type": classify_resource(res['href'])
                }
                for res in week.find_all('a', href=True)
            ]
        return course_data
    finally:
        driver.quit()

def scrape_discourse():
    print("Scraping Discourse posts...")
    session = requests.Session()
    all_posts = []
    page = 1
    
    while True:
        print(f"Processing page {page}...")
        response = session.get(f"{DISCOURSE_URL}?page={page}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for topic in soup.find_all('tr', class_='topic-list-item'):
            all_posts.append({
                "title": topic.find('a', class_='title').text.strip(),
                "url": f"https://discourse.onlinedegree.iitm.ac.in{topic.find('a')['href']}",
                "tags": [tag.text for tag in topic.find_all('a', class_='discourse-tag')],
                "date": topic.find('span', class_='relative-date')['title']
            })
        
        if not soup.find('a', class_='next'):
            break
        page += 1
        time.sleep(1)
    
    return all_posts

def save_data(course_content, discourse_posts):
    """Save data with proper error handling"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "last_updated": datetime.now().isoformat(),
                "course_content": course_content,
                "discourse_posts": discourse_posts
            }, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {DATA_FILE}")
    except Exception as e:
        print(f"Failed to save data: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        course = scrape_course_content()
        posts = scrape_discourse()
        save_data(course, posts)
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
