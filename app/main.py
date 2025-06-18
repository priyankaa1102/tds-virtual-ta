from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path
import logging
from thefuzz import fuzz  # For fuzzy matching

# Initialize logging
logging.basicConfig(
    filename='api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="TDS Virtual TA", version="1.0")

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

class Resource(BaseModel):
    title: str
    url: str
    source: str  # 'discourse' or 'course'
    type: Optional[str] = None  # For course resources
    tags: Optional[list] = None  # For discourse posts
    week: Optional[str] = None  # For course resources

class APIResponse(BaseModel):
    answer: str
    links: list[Resource]

DATA_FILE = Path("data/tds_data.json")

def load_data():
    """Load and validate scraped data"""
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        
        # Validate data structure
        if not isinstance(data.get("discourse_posts", []), list):
            raise ValueError("Invalid discourse posts format")
        if not isinstance(data.get("course_content", {}).get("weeks", {}), dict):
            raise ValueError("Invalid course content format")
            
        return data
    except Exception as e:
        logging.error(f"Data loading failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Data service unavailable. Please try again later."
        )

@app.post("/api/", response_model=APIResponse)
def answer_question(request: QuestionRequest):
    """Enhanced search endpoint with fuzzy matching"""
    try:
        data = load_data()
        query = request.question.lower()
        results = []
        logging.info(f"New query: {query}")

        # Search discourse posts
        for post in data.get("discourse_posts", []):
            title = post.get("title", "").lower()
            tags = [tag.lower() for tag in post.get("tags", [])]
            
            # Fuzzy match with title and tags
            if (fuzz.partial_ratio(query, title) > 70 or
                any(fuzz.partial_ratio(query, tag) > 80 for tag in tags)):
                
                results.append(Resource(
                    title=post["title"],
                    url=post["url"],
                    source="discourse",
                    tags=post.get("tags", [])
                ))

        # Search course content
        for week, resources in data.get("course_content", {}).get("weeks", {}).items():
            for resource in resources:
                if fuzz.partial_ratio(query, resource["title"].lower()) > 70:
                    results.append(Resource(
                        title=resource["title"],
                        url=resource["url"],
                        source="course",
                        type=resource.get("type"),
                        week=week
                    ))

        # Sort by relevance (simple heuristic)
        results.sort(
            key=lambda x: max(
                fuzz.partial_ratio(query, x.title.lower()),
                max(fuzz.partial_ratio(query, tag) for tag in x.tags or []) if x.tags else 0
            ),
            reverse=True
        )

        return APIResponse(
            answer=f"Found {len(results)} relevant resources",
            links=results[:10]  # Return top 10 most relevant
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

@app.get("/health")
def health_check():
    """Service health endpoint"""
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

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return ""
