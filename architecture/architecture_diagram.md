# Sports Psychologist AI Agent MVP: Architecture Diagram

```mermaid
graph TD
    subgraph Frontend
        A[Lovable Web App]
    end
    subgraph Backend
        B[FastAPI Server]
        C[LangChain Orchestration]
    end
    subgraph External AI Services
        D[OpenAI GPT-4o<br>LLM & Embeddings]
        E[ElevenLabs<br>Text-to-Speech]
    end
    subgraph Database
        F[Supabase<br>Auth, Profiles, Messages, RAG Vector DB]
    end
    subgraph Storage
        G[Docs Folder<br>Knowledge Base]
    end

    %% User interaction
    A -- User Message/Profile/Audio --> B
    B -- API Calls --> F
    B -- Calls --> C
    C -- RAG Query --> F
    C -- Embedding/LLM --> D
    B -- TTS Request --> E
    E -- Audio Stream --> B
    B -- Audio/Text Response --> A
    G -- Ingestion Script --> F

    %% Data flow labels
    classDef ext fill:#f9f,stroke:#333,stroke-width:2px;
    class D,E ext;
    classDef db fill:#bbf,stroke:#333,stroke-width:2px;
    class F db;
    classDef storage fill:#bfb,stroke:#333,stroke-width:2px;
    class G storage;
```

---

**Legend:**
- **Lovable Web App:** User interface for chat, profile, and audio.
- **FastAPI Server:** Handles API endpoints, user logic, and orchestration.
- **LangChain:** Manages prompt construction, RAG, and LLM calls.
- **Supabase:** Stores user auth, profiles, messages, and RAG vectors.
- **OpenAI:** Provides LLM (GPT-4o) and embeddings for RAG.
- **ElevenLabs:** Provides TTS audio for agent responses.
- **Docs Folder:** Local knowledge base, ingested into Supabase for RAG.

**Flow:**
1. User interacts via Lovable (chat, profile, audio).
2. FastAPI handles requests, fetches/saves data in Supabase, and orchestrates LangChain.
3. LangChain retrieves relevant docs (RAG) and calls OpenAI for LLM/embeddings.
4. FastAPI calls ElevenLabs for TTS as needed.
5. All knowledge base docs are ingested into Supabase for RAG. 