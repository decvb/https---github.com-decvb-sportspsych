# Sports Psychologist AI Agent

This project is an MVP for a Sports Psychologist AI Agent. It provides a FastAPI backend with endpoints for chat, user profile management, and text-to-speech (TTS), leveraging Supabase for storage and OpenAI for LLM responses.

## Features
- Chat endpoint with context-aware LLM responses
- User profile creation, update, and retrieval
- Text-to-speech (TTS) using ElevenLabs
- Document ingestion and chunking with LangChain, stored in Supabase PGVector

## Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd langchain test
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the project root with the following variables:
```
OPENAI_API_KEY=your-openai-key
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SUPABASE_ANON_KEY=your-supabase-anon-key
ELEVENLABS_API_KEY=your-elevenlabs-key
SUPABASE_DB_PASSWORD=your-supabase-db-password
# (Optional, advanced) Use this to override the PGVector connection string, e.g. for session pooler:
SUPABASE_PG_CONN_STRING=postgresql+psycopg2://USER:PASSWORD@HOST:6543/postgres
```

### 5. Ingest Documents
To process and store documents in the vector store:
```bash
python ingest_data.py
```

## Running the FastAPI App
```bash
uvicorn main:app --reload
```

## API Endpoints

### POST /chat
- **Description:** Chat with the AI agent.
- **Request Body:**
  ```json
  { "user_id": "<uuid>", "message": "How can I improve my focus?" }
  ```
- **Response:**
  ```json
  { "response": "..." }
  ```

### GET /profile
- **Query:** `user_id=<uuid>`
- **Response:**
  ```json
  { "id": "<uuid>", "sport": "Tennis", ... }
  ```

### POST /profile
- **Body:**
  ```json
  { "id": "<uuid>", "sport": "Tennis", ... }
  ```
- **Response:** Profile object

### PUT /profile
- **Body:** Profile object (same as POST)
- **Response:** Profile object

### POST /tts
- **Body:**
  ```json
  { "text": "Visualize your success before the match." }
  ```
- **Response:** Audio stream (audio/mpeg)

## Running Tests
```bash
pytest
```

## Notes
- Ensure your Supabase project allows the required API and database access.
- RAG/vector search is a placeholder until direct DB access is available.
- See `PLANNING.md` and `TASK.md` for architecture and progress. 