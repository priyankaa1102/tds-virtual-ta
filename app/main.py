from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path
import logging
from thefuzz import fuzz

# === Setup Logging ===
logging.basicConfig(
    filename='api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# === FastAPI App ===
app = FastAPI(title="TDS Virtual TA", version="1.0")

# === Pydantic Models ===
class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None  # Reserved for future use

class Resource(BaseModel):
    title: str
    url: str
    source: str  # 'discourse' or 'course'
    type: Optional[str] = None
    tags: Optional[List[str]] = None
    week: Optional[str] = None

class APIResponse(BaseModel):
    answer: str
    links: List[Resource]

# === Constants ===
DATA_FILE = Path("data/tds_data.json")

# === Utility: Load and validate JSON ===
def load_data():
    if not DATA_FILE.exists():
        logging.error("Data file missing")
        raise HTTPException(status_code=503, detail="Data not available yet.")
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data.get("discourse_posts", []), list):
            raise ValueError("Invalid discourse format")
        if not isinstance(data.get("course_content", {}).get("weeks", {}), dict):
            raise ValueError("Invalid course format")
        return data
    except Exception as e:
        logging.exception("Failed to load data")
        raise HTTPException(status_code=503, detail="Failed to read data.")

# === Main API Endpoint ===
@app.post("/api/", response_model=APIResponse)
def answer_question(request: QuestionRequest):
    query = request.question.lower()
    data = load_data()
    results = []
    logging.info(f"Query received: {query}")

    # --- Search Discourse Posts ---
    for post in data.get("discourse_posts", []):
        title = post.get("title", "").lower()
        tags = [tag.lower() for tag in post.get("tags", [])]
        if fuzz.partial_ratio(query, title) > 70 or any(fuzz.partial_ratio(query, tag) > 80 for tag in tags):
            results.append(Resource(
                title=post["title"],
                url=post["url"],
                source="discourse",
                tags=post.get("tags", [])
            ))

    # --- Search Course Content ---
    for week, resources in data.get("course_content", {}).get("weeks", {}).items():
        for res in resources:
            res_title = res.get("title", "").lower()
            if fuzz.partial_ratio(query, res_title) > 70:
                results.append(Resource(
                    title=res["title"],
                    url=res["url"],
                    source="course",
                    type=res.get("type"),
                    week=week
                ))

    # --- Sort Results by Relevance ---
    results.sort(
        key=lambda x: max(
            fuzz.partial_ratio(query, x.title.lower()),
            max([fuzz.partial_ratio(query, tag) for tag in x.tags], default=0) if x.tags else 0
        ),
        reverse=True
    )

    return APIResponse(
        answer=f"Found {len(results)} relevant resources" if results else "No relevant resources found.",
        links=results[:10]
    )

# === Health Check Endpoint ===
@app.get("/health")
def health_check():
    try:
        data = load_data()
        return {
            "status": "healthy",
            "stats": {
                "discourse_posts": len(data.get("discourse_posts", [])),
                "course_weeks": len(data.get("course_content", {}).get("weeks", {}))
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }

# === Favicon Override ===
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return ""
