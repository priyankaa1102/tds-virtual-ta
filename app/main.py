from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path
from .config import DATA_PATH

app = FastAPI(title="TDS Virtual TA", version="1.0")

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None  # Base64 encoded image (future use)

class ResourceLink(BaseModel):
    url: str
    text: str

class APIResponse(BaseModel):
    answer: str
    links: List[ResourceLink]

def load_knowledge_base():
    """Load scraped data from JSON"""
    try:
        with open(DATA_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"Data loading failed: {str(e)}"
        )

@app.post("/api/", response_model=APIResponse)
async def answer_question(request: QuestionRequest):
    """Main question-answering endpoint"""
    knowledge_base = load_knowledge_base()
    question = request.question.lower()
    results = {"answer": "", "links": []}
    
    # Search course content
    for week, resources in knowledge_base["course_content"]["weeks"].items():
        for resource in resources:
            if question in resource["title"].lower():
                results["links"].append(
                    ResourceLink(
                        url=resource["url"],
                        text=f"{week}: {resource['title']}"
                    )
                )
    
    # Search Discourse posts
    for post in knowledge_base["discourse_posts"]:
        if (question in post["title"].lower() or 
            any(question in tag.lower() for tag in post.get("tags", []))):
            results["links"].append(
                ResourceLink(url=post["url"], text=post["title"])
            )
    
    results["answer"] = (
        "Found relevant resources:" if results["links"] 
        else "No matches found. Try rephrasing or ask on Discourse."
    )
    return results

@app.get("/health")
async def health_check():
    """Service health endpoint"""
    return {
        "status": "healthy",
        "data_stats": {
            "weeks_loaded": len(load_knowledge_base()["course_content"]["weeks"]),
            "posts_loaded": len(load_knowledge_base()["discourse_posts"])
        }
    }
