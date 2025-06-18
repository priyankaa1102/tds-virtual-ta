from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import os

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None  # Base64 encoded

class APIResponse(BaseModel):
    answer: str
    links: list[dict]

def load_data():
    try:
        with open('data/tds_data.json') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"posts": []}

@app.post("/api/")
def answer_question(request: QuestionRequest):
    data = load_data()
    return {
        "answer": f"Found {len(data['posts'])} relevant posts",
        "links": data["posts"][:3]  #
