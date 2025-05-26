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
from langchain.evaluation import load_evaluator
from datetime import datetime

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
    """
    Generate headers for Supabase REST API requests.

    Returns:
        dict: Headers including API key and authorization.
    """
    return {
        "apikey": settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

def get_profile(user_id: str) -> Optional[Profile]:
    """
    Fetch a user profile from Supabase by user_id.

    Args:
        user_id (str): The user's UUID.

    Returns:
        Optional[Profile]: The user's profile or None if not found.
    """
    url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
    resp = requests.get(url, headers=supabase_headers())
    if resp.status_code == 200 and resp.json():
        return Profile(**resp.json()[0])
    return None

def upsert_profile(profile: Profile) -> bool:
    """
    Create or update a user profile in Supabase.

    Args:
        profile (Profile): The profile data.

    Returns:
        bool: True if successful, False otherwise.
    """
    url = f"{settings.SUPABASE_URL}/rest/v1/profiles"
    resp = requests.post(url, headers={**supabase_headers(), "Prefer": "resolution=merge-duplicates"}, json=profile.dict())
    return resp.status_code in (200, 201)

def get_message_history(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch the most recent message history for a user.

    Args:
        user_id (str): The user's UUID.
        limit (int): Number of messages to fetch.

    Returns:
        List[Dict[str, Any]]: List of message dicts.
    """
    url = f"{settings.SUPABASE_URL}/rest/v1/messages?user_id=eq.{user_id}&order=created_at.desc&limit={limit}"
    resp = requests.get(url, headers=supabase_headers())
    if resp.status_code == 200:
        return resp.json()
    return []

def add_message_to_history(user_id: str, role: str, content: str) -> bool:
    """
    Add a message to the user's conversation history in Supabase.

    Args:
        user_id (str): The user's UUID.
        role (str): 'user' or 'assistant'.
        content (str): The message content.

    Returns:
        bool: True if successful, False otherwise.
    """
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
    """
    Call ElevenLabs TTS API to synthesize speech from text.

    Args:
        text (str): The text to synthesize.
        voice_id (str): The ElevenLabs voice ID.

    Returns:
        bytes: The audio content (MP3).
    """
    # Debug: Print API key (masked), voice_id, and text length
    print(f"[TTS DEBUG] ELEVENLABS_API_KEY: {settings.ELEVENLABS_API_KEY[:8]}... (len={len(settings.ELEVENLABS_API_KEY)})")
    print(f"[TTS DEBUG] voice_id: {voice_id}")
    print(f"[TTS DEBUG] text: {text[:30]}... (len={len(text)})")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {"text": text, "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}}
    resp = requests.post(url, headers=headers, json=data)
    print(f"[TTS DEBUG] ElevenLabs response status: {resp.status_code}")
    if resp.status_code == 200:
        return resp.content
    # Print the error message from ElevenLabs for easier debugging
    print(f"[TTS DEBUG] ElevenLabs error: {resp.text}")
    raise HTTPException(status_code=500, detail=f"TTS failed: {resp.status_code} {resp.text}")

def evaluate_agent_response(input_text, profile, context, agent_response, expected=None):
    """
    Evaluate the agent's response using LangChain Evals (LLM-as-a-judge).
    Args:
        input_text (str): The user's message.
        profile (str): The user's profile info.
        context (str): The retrieved context.
        agent_response (str): The agent's response.
        expected (str, optional): Reference/guidance for the ideal response.
    Returns:
        dict: Evaluation results for each criterion.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    evaluator = load_evaluator(
        "criteria",
        llm=llm,
        criteria={
            "empathy": "Does the response show empathy and support?",
            "personalization": "Does the response use the user's profile info?",
            "clarity": "Is the advice clear and actionable?"
        }
    )
    result = evaluator.evaluate_strings(
        input=input_text,
        prediction=agent_response,
        reference=expected or "The response should be empathetic, personalized, and clear.",
        input_variables={
            "profile": profile,
            "context": context
        }
    )
    # Print for now; can be logged to DB later
    print(f"[EVAL] {datetime.utcnow().isoformat()} | Empathy: {result.get('empathy')} | Personalization: {result.get('personalization')} | Clarity: {result.get('clarity')}")
    print(f"[EVAL DETAILS] {result}")
    return result

# --- Endpoints ---

# /chat: Conversational endpoint for user-agent interaction with RAG and memory
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """
    Chat endpoint: Accepts user message, fetches history/profile, uses LLM, saves history, returns response.
    Returns 404 if user_id is invalid or not found.
    """
    profile = get_profile(req.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found. Invalid user_id.")
    history = get_message_history(req.user_id)
    context = retrieve_context(req.message)
    # New, detailed system prompt for Sports Psychologist AI
    system_prompt = (
        "You are a highly skilled, empathetic, and experienced Sports Psychologist AI, dedicated to helping athletes enhance their mental performance. Your primary goal is to provide personalized mental training guidance, support, and practical exercises.\n"
        "\n"
        "**Persona and Tone:**\n"
        "*   Maintain a consistently positive, encouraging, and patient tone.\n"
        "*   Use language that is accessible, clear, and avoids overly technical jargon where possible, explaining complex concepts simply.\n"
        "*   Show genuine interest in the athlete's individual journey, challenges, and goals.\n"
        "*   Be an active listener: acknowledge the athlete's feelings, validate their experiences, and respond thoughtfully to their specific concerns.\n"
        "*   Your persona is that of a trusted coach and guide, not just an information provider.\n"
        "\n"
        "**Core Responsibilities & Interaction Style:**\n"
        "*   **Personalized Guidance:** Always prioritize the athlete's unique profile information (Sport, Goals, Experience Level, Specific Challenges discussed in profile or conversation). Frame all guidance, explanations, and exercises in the direct context of their sport and stated objectives. Tailor language and examples to resonate with someone at their indicated experience level.\n"
        "*   **Leverage Conversation History:** Remember and actively reference previous discussions, exercises attempted, successes, and difficulties shared by the athlete. Build upon past interactions to show continuity and deepen the sense of a personalized journey. Use this history to understand recurring patterns or progress.\n"
        "*   **Utilize Knowledge Base (Context):** Draw heavily and synthesize information from the provided sports psychology concepts, methodologies, and techniques (the `Context`). Do not just copy text from the context. Explain *how* the techniques work and *why* they are relevant to the athlete's situation, based on the context. Integrate references to techniques or concepts naturally within the conversation (e.g., 'This sounds like a good opportunity to practice a focus technique similar to X...', 'Based on principles of Y...').\n"
        "*   **Actionable & Exercise-Focused:** Where appropriate, guide the athlete through mental training exercises. Break down exercises into clear, sequential steps. After presenting a step, *always* prompt the user for engagement or confirmation before proceeding (e.g., 'Does that make sense?', 'Are you ready to try the first step?', 'How did that feel?'). This creates an interactive, guided experience rather than a monologue.\n"
        "*   **Triage Content:** When the athlete asks a question or describes a challenge, identify the core psychological principle or technique relevant to their situation based on the `Context` and your persona. Triage the information to provide the *most* relevant and actionable guidance from the knowledge base for *that specific user and their context*.\n"
        "*   **Manage Conversation Scope:** Focus strictly on sports psychology, mental performance, and general supportive conversation related to an athlete's well-being. If the athlete asks about unrelated topics, politely and gently steer the conversation back to their athletic or mental performance goals, or state that you can only assist with sports psychology related matters.\n"
        "*   **Encouragement and Feedback:** Offer positive reinforcement and encouragement regularly, especially when the athlete shares progress, attempts an exercise, or demonstrates effort. Acknowledge difficulties with empathy and offer support.\n"
        "*   **Handling Unclear Queries:** If a user's message is unclear, ask clarifying questions to better understand their needs before providing guidance.\n"
        "\n"
        "**Inputs Provided (via LangChain):**\n"
        "*   `{profile_info}`: A string containing the athlete's relevant profile details (e.g., 'User Profile:\nSport: Running\nGoals: Improve focus\nLevel: Competitive Amateur'). This will be formatted by the backend. Use this *prominently* to tailor your responses.\n"
        "*   `{chat_history}`: The recent conversation history between you and the athlete. Use this to remember previous turns and maintain context.\n"
        "*   `{context}`: Relevant chunks of text retrieved from the sports psychology knowledge base based on the user's query and conversation history. Use this to inform your expert responses and techniques.\n"
        "*   `{question}`: The athlete's current message.\n"
        "\n"
        "**Output Format:**\n"
        "*   Provide a text response formatted for conversational chat. TTS is handled separately, so focus on clear, well-structured text.\n"
        "\n"
        "**Initial Interaction / Onboarding (If Profile Incomplete):**\n"
        "*   If the athlete is new or has an incomplete profile (`{profile_info}` indicates missing details), gently introduce the value of sharing information about their sport, goals, etc., explaining *how* it will enable you to provide more personalized and effective guidance. Weave this into your initial response or after they share their first query.\n"
        "\n"
        "**Constraint Checklist (Self-Correction):**\n"
        "*   Is the response empathetic and supportive?\n"
        "*   Does it use the athlete's profile info?\n"
        "*   Does it consider the conversation history?\n"
        "*   Does it draw upon the provided context?\n"
        "*   Is the language clear and accessible?\n"
        "*   Is it focused on sports psychology?\n"
        "*   If guiding an exercise, is it broken down into steps with engagement prompts?\n"
        "*   Does it encourage the athlete?\n"
        "\n"
        "Always adhere to this persona and these instructions. Respond as the Sports Psychologist AI.\n"
        "\n"
        "{profile_info} // Backend will insert profile here\n"
        "{context} // LangChain will insert retrieved context here"
    )
    # Format profile, history, context, and question for the prompt
    profile_info = f"User Profile:\n" + "\n".join(f"{k}: {v}" for k, v in profile.dict().items() if v)
    chat_history = str(history)
    question = req.message
    # Compose the prompt for the LLM
    prompt = (
        f"{profile_info}\n"
        f"Chat History:\n{chat_history}\n"
        f"Context:\n{context}\n"
        f"Question:\n{question}\n"
    )
    ai_response = call_openai_llm_with_system_prompt(prompt, system_prompt)
    add_message_to_history(req.user_id, "user", req.message)
    add_message_to_history(req.user_id, "assistant", ai_response)
    # --- Automated Evaluation ---
    evaluate_agent_response(
        input_text=req.message,
        profile=profile_info,
        context=context,
        agent_response=ai_response
    )
    return ChatResponse(response=ai_response)

# Add a helper to support system prompt injection
def call_openai_llm_with_system_prompt(prompt: str, system_prompt: str) -> str:
    """
    Call OpenAI LLM with a custom system prompt.

    Args:
        prompt (str): The user prompt and context.
        system_prompt (str): The system prompt for the LLM.

    Returns:
        str: The LLM's response.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256
    }
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    return "Sorry, I couldn't generate a response."

# /profile: Get user profile by user_id
@app.get("/profile", response_model=Profile)
def get_profile_endpoint(user_id: str):
    """
    Get user profile by user_id.
    Returns 404 if not found.
    """
    profile = get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

# /profile: Create or update user profile
@app.post("/profile", response_model=Profile)
def post_profile_endpoint(profile: Profile):
    """
    Create or update user profile. Upserts by id.
    """
    if not upsert_profile(profile):
        raise HTTPException(status_code=500, detail="Failed to upsert profile")
    return profile

# /profile: Update user profile (PUT)
@app.put("/profile", response_model=Profile)
def put_profile_endpoint(profile: Profile):
    """
    Update user profile. Upserts by id.
    """
    if not upsert_profile(profile):
        raise HTTPException(status_code=500, detail="Failed to update profile")
    return profile

# /tts: Text-to-speech endpoint
@app.post("/tts")
def tts_endpoint(req: TTSRequest):
    """
    Text-to-speech endpoint: Accepts text, returns audio stream (MP3).
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

# /debug/profiles: Debug endpoint to return all profiles
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