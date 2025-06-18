#!/bin/bash
cd /app
python app/scraper.py && \
cp data/tds_data.json data/backup_$(date +%Y%m%d).json
