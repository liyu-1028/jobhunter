import pytest
from fastapi.testclient import TestClient
from src.server import app

client = TestClient(app)

def test_api_index():
    response = client.get("/")
    assert response.status_code == 200

def test_api_search_jobs():
    profile_payload = {
        "degree": "硕士",
        "school": "浙江大学",
        "major": "计算机",
        "batch": "2026届秋招",
        "target_industry": "互联网",
        "company_type": "大厂/国企",
        "company_size": "1000人以上",
        "location": "杭州",
        "keywords": "Python, 大模型"
    }
    response = client.post("/api/search_jobs", json=profile_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "fetched_at" in data
    assert "jobs" in data
    assert len(data["jobs"]) > 0

def test_api_fetch_enterprises():
    response = client.post("/api/fetch_enterprises")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_enterprises"] == 245
    assert len(data["enterprises"]) == 245

def test_api_fetch_counselors():
    payload = {"province": "浙江", "city": "杭州"}
    response = client.post("/api/fetch_counselors", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "counselors" in data
    assert len(data["counselors"]) > 0

def test_api_get_history():
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "enterprises" in data
    assert "counselors" in data
