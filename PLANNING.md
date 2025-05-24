# PLANNING.md: Sports Psychologist AI Agent MVP

This document outlines the core plan, architecture, and technical decisions for building the Minimum Viable Product (MVP) of a conversational AI Sports Psychologist agent. This serves as the primary reference for the coding assistant during development.

## 1. Purpose & Vision

*   **Goal:** Create an AI agent that acts as a sports psychologist, guiding athletes through mental training exercises.
*   **Core Functionality:** Engage in natural conversation, understand user context (history, profile), and draw upon a specialized knowledge base to provide relevant guidance.
*   **Personalization:** Tailor interactions based on individual user profiles and past conversations.

## 2. Key Features (MVP Scope)

*   Text-based chat interface.
*   Text-to-Speech (TTS) audio output for AI responses.
*   Knowledge retrieval (RAG) from a corpus of sports psychology documents.
*   Conversation history recall.
*   User profiles (sport, goals, etc.) influencing guidance.
*   User authentication and separation of data.

## 3. Architecture

*   **Frontend:** Lovable web application (handles UI, user input, potentially STT).
*   **Backend API:** FastAPI (Python) handles all core logic, connecting frontend to database and AI services.
*   **Database:** Supabase (PostgreSQL) for user authentication, conversation history, user profiles, and RAG vector storage.
*   **External AI Services:** OpenAI (LLM, Embeddings), ElevenLabs (TTS).

## 4. Tech Stack & Tools

*   **Backend Framework:** FastAPI (Python)
*   **AI Orchestration:** LangChain (Python Library)
*   **Large Language Model (LLM):** OpenAI GPT-4o (primary for MVP cost efficiency)
*   **Embeddings:** OpenAI Embeddings
*   **Vector Database (RAG):** Supabase `pgvector` extension
*   **Database (Auth, History, Profiles):** Supabase (standard PostgreSQL tables)
*   **Text-to-Speech (TTS):** ElevenLabs API
*   **Backend Python Libraries:** `fastapi`, `uvicorn`, `langchain`, `langchain-openai`, `langchain-community` (for PGVector), `supabase` (Python client), `psycopg2-binary` (or `asyncpg`), `python-dotenv`, `elevenlabs`, `pydantic`.
*   **Frontend Platform:** Lovable (Handles connecting to FastAPI API, displaying chat, playing audio).
*   **Development Environment:** Cursor IDE.

## 5. Key Decisions & Constraints

*   **Budget:** Minimal (MVP focus). Prioritize cost-effective APIs (GPT-3.5-Turbo).
*   **Database Integration:** Utilize Supabase for *all* data storage (Auth, RAG vectors via `pgvector`, History, Profiles) to minimize infrastructure complexity.
*   **User Identity:** Supabase Auth (`auth.users` table) is the source of truth for user identification (UUID). All user-specific data (`messages`, `profiles`) must be linked via the user's Supabase UUID. Row Level Security (RLS) in Supabase is essential for data privacy.
*   **RAG Implementation:** Use LangChain with Supabase `pgvector` for document retrieval. Knowledge base ingestion is a separate script.
*   **Conversation Memory:** Implement memory in the FastAPI backend using LangChain, saving/loading state from the Supabase `messages` table for each user.
*   **TTS Handling:** Performed in the FastAPI backend using ElevenLabs API, returning an audio stream to the frontend.
*   **STT Handling:** Expected to be handled primarily by the Lovable frontend.
*   **API Structure:** FastAPI endpoints for `/chat` (text input, text output), `/tts` (text input, audio stream output), and `/profile` (GET/POST for user profile data).

## 6. Data Model (Supabase Tables)

*   `auth.users`: Supabase standard user table (`id` UUID is key identifier).
*   `profiles`: Stores custom user data (sport, goals, etc.). `id` column is PK and FK referencing `auth.users(id)`.
*   `messages`: Stores conversation turns. `user_id` column is FK referencing `auth.users(id)`. Includes `role`, `content`, `created_at`.
*   `langchain_pg_collections`, `langchain_pg_embeddings`: Tables managed by LangChain's PGVector integration for RAG embeddings.

## 7. Core Workflows

*   **Chat Interaction:**
    *   Lovable sends user message + Supabase User UUID to FastAPI `/chat`.
    *   FastAPI fetches user profile and conversation history (via Supabase UUID).
    *   FastAPI uses LangChain to:
        *   Retrieve relevant docs from Supabase PGVector (RAG).
        *   Format prompt with persona, profile info, history, and retrieved context.
        *   Call OpenAI GPT-4o
    *   FastAPI saves user message and AI response to Supabase `messages` table.
    *   FastAPI returns AI's text response to Lovable.
*   **Voice Output:**
    *   Lovable receives AI text response.
    *   Lovable sends AI text response (and potentially user UUID) to FastAPI `/tts`.
    *   FastAPI calls ElevenLabs API.
    *   FastAPI streams audio bytes back to Lovable.
    *   Lovable plays audio.
*   **Profile Management:**
    *   Lovable gets/sends profile data + Supabase User UUID to FastAPI `/profile`.
    *   FastAPI reads/writes to the Supabase `profiles` table.

---

**Instructions for Cursor:**

*   **Prompt to AI:** `Use the structure and decisions outlined in the PLANNING.md file located in the project root. Reference this document for context on the project's purpose, architecture, tech stack, database schema, and key implementation decisions whenever generating code or providing guidance related to the build process.`
*   **Beginning of each new conversation:** When starting a new conversation or thread about this project, the AI should acknowledge that it is referencing the `PLANNING.md` file. For example: "Okay, referencing the `PLANNING.md` for the Sports Psychologist AI Agent MVP. How can I help you today with the build?"

---