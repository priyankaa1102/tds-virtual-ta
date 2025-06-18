import os
from pathlib import Path

# Add this near the top of your file (replace existing DATA_FILE definition)
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)  # Creates directory if doesn't exist
DATA_FILE = DATA_DIR / "tds_data.json"

# Then modify your save_data function:
def save_data(course_content, discourse_posts):
    """Save scraped data to JSON with directory creation"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "last_updated": datetime.now().isoformat(),
                "course_content": course_content,
                "discourse_posts": discourse_posts
            }, f, indent=2, ensure_ascii=False)
        print(f"Data successfully saved to {DATA_FILE}")
    except Exception as e:
        print(f"Failed to save data: {str(e)}")
        raise
