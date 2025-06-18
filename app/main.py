from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path

app = FastAPI(title="TDS Virtual TA", version="1.0")

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

class APIResponse(BaseModel):
    answer: str
    links: list[dict]

DATA_FILE = Path("data/tds_data.json")

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "TDS Virtual TA API",
        "endpoints": {
            "/api": "POST - Submit questions",
            "/health": "GET - Service status"
        }
    }

# Main Q&A endpoint
@app.post("/api/")
def answer_question(request: QuestionRequest):
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        return {
            "answer": f"Found {len(data.get('posts', []))} relevant resources",
            "links": data.get("posts", [])[:3]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok", "ready": True}
