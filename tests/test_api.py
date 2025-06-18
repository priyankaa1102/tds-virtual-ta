from fastapi.testclient import TestClient
from app.main import app
import json
from pathlib import Path

client = TestClient(app)
SAMPLE_DATA = Path(__file__).parent / "test_data/sample_response.json"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "data_stats" in response.json()

def test_answer_endpoint(monkeypatch):
    # Mock the data loading
    def mock_load():
        with open(SAMPLE_DATA) as f:
            return json.load(f)
    
    monkeypatch.setattr("app.main.load_knowledge_base", mock_load)
    
    # Test with known question
    response = client.post(
        "/api/",
        json={"question": "pandas"}
    )
    
    assert response.status_code == 200
    assert len(response.json()["links"]) > 0
    assert "pandas" in response.json()["links"][0]["text"].lower()
