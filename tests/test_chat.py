import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def user_id():
    # Real Supabase user UUID for integration test
    return "c5d6d19d-530f-4ade-9fdd-1d020c2c9280"

def test_chat_expected_use(user_id):
    response = client.post("/chat", json={"user_id": user_id, "message": "How can I improve my focus before a game?"})
    print("RESPONSE STATUS:", response.status_code)
    print("RESPONSE JSON:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0

def test_chat_empty_message(user_id):
    response = client.post("/chat", json={"user_id": user_id, "message": ""})
    assert response.status_code == 200 or response.status_code == 400
    # Accept either a valid (but likely generic) response or a validation error

def test_chat_invalid_user():
    response = client.post("/chat", json={"user_id": "invalid-uuid", "message": "Hello"})
    assert response.status_code in (404, 400, 500)

def test_chat_missing_message(user_id):
    response = client.post("/chat", json={"user_id": user_id})
    print("RESPONSE STATUS (missing message):", response.status_code)
    print("RESPONSE JSON (missing message):", response.text)
    assert response.status_code in (400, 422) 