"""
main.py - FastAPI backend for Sports Psychologist AI Agent MVP

- Loads environment variables
- Initializes Supabase, OpenAI, and ElevenLabs clients (stubs)
- Defines endpoints for /chat, /profile, /tts
"""

import os
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_postgres.vectorstores import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableSequence
from pydantic_settings import BaseSettings
from langchain_community.vectorstores.pgvector import PGVector as CommunityPGVector

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    OPENAI_API_KEY: str
    ELEVENLABS_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_DB_PASSWORD: str
    SUPABASE_SERVICE_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Initialize FastAPI app
app = FastAPI(title="Sports Psychologist AI Agent API")

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

# --- Stub client initializations (to be implemented) ---
# Example: openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
# Example: elevenlabs_client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

print("SUPABASE_URL:", settings.SUPABASE_URL)
print("SUPABASE_ANON_KEY:", settings.SUPABASE_ANON_KEY[:8], "...")

# --- Models ---
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

class Profile(BaseModel):
    id: str
    sport: Optional[str] = None
    goals: Optional[str] = None
    level: Optional[str] = None
    notes: Optional[str] = None
    updated_at: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    user_id: Optional[str] = None
    voice_id: Optional[str] = None

# --- Supabase REST API helpers ---
def supabase_headers():
    return {
        "apikey": settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

def get_profile(user_id: str) -> Optional[Profile]:
    url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    resp = requests.get(url, headers=supabase_headers())
    if resp.status_code == 200 and resp.json():
        return Profile(**resp.json()[0])
    return None

def upsert_profile(profile: Profile) -> bool:
    url = f"{settings.SUPABASE_URL}/rest/v1/profiles"
    resp = requests.post(url, headers={**supabase_headers(), "Prefer": "resolution=merge-duplicates"}, json=profile.dict())
    return resp.status_code in (200, 201)

def get_message_history(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    url = f"{settings.SUPABASE_URL}/rest/v1/messages?user_id=eq.{user_id}&order=created_at.desc&limit={limit}"
    resp = requests.get(url, headers=supabase_headers())
    if resp.status_code == 200:
        return resp.json()
    return []

def add_message_to_history(user_id: str, role: str, content: str) -> bool:
    url = f"{settings.SUPABASE_URL}/rest/v1/messages"
    data = {"user_id": user_id, "role": role, "content": content}
    resp = requests.post(url, headers=supabase_headers(), json=data)
    return resp.status_code in (200, 201)

# --- LangChain PGVector Vector Store Initialization ---
embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
SUPABASE_PG_CONNECTION_STRING = os.getenv("SUPABASE_PG_CONNECTION_STRING")
# Prefer full connection string from env if provided
if SUPABASE_PG_CONNECTION_STRING:
    connection_string = SUPABASE_PG_CONNECTION_STRING
else:
    connection_string = f"postgresql+psycopg2://postgres:{settings.SUPABASE_SERVICE_KEY}@{settings.SUPABASE_URL.replace('https://', '').replace('.supabase.co', '.supabase.co:5432')}/postgres"
vectorstore = CommunityPGVector(
    connection_string=connection_string,
    collection_name="sports_psychology_docs",
    embedding_function=embeddings,
)

# --- RAG/vector search implementation ---
def retrieve_context(query: str, k: int = 2) -> str:
    """
    Retrieve relevant context from the vector store using semantic search.

    Args:
        query (str): The user query.
        k (int): Number of top chunks to retrieve.

    Returns:
        str: Concatenated relevant context.
    """
    try:
        docs = vectorstore.similarity_search(query, k=k)
        if not docs:
            return ""
        # Concatenate the content of the top-k docs
        return "\n---\n".join([doc.page_content for doc in docs])
    except Exception as e:
        # Reason: If vector search fails, fallback to empty context
        print(f"[RAG ERROR] {e}")
        return ""

# --- OpenAI LLM call (simple completion) ---
def call_openai_llm(prompt: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a friendly, down-to-earth sports psychologist. Speak casually, use everyday language, and keep your advice short and practical. Imagine you're chatting with an athlete over coffee."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256
    }
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    return "Sorry, I couldn't generate a response."

# --- ElevenLabs TTS ---
def call_elevenlabs_tts(text: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL") -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {"text": text, "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        return resp.content
    # Return the error message from ElevenLabs for easier debugging
    raise HTTPException(status_code=500, detail=f"TTS failed: {resp.status_code} {resp.text}")

# --- Endpoints ---
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """
    Chat endpoint: Accepts user message, fetches history/profile, uses LLM, saves history, returns response.
    """
    profile = get_profile(req.user_id)
    history = get_message_history(req.user_id)
    context = retrieve_context(req.message)
    prompt = (
        "You are a friendly, down-to-earth sports psychologist. "
        "Here is some background info you can use to help the user (do not repeat it verbatim):\n"
        f"{context}\n\n"
        f"User profile: {profile.dict() if profile else 'N/A'}\n"
        f"Conversation history: {history}\n"
        f"User: {req.message}\n"
        "Give a short, practical, and conversational response."
    )
    ai_response = call_openai_llm(prompt)
    add_message_to_history(req.user_id, "user", req.message)
    add_message_to_history(req.user_id, "assistant", ai_response)
    return ChatResponse(response=ai_response)

@app.get("/profile", response_model=Profile)
def get_profile_endpoint(user_id: str):
    """
    Get user profile by user_id.
    """
    profile = get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.post("/profile", response_model=Profile)
def post_profile_endpoint(profile: Profile):
    """
    Create or update user profile.
    """
    if not upsert_profile(profile):
        raise HTTPException(status_code=500, detail="Failed to upsert profile")
    return profile

@app.put("/profile", response_model=Profile)
def put_profile_endpoint(profile: Profile):
    """
    Update user profile.
    """
    if not upsert_profile(profile):
        raise HTTPException(status_code=500, detail="Failed to update profile")
    return profile

@app.post("/tts")
def tts_endpoint(req: TTSRequest):
    """
    Text-to-speech endpoint: Accepts text, returns audio stream.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text for TTS cannot be empty.")
    try:
        voice_id = req.voice_id or "EXAVITQu4vr4xnSDxMaL"
        audio = call_elevenlabs_tts(req.text, voice_id)
        return StreamingResponse(iter([audio]), media_type="audio/mpeg")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

@app.get("/debug/profiles")
def debug_profiles():
    """
    Debug endpoint to return all rows in the profiles table.
    """
    try:
        resp = supabase.table("profiles").select("*").execute()
        return {"profiles": resp.data}
    except Exception as e:
        return {"error": str(e)} 