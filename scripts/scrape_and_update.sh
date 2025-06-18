#!/bin/bash

# Navigate to project root
cd "$(dirname "$0")/.."

# Run the scraper and handle errors
if python app/scraper.py; then
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Scraping completed successfully"
    
    # Create timestamped backup (keeps last 5 backups)
    cp data/tds_data.json "data/backup_$(date +'%Y%m%d_%H%M%S').json"
    ls -t data/backup_*.json | tail -n +6 | xargs rm -f
    
    # Optional: Restart API to load new data
    # pkill -f uvicorn
    # uvicorn app.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
else
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Scraping failed"
    exit 1
fi
