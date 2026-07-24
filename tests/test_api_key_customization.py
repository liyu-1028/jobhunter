import pytest
from fastapi.testclient import TestClient
from src.server import app
from src.deepseek_client import DeepSeekJobHunter
from src.models import UserProfile

client = TestClient(app)

def test_deepseek_client_custom_api_key():
    """测试 DeepSeekJobHunter 能够正确接受动态传入的自定义 api_key"""
    custom_key = "sk-test-custom-key-123456"
    hunter = DeepSeekJobHunter(api_key=custom_key)
    assert hunter.api_key == custom_key
    assert hunter.client is not None

def test_api_search_jobs_with_custom_api_key():
    """测试 /api/search_jobs 接口能接收前端传入的 api_key"""
    payload = {
        "degree": "硕士",
        "school": "浙江大学",
        "major": "计算机",
        "batch": "2026届秋招",
        "target_industry": "互联网",
        "company_type": "大厂/国企",
        "company_size": "1000人以上",
        "location": "杭州",
        "keywords": "Python, 大模型",
        "api_key": "sk-user-browser-provided-key"
    }
    response = client.post("/api/search_jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_api_fetch_counselors_with_custom_api_key():
    """测试 /api/fetch_counselors 接口能接收前端传入的 api_key"""
    payload = {
        "province": "浙江",
        "city": "杭州",
        "api_key": "sk-user-browser-provided-key"
    }
    response = client.post("/api/fetch_counselors", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
