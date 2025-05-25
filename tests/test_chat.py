import pytest
from fastapi.testclient import TestClient
from main import app, retrieve_context
from unittest.mock import patch

client = TestClient(app)

@pytest.fixture
def user_id():
    # Real Supabase user UUID for integration test
    return "f2cbd6e8-f644-408f-ac90-e4214a0e7d19"

def test_chat_expected_use(user_id):
    """Test /chat endpoint with expected input."""
    response = client.post("/chat", json={"user_id": user_id, "message": "How can I improve my focus before a game?"})
    print("RESPONSE STATUS:", response.status_code)
    print("RESPONSE JSON:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0

def test_chat_empty_message(user_id):
    """Test /chat endpoint with empty message (edge case)."""
    response = client.post("/chat", json={"user_id": user_id, "message": ""})
    assert response.status_code == 200 or response.status_code == 400
    # Accept either a valid (but likely generic) response or a validation error

def test_chat_invalid_user():
    """Test /chat endpoint with invalid user_id (failure case)."""
    response = client.post("/chat", json={"user_id": "invalid-uuid", "message": "Hello"})
    assert response.status_code in (404, 400, 500)

def test_chat_missing_message(user_id):
    """Test /chat endpoint with missing message field (failure case)."""
    response = client.post("/chat", json={"user_id": user_id})
    print("RESPONSE STATUS (missing message):", response.status_code)
    print("RESPONSE JSON (missing message):", response.text)
    assert response.status_code in (400, 422)

# --- Profile endpoint tests ---
def test_get_profile_expected_use(user_id):
    """Test /profile GET with valid user_id."""
    response = client.get(f"/profile?user_id={user_id}")
    assert response.status_code in (200, 404)  # 404 if profile doesn't exist
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert data["id"] == user_id

def test_get_profile_invalid_user():
    """Test /profile GET with invalid user_id (failure case)."""
    response = client.get("/profile?user_id=invalid-uuid")
    assert response.status_code in (404, 400)

def test_post_profile_expected_use(user_id):
    """Test /profile POST to create/update a profile (expected use)."""
    profile = {
        "id": user_id,
        "sport": "Tennis",
        "goals": "Win next tournament",
        "level": "Intermediate",
        "notes": "Focus on serve"
    }
    response = client.post("/profile", json=profile)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["sport"] == "Tennis"

def test_post_profile_missing_id():
    """Test /profile POST with missing id (failure case)."""
    profile = {
        "sport": "Soccer",
        "goals": "Improve stamina"
    }
    response = client.post("/profile", json=profile)
    assert response.status_code in (400, 422)

def test_put_profile_expected_use(user_id):
    """Test /profile PUT to update a profile (expected use)."""
    profile = {
        "id": user_id,
        "sport": "Basketball",
        "goals": "Increase scoring",
        "level": "Advanced",
        "notes": "Work on defense"
    }
    response = client.put("/profile", json=profile)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["sport"] == "Basketball"

def test_put_profile_missing_id():
    """Test /profile PUT with missing id (failure case)."""
    profile = {
        "sport": "Golf",
        "goals": "Lower handicap"
    }
    response = client.put("/profile", json=profile)
    assert response.status_code in (400, 422)

# --- TTS endpoint tests ---
def test_tts_expected_use():
    """Test /tts POST with valid text (expected use)."""
    req = {"text": "Visualize your success before the match."}
    response = client.post("/tts", json=req)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")

def test_tts_empty_text():
    """Test /tts POST with empty text (edge case)."""
    req = {"text": ""}
    response = client.post("/tts", json=req)
    assert response.status_code in (200, 400)

def test_tts_missing_text():
    """Test /tts POST with missing text field (failure case)."""
    req = {}
    response = client.post("/tts", json=req)
    assert response.status_code in (400, 422)

# --- RAG retrieve_context tests ---
def test_retrieve_context_expected_use(monkeypatch):
    """Test retrieve_context returns concatenated context for a valid query."""
    class DummyDoc:
        def __init__(self, content):
            self.page_content = content
    monkeypatch.setattr(
        "main.vectorstore.similarity_search",
        lambda query, k=2: [DummyDoc("Chunk 1"), DummyDoc("Chunk 2")]
    )
    context = retrieve_context("focus training")
    assert "Chunk 1" in context and "Chunk 2" in context

def test_retrieve_context_no_results(monkeypatch):
    """Test retrieve_context returns empty string if no docs found."""
    monkeypatch.setattr(
        "main.vectorstore.similarity_search",
        lambda query, k=2: []
    )
    context = retrieve_context("nonexistent topic")
    assert context == ""

def test_retrieve_context_failure(monkeypatch):
    """Test retrieve_context handles vectorstore errors gracefully."""
    def raise_error(query, k=2):
        raise Exception("Vectorstore error!")
    monkeypatch.setattr("main.vectorstore.similarity_search", raise_error)
    context = retrieve_context("error case")
    assert context == "" 