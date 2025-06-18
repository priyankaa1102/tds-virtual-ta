# Base image
FROM python:3.9-slim

# Install system dependencies for Selenium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only necessary files (optimizes Docker layer caching)
COPY app/requirements.txt .
COPY app ./app
COPY scripts ./scripts
COPY data/sample_data.json ./data/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Initialize data directory
RUN mkdir -p /app/data && \
    chmod +x /app/scripts/scrape_and_update.sh

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

# Startup command (runs both API and scraper)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & /app/scripts/scrape_and_update.sh"]
