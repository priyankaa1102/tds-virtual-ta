import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
from datetime import datetime
import time
from pathlib import Path

# Configuration
COURSE_URL = "https://tds.s-anand.net/#/2025-01/"
DISCOURSE_URL = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34"
DATA_FILE = Path("data/tds_data.json")
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 4, 14)

def scrape_course_content():
    """Scrape official course materials using Selenium"""
    print("Scraping course content...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(COURSE_URL)
    
    # Wait for dynamic content to load
    time.sleep(5)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    course_data = {"weeks": {}}
    
    # Extract week containers - adjust selector based on actual page structure
    week_containers = soup.find_all('div', class_='week-container') or \
                     soup.find_all('div', {'id': lambda x: x and 'week' in x.lower()})
    
    for week in week_containers:
        week_title = week.find('h2').text.strip() if week.find('h2') else "Untitled Week"
        week_data = []
        
        # Extract resources (videos, slides, notebooks)
        for resource in week.find_all('a', href=True):
            resource_url = resource['href']
            if not resource_url.startswith('http'):
                resource_url = COURSE_URL + resource_url.lstrip('/')
            
            week_data.append({
                "title": resource.text.strip(),
                "url": resource_url,
                "type": classify_resource(resource_url)
            })
        
        course_data["weeks"][week_title] = week_data
    
    driver.quit()
    return course_data

def classify_resource(url: str) -> str:
    """Categorize resources by type"""
    url = url.lower()
    if "youtube.com" in url: return "video"
    if ".ipynb" in url: return "notebook"
    if ".pdf" in url: return "slides"
    return "document"

def scrape_discourse_posts():
    """Scrape Discourse posts within date range"""
    print("Scraping Discourse posts...")
    session = requests.Session()
    all_posts = []
    page = 1
    
    while True:
        print(f"Processing page {page}...")
        response = session.get(f"{DISCOURSE_URL}?page={page}")
        soup = BeautifulSoup(response.text, 'html.parser')
        posts_found = False
        
        for topic in soup.find_all('tr', class_='topic-list-item'):
            post_date_str = topic.find('span', class_='relative-date')['title']
            post_date = datetime.strptime(post_date_str, "%Y-%m-%dT%H:%M:%SZ")
            
            # Skip posts outside our date range
            if not (START_DATE <= post_date <= END_DATE):
                continue
                
            posts_found = True
            all_posts.append({
                "title": topic.find('a', class_='title').text.strip(),
                "url": f"https://discourse.onlinedegree.iitm.ac.in{topic.find('a')['href']}",
                "tags": [tag.text for tag in topic.find_all('a', class_='discourse-tag')],
                "date": post_date_str,
                "is_solution": 'is-solution' in topic.get('class', [])
            })
        
        # Stop if we've reached the start date or end of posts
        if not posts_found or post_date < START_DATE:
            break
            
        page += 1
        time.sleep(1)  # Be polite to the server
    
    return all_posts

def save_data(course_content, discourse_posts):
    """Save scraped data to JSON"""
    data = {
        "last_updated": datetime.now().isoformat(),
        "course_content": course_content,
        "discourse_posts": discourse_posts,
        "metadata": {
            "course_url": COURSE_URL,
            "discourse_url": DISCOURSE_URL,
            "date_range": {
                "start": START_DATE.isoformat(),
                "end": END_DATE.isoformat()
            }
        }
    }
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Data saved to {DATA_FILE}")

def main():
    try:
        course_content = scrape_course_content()
        discourse_posts = scrape_discourse_posts()
        save_data(course_content, discourse_posts)
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
