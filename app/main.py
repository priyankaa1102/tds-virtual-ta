from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path
import logging
from thefuzz import fuzz
from dotenv import load_dotenv
import os
import requests

# Load API token securely
load_dotenv()
AI_PROXY_TOKEN = os.getenv("AI_PROXY_TOKEN")

if not AI_PROXY_TOKEN:
    raise RuntimeError("Missing AI_PROXY_TOKEN. Set it in your .env file.")

app = FastAPI(title="TDS Virtual TA", version="1.0")

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

class Resource(BaseModel):
    title: str
    url: str
    source: str
    type: Optional[str] = None
    tags: Optional[list] = None
    week: Optional[str] = None

class APIResponse(BaseModel):
    answer: str
    links: List[Resource]

DATA_FILE = Path("data/tds_data.json")

def load_data():
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)

        if not isinstance(data.get("discourse_posts", []), list):
            raise ValueError("Invalid discourse posts format")
        if not isinstance(data.get("course_content", {}).get("weeks", {}), dict):
            raise ValueError("Invalid course content format")

        return data
    except Exception as e:
        logging.error(f"Data loading failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Data service unavailable.")

def query_ai_proxy(question: str) -> str:
    url = "https://api.proxy.onlinedegree.iitm.ac.in/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_PROXY_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful TA for the TDS course."},
            {"role": "user", "content": question}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logging.warning(f"AI Proxy fallback: {str(e)}")
        return "I'm not sure about that. Please check the course resources or Discourse."

@app.post("/api/", response_model=APIResponse)
def answer_question(request: QuestionRequest):
    data = load_data()
    query = request.question.lower()
    results = []

    # Search Discourse
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

    # Search Course Content
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

    results.sort(
        key=lambda x: max(
            fuzz.partial_ratio(query, x.title.lower()),
            max(fuzz.partial_ratio(query, tag) for tag in x.tags or []) if x.tags else 0
        ),
        reverse=True
    )

    # Get LLM-based answer regardless of resource count
    llm_answer = query_ai_proxy(request.question)

    return APIResponse(
        answer=llm_answer,
        links=results[:10]
    )

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
        return {"status": "degraded", "error": str(e)}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return ""
