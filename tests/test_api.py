from fastapi.testclient import TestClient
from app.main import app
import json
import os

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_answer_endpoint(tmp_path):
    # Setup test data
    test_data = {
        "posts": [
            {"title": "Pandas Help", "url": "https://example.com/1"},
            {"title": "GPT Models", "url": "https://example.com/2"}
        ]
    }
    
    # Create temporary data file
    os.makedirs("data", exist_ok=True)
    with open("data/tds_data.json", "w") as f:
        json.dump(test_data, f)
    
    # Test API response
    response = client.post(
        "/api/",
        json={"question": "test", "image": None}
    )
    
    assert response.status_code == 200
    assert len(response.json()["links"]) == 2
    assert "Pandas Help" in response.json()["links"][0]["title"]
