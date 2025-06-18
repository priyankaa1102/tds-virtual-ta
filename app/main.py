from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

class APIResponse(BaseModel):
    answer: str
    links: list[dict]

DATA_FILE = Path("data/tds_data.json")

@app.post("/api/")
def answer_question(request: QuestionRequest):
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        return {
            "answer": f"Found {len(data['posts'])} relevant resources",
            "links": data["posts"][:3]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
