import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
from .config import DATA_PATH
import time

def scrape_discourse(max_pages: int = 3) -> list:
    """Scrape TDS Discourse forum"""
    base_url = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34"
    session = requests.Session()
    results = []

    for page in range(1, max_pages + 1):
        try:
            response = session.get(f"{base_url}?page={page}", timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for topic in soup.find_all('tr', class_='topic-list-item'):
                results.append({
                    "title": topic.find('a', class_='title').text.strip(),
                    "url": f"https://discourse.onlinedegree.iitm.ac.in{topic.find('a')['href']}",
                    "tags": [tag.text for tag in topic.find_all('a', class_='discourse-tag')],
                    "activity": topic.find('span', class_='relative-date')['title']
                })
        except Exception as e:
            print(f"Error scraping page {page}: {str(e)}")
    
    return results

def scrape_course_content() -> dict:
    """Scrape official course materials"""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://tds.s-anand.net/#/2025-01/")
    time.sleep(5)  # Wait for dynamic content
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    course_data = {"weeks": {}}
    
    # Adjust selectors based on actual page structure
    weeks = soup.find_all('div', class_='week-container') or \
            soup.find_all('div', {'id': lambda x: x and 'week' in x.lower()})
    
    for week in weeks:
        week_title = week.find('h2').text.strip() if week.find('h2') else "Untitled"
        week_data = []
        
        for resource in week.find_all('a', href=True):
            week_data.append({
                "title": resource.text.strip(),
                "url": resource['href'],
                "type": classify_resource(resource['href'])
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

def update_knowledge_base():
    """Main scraping function"""
    data = {
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "course_content": scrape_course_content(),
        "discourse_posts": scrape_discourse()
    }
    
    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    update_knowledge_base()
