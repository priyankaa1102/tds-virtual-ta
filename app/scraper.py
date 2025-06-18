import requests
from bs4 import BeautifulSoup
import json

def scrape_discourse():
    url = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = []
    for topic in soup.find_all('tr', class_='topic-list-item'):
        posts.append({
            "title": topic.find('a', class_='title').text.strip(),
            "url": "https://discourse.onlinedegree.iitm.ac.in" + topic.find('a')['href']
        })
    
    with open('data/tds_data.json', 'w') as f:
        json.dump({"posts": posts}, f)

if __name__ == "__main__":
    scrape_discourse()
