"""
main.py - FastAPI backend for Sports Psychologist AI Agent MVP

- Loads environment variables
- Initializes Supabase, OpenAI, and ElevenLabs clients (stubs)
- Defines endpoints for /chat, /profile, /tts
"""

import os
from fastapi import FastAPI, HTTPException, Query
from pydantic_settings import BaseSettings
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional, List
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_postgres.vectorstores import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableSequence

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

class Profile(BaseModel):
    id: str
    sport: Optional[str] = None
    goals: Optional[str] = None
    level: Optional[str] = None
    notes: Optional[str] = None
    updated_at: Optional[str] = None

@app.get("/profile", response_model=Profile)
def get_profile(user_id: str = Query(..., description="Supabase user UUID")):
    """
    Fetch the user's profile from Supabase.

    Args:
        user_id (str): Supabase user UUID.

    Returns:
        Profile: The user's profile data.
    """
    response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    if response.data is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return response.data

class ProfileUpdate(BaseModel):
    sport: Optional[str] = None
    goals: Optional[str] = None
    level: Optional[str] = None
    notes: Optional[str] = None

@app.post("/profile", response_model=Profile)
def update_profile(user_id: str = Query(..., description="Supabase user UUID"), profile: ProfileUpdate = ...):
    """
    Upsert (insert or update) the user's profile in Supabase.

    Args:
        user_id (str): Supabase user UUID.
        profile (ProfileUpdate): Profile fields to update.

    Returns:
        Profile: The updated profile data.
    """
    profile_data = profile.dict(exclude_unset=True)
    profile_data["id"] = user_id
    from datetime import datetime
    profile_data["updated_at"] = datetime.utcnow().isoformat()
    response = supabase.table("profiles").upsert(profile_data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update profile.")
    return response.data[0]

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

# Helper: Fetch message history from Supabase
def get_message_history(user_id: str) -> List[dict]:
    resp = supabase.table("messages").select("role,content,created_at").eq("user_id", user_id).order("created_at").execute()
    return resp.data or []

# Helper: Add message to Supabase
def add_message_to_history(user_id: str, role: str, content: str):
    from datetime import datetime
    supabase.table("messages").insert({
        "user_id": user_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Chat endpoint: Accepts user message and user_id, fetches history/profile, retrieves docs from PGVector, calls OpenAI, saves history, returns response.
    """
    # 1. Fetch user profile
    profile_resp = supabase.table("profiles").select("*").eq("id", request.user_id).single().execute()
    profile = profile_resp.data if profile_resp.data else {}

    # 2. Fetch message history
    history = get_message_history(request.user_id)
    lc_history = []
    for msg in history:
        if msg["role"] == "user":
            lc_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_history.append(AIMessage(content=msg["content"]))

    # 3. Set up LangChain components
    # PGVector connection string: postgresql+psycopg://user:password@host:port/dbname
    import urllib.parse
    db_url = urllib.parse.urlparse(settings.SUPABASE_URL)
    # Supabase URL is like https://xxxx.supabase.co, need to convert to db host
    db_host = db_url.hostname.replace("https://", "db.") if db_url.hostname else ""
    db_user = "postgres"
    db_pass = settings.SUPABASE_DB_PASSWORD
    db_name = db_url.hostname.split(".")[0] if db_url.hostname else ""
    pgvector_conn_str = f"postgresql+psycopg://{db_user}:{db_pass}@{db_host}:5432/{db_name}"

    embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name="langchain_pg_collection",
        connection=pgvector_conn_str
    )
    retriever = vectorstore.as_retriever()

    # 4. Retrieve relevant docs
    docs = retriever.get_relevant_documents(request.message)
    context = "\n".join([doc.page_content for doc in docs])

    # 5. Format prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are a sports psychologist AI. User profile: {profile}. Conversation history: {{history}}. Context: {{context}}."),
        ("human", "{input}")
    ])
    chain = RunnableSequence([
        prompt,
        ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY)
    ])
    # 6. Run chain
    result = chain.invoke({
        "input": request.message,
        "history": lc_history,
        "context": context
    })
    ai_response = result.content if hasattr(result, "content") else str(result)

    # 7. Save user and AI messages
    add_message_to_history(request.user_id, "user", request.message)
    add_message_to_history(request.user_id, "assistant", ai_response)

    return ChatResponse(response=ai_response)

@app.post("/tts")
def tts():
    """
    Placeholder for text-to-speech endpoint.
    """
    return {"audio": "TTS endpoint not yet implemented."}

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