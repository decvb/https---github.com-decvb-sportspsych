# TASK.md: Sports Psychologist AI Agent - Task Tracking

This document is used by the developer and the AI coding assistant to track the progress of the Sports Psychologist AI Agent MVP build, manage the backlog, and note important discoveries.

**Instructions for the AI:**

*   **Reference:** Use this file to understand the current build status, active tasks, and upcoming items.
*   **Updates:** When prompted, update the status of tasks (e.g., change `[ ]` to `[x]`), add new tasks to the appropriate section, or move tasks between sections.
*   **Adding Tasks:** Add discovered sub-tasks or new requirements to the "Active Tasks" if immediately relevant, or to the "Backlog" if not.
*   **Completing Tasks:** When a task is finished, mark its checkbox as `[x]`.
*   **Maintaining Structure:** Preserve the main headings and bullet list format.

---

## Active Tasks

These are the tasks currently being worked on or the immediate next steps.

*   [~] Set up project directory, virtual environment, and install basic dependencies (`fastapi`, `uvicorn`, `python-dotenv`). _Setup commands being provided._
*   [~] Create and configure the `.env` file with API keys and Supabase connection details (including DB password). _Template and variable descriptions provided._
*   [~] In Supabase: Enable `pgvector` extension. _SQL command provided._
*   [~] In Supabase: Create the `messages` table with `user_id` (UUID FK to `auth.users`), `role`, `content`, `created_at`. _SQL command provided._
*   [~] In Supabase: Create the `profiles` table with `id` (UUID PK & FK to `auth.users`), `updated_at`, and initial profile fields (sport, goals, level, notes). _SQL command provided._
*   [~] In Supabase: Implement Row Level Security (RLS) for `messages` and `profiles` tables to ensure users can only access their own data. _RLS policies provided._
*   [~] Run `ingest_data.py` to populate the Supabase vector store.
*   [ ] Implement frontend UI for chat, profile, and TTS endpoints
*   [ ] Write Pytest unit tests for FastAPI endpoints and Supabase helpers
*   [ ] Integrate RAG/vector search with FastAPI backend when direct DB access is available
*   [ ] Implement an interactive CLI or notebook-based agent test harness for conversational testing (not frontend)
*   [x] Implement dynamic voice switching in CLI and backend using ElevenLabs voice IDs (2024-06-13)
*   [x] Enhance CLI for real-time audio playback and user-driven voice changes (2024-06-13)
*   [x] Robust TTS error handling and dynamic voice_id support in backend (2024-06-13)
*   [ ] Refine sports psych agent persona and prompt for more natural, conversational, less formal/verbose responses (2024-06-13)
*   [ ] Update knowledge base documents to match new, more natural style (2024-06-13)
*   [x] Implement the `/chat` POST endpoint: accept user ID and message, fetch history/profile, use LangChain (Memory, RAG, LLM), save history, return text response. (2024-06-13)
*   [x] Implement the `/profile` GET/POST/PUT endpoints for fetching and updating user profile data in Supabase. (2024-06-13)
*   [x] Implement the `/tts` POST endpoint: accept text and user ID, call ElevenLabs API (streaming), return audio stream. (2024-06-13)
*   [x] Test FastAPI endpoints locally (`uvicorn`, Swagger UI). (2024-06-13)
*   [x] Implement an interactive CLI or notebook-based agent test harness for conversational testing (not frontend). (2024-06-13)
*   [~] Validate chunking and embedding in Supabase after ingestion
*   [~] Integrate Supabase Auth into Lovable frontend (signup, login, get user UUID).
*   [~] Update Lovable chat interface to send user message + Supabase UUID to FastAPI `/chat`.
*   [~] Update Lovable chat interface to receive and display text response from `/chat`.
*   [~] Update Lovable frontend to call FastAPI `/tts` with AI response text and play the returned audio stream.
*   [~] Implement profile input form in Lovable, calling FastAPI `/profile`.
*   [~] Set up deployment environment (Render, Fly.io, etc.).
*   [~] Configure environment variables on the hosting platform.
*   [~] Deploy the FastAPI application.
*   [~] Update Lovable to use the deployed API URL.
*   [ ] (Post-MVP) Implement Speech-to-Text (STT) in Lovable frontend.
*   [x] Upgrade backend LLM to OpenAI GPT-4o for all completions (2024-06-13)
*   [ ] (Post-MVP) Refine prompt engineering for better sports psych guidance using GPT-4o.
*   [ ] (Post-MVP) Add more documents to the knowledge base.
*   [ ] (Post-MVP) Improve error handling and logging.
*   [ ] (Post-MVP) Enhance RLS policies and security.

## Completed Tasks

*   [x] Create `docs` directory in project root and add at least one sample sports psychology document for ingestion.
*   [x] Write `ingest_data.py` script using LangChain (loaders, splitter, OpenAIEmbeddings, PGVector) to process documents and store in Supabase.
*   [x] Run `ingest_data.py` to populate the Supabase vector store.
*   [x] Successfully tested ingest_data.py after fixing connection string variable. (2024-06-13)
*   [x] Implement FastAPI backend skeleton (main.py) with endpoints and Supabase REST integration.
*   [x] Write Pytest unit tests for FastAPI endpoints and Supabase helpers.
*   [x] Fixed Supabase RLS/permissions for profiles and messages tables. Applied migration to enforce correct policies. (2024-06-13)

## Backlog / Future Tasks

These tasks are planned for later stages of the MVP or post-MVP, ordered roughly by priority.

*   [ ] Create `main.py` with basic FastAPI app structure.
*   [ ] Initialize Supabase client, OpenAI clients (LLM, Embeddings), and ElevenLabs client/key in `main.py`.
*   [ ] Implement `get_message_history(user_id)` function in `main.py` (fetches from Supabase, converts to LangChain messages).
*   [ ] Implement `add_message_to_history(user_id, role, content)` function in `main.py` (inserts into Supabase).
*   [ ] Implement `get_user_profile(user_id)` function in `main.py` (fetches from Supabase).
*   [ ] Set up LangChain RAG components in `main.py` (PGVector vector store, retriever).
*   [ ] Define core LangChain prompt template (including persona, profile info, context, history).
*   [ ] Implement the `/chat` POST endpoint: accept user ID and message, fetch history/profile, use LangChain (Memory, RAG, LLM), save history, return text response.
*   [ ] Implement the `/profile` GET/POST/PUT endpoints for fetching and updating user profile data in Supabase.
*   [ ] Implement the `/tts` POST endpoint: accept text and user ID, call ElevenLabs API (streaming), return audio stream.
*   [ ] Test FastAPI endpoints locally (`uvicorn`, Swagger UI).
*   [ ] Integrate Supabase Auth into Lovable frontend (signup, login, get user UUID).
*   [ ] Update Lovable chat interface to send user message + Supabase UUID to FastAPI `/chat`.
*   [ ] Update Lovable chat interface to receive and display text response from `/chat`.
*   [ ] Update Lovable frontend to call FastAPI `/tts` with AI response text and play the returned audio stream.
*   [ ] Implement profile input form in Lovable, calling FastAPI `/profile`.
*   [ ] Set up deployment environment (Render, Fly.io, etc.).
*   [ ] Configure environment variables on the hosting platform.
*   [ ] Deploy the FastAPI application.
*   [ ] Update Lovable to use the deployed API URL.
*   [ ] (Post-MVP) Implement Speech-to-Text (STT) in Lovable frontend.
*   [ ] (Post-MVP) Refine prompt engineering for better sports psych guidance using GPT-4o.
*   [ ] (Post-MVP) Add more documents to the knowledge base.
*   [ ] (Post-MVP) Improve error handling and logging.
*   [ ] (Post-MVP) Enhance RLS policies and security.

## Milestones

Major phases of the project completion.

*   [ ] Supabase database schema and RLS are complete.
*   [ ] Knowledge base ingestion is working and data is in PGVector.
*   [ ] Core FastAPI backend API endpoints (`/chat` with RAG/History, `/tts`, `/profile`) are implemented and tested locally.
*   [ ] Lovable frontend successfully integrates with Supabase Auth and can communicate with *local* FastAPI endpoints for chat and profile.
*   [ ] Full stack is deployed and functional (Lovable connects to deployed FastAPI).

## Notes / Discoveries

Chronological log of issues found, decisions made mid-process, or helpful links.

*   YYYY-MM-DD: Discovered need to use `psycopg2-binary` or `asyncpg` with Supabase Python client for database interaction from FastAPI.
*   YYYY-MM-DD: Confirmed LangChain's PGVector typically creates its own table schema; adjusted plan to drop manual `documents` table creation for simplicity.
*   YYYY-MM-DD: Realized Supabase Auth provides the UUID needed for linking all user data; `user_id` fields in `messages` and `profiles` must be UUIDs referencing `auth.users(id)`.
*   YYYY-MM-DD: RLS is critical for multi-user Supabase, must implement policies for `SELECT`, `INSERT`, `UPDATE` based on `auth.uid()`.
*   YYYY-MM-DD: Decided on separate `/chat` (text) and `/tts` (audio) endpoints for simpler frontend streaming implementation.

## Discovered During Work

*   [ ] Implement RAG/vector search integration in FastAPI backend when direct DB access is available
*   [ ] Refactor main.py into modules if it approaches 500 lines (to maintain codebase standards)
*   [x] Bug: ingest_data.py used SUPABASE_PG_CONN_STRING instead of SUPABASE_PG_CONNECTION_STRING (as in .env). Fixed by aligning variable names. (2024-06-13)
*   [x] Successfully tested ingest_data.py after fixing connection string variable. (2024-06-13)

---