# Lenny Growth Assistant — Combined Master Build Plan

This document synthesizes `Lenny growth assistant guide.MD` and `Lenny growth assistant guid for frontend design.md` into a single, cohesive, production-grade roadmap.

---

## 1. System Architecture

```
 Browser (Desktop & Mobile)
    │
    │ HTTPS (SSE / JSON)
    ▼
┌─────────────────────────────────────────────────────────────┐
│             Next.js Frontend (App Router + RSC)             │
│  - Sidebar: Sessions (grouped by date), Model Settings      │
│  - Chat Thread: Live SSE streaming, Citations, Ship 30 CTA  │
│  - Artifact Viewer: Sandboxed <iframe>, Code, MD, Export    │
│  - Settings Drawer: Dynamic Model Router overrides & pings  │
└─────────────────────────────────────────────────────────────┘
    │
    ├── /api/chat           ──► Proxies & streams SSE from FastAPI
    ├── /api/sessions       ──► Session management
    ├── /api/artifacts/[id] ──► Artifact retrieval
    └── /api/config         ──► Model router inspection & updates
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                 │
│  - Health & Config endpoints (`/health`, `/config`)         │
│  - Session & Message persistence (`/sessions`)              │
│  - Model Router (`router.py`) with 3-tier fallback chains   │
│  - RAG Agent Loop & Ship 30/30 skill engine                 │
│  - Sandboxed Artifact Generation & Sanitization Engine      │
│  - Structured JSON Observability & Tracing                  │
└─────────────────────────────────────────────────────────────┘
    │
    ├──► Model Router
    │       ├── Tier 1: Google Gemini (2.0 Flash / Pro) - Direct SDK/REST
    │       ├── Tier 2: OpenRouter (Claude 3.7 Sonnet, GPT-4o, Llama 3.3)
    │       └── Tier 3: Ollama (llama3.2:3b) - Local Offline Fallback
    │
    ├──► Retrieval & Vector Engine
    │       ├── pgvector (PostgreSQL vector extension)
    │       └── Local Lightweight Vector Fallback (Chroma/sqlite-vec/FAISS)
    │
    └──► Storage Layer (PostgreSQL / SQLite fallback)
            ├── sessions (id, created_at, title, metadata)
            ├── messages (id, session_id, role, content, sources, model_info)
            ├── artifacts (id, session_id, type, title, content, model_info)
            └── routing_logs (id, task, provider, model, latency_ms, fallback_used)
```

---

## 2. Model Routing & Fallback Matrix

| Task Type | Primary Provider & Model | Secondary Fallback | Final Local Fallback | Rationale |
|---|---|---|---|---|
| `retrieval_qa` | **Gemini 2.0 Flash** | OpenRouter (`anthropic/claude-3.5-sonnet`) | Ollama (`llama3.2:3b`) | Massive context window for multiple transcript chunks, ultra-low latency, grounded generation. |
| `essay_generation` | **OpenRouter** (`anthropic/claude-3.7-sonnet` or `openai/gpt-4o`) | Gemini Pro | Ollama (`llama3.2:3b`) | Deep synthesis, long-form narrative cadence matching Ship 30/30 rubric. |
| `artifact_generation` | **Gemini 2.0 Flash** / OpenRouter | OpenRouter (`gpt-4o`) | Ollama (`llama3.2:3b`) | High syntax fidelity for HTML/CSS/JS and Markdown code generation. |
| `intent_routing` | **Gemini 2.0 Flash** | Ollama (`llama3.2:3b`) | Rule-based regex heuristic | Fast, deterministic classification of prompt intentions. |
| `offline_demo_mode` | **Ollama** (`llama3.2:3b`) | Rule-based responses | None | Completely air-gapped demo capability without cloud keys. |

---

## 3. Detailed Phase Breakdown

### Phase 0: Repo Scaffolding & Git Initialization
- **Deliverables**:
  - Root directory layout: `backend/`, `frontend/`, `ingestion/`, `docs/`, `agent-transcripts/`.
  - Comprehensive root `.gitignore` (Python virtual environments, `.env`, `node_modules`, `.next`, `__pycache__`, `*.db`, vector caches).
  - Clean `git init`, initial branch `main`.
- **Validation**:
  - `git status` verifies clean untracked list matching `.gitignore`.
- **Commit**: `chore: scaffold repo structure`

---

### Phase 1: Discovery Brief & PRD
- **Deliverables**:
  - `docs/PRD.md`: Concrete jobs-to-be-done, target personas (growth leads, founders, PMs), success metrics (≥80% citation accuracy, sub-6s p50 latency), scope boundaries (RAG chat, Ship 30/30 skill, Artifact viewer, local/cloud toggle), technical assumptions, and risk mitigations (hallucination guardrails, iframe sandboxing, API cost/latency fallback).
- **Validation**:
  - Document completeness and rubric alignment check.
- **Commit**: `docs: add PRD and discovery brief`

---

### Phase 2: Minimal FastAPI Backend with Health Check
- **Deliverables**:
  - `backend/app/main.py`: FastAPI application with CORS middleware, lifespan events, structured JSON error handlers.
  - `backend/app/config.py`: Pydantic `BaseSettings` reading environment variables with graceful defaults.
  - `GET /health` endpoint returning:
    ```json
    {
      "status": "healthy",
      "db": true,
      "ollama": false,
      "cloud_llm_configured": true,
      "version": "0.1.0"
    }
    ```
  - `requirements.txt` / `pyproject.toml` with pinned, compatible dependencies.
- **Validation**:
  - Automated test with `TestClient(app)` verifying `/health` response structure and status code 200.
- **Commit**: `feat: bootstrap FastAPI app with health endpoint`

---

### Phase 3: PostgreSQL & Session Persistence
- **Deliverables**:
  - `backend/app/db/session.py`: Async/sync SQLAlchemy engine supporting PostgreSQL (via `psycopg2` or `asyncpg`) with auto-fallback to SQLite for friction-free zero-config local testing.
  - `backend/app/models/`:
    - `SessionModel`: id (UUID), title, created_at, updated_at, user_metadata.
    - `MessageModel`: id (UUID), session_id, role, content, sources (JSON), model_info (JSON), created_at.
    - `ArtifactModel`: id (UUID), session_id, message_id, title, type (`markdown` | `html`), content, created_at.
  - CRUD repositories and Pydantic schemas.
  - Endpoints:
    - `POST /sessions` — create a new chat session.
    - `GET /sessions` — list sessions grouped/sorted by updated date.
    - `GET /sessions/{id}` — fetch session detail with message history.
    - `DELETE /sessions/{id}` — remove a session.
- **Validation**:
  - Pytest integration tests: create session, save messages, fetch history, cascade delete.
- **Commit**: `feat: add Postgres persistence for sessions and messages` & `test: add persistence integration tests`

---

### Phase 4: Multi-Provider LLM Layer
- **Deliverables**:
  - `backend/app/llm/base.py`: Normalized abstract interface:
    - `generate(messages, system_prompt, tools, response_format) -> LLMResponse`
    - `stream(messages, system_prompt, tools) -> AsyncIterator[str]`
    - `LLMResponse`: text, tool_calls, usage (input/output tokens), latency_ms, provider, model.
  - `backend/app/llm/gemini_provider.py`: Native Google Gemini API client (REST or `google-genai`/`google-generativeai`).
  - `backend/app/llm/openrouter_provider.py`: OpenRouter client hitting OpenAI-compatible completions API with customizable headers and multi-model routing.
  - `backend/app/llm/ollama_provider.py`: Local Ollama REST client (`http://localhost:11434/api/chat` or `api/generate`).
  - Graceful connection testing and credentials validation.
- **Validation**:
  - Unit tests with mock providers and live integration smoke tests verifying normalized `LLMResponse` attributes.
- **Commit**: `feat: add multi-provider LLM layer (Gemini, OpenRouter, Ollama)`

---

### Phase 4.5: Dynamic Model Router with Fallback Chains
- **Deliverables**:
  - `backend/app/llm/router.py`: Task-based router mapping tasks (`intent_routing`, `retrieval_qa`, `essay_generation`, `artifact_generation`, `offline_demo_mode`) to provider sequences.
  - Fallback execution loop: attempt primary -> catch network/quota error -> fallback to secondary -> fallback to Ollama -> record fallback flag.
  - Endpoints:
    - `GET /config`: Returns active routing table, configured providers, and live health/reachability status of each LLM.
    - `POST /config`: Allows live override of routing choices from the UI settings drawer without restarting the server.
  - Structured audit logging of every routing decision.
- **Validation**:
  - Unit test simulating primary failure triggering secondary and local Ollama fallback.
- **Commit**: `feat: add task-based model router with fallback chains`

---

### Phase 5: Transcript Ingestion & Vector Retrieval
- **Deliverables**:
  - High-value curated Lenny Podcast transcripts dataset stored in `ingestion/data/` (e.g., Elena Verna on B2B PLG, Brian Balfour on Growth Loops, Shreyas Doshi on High-Agency PMing, Lenny Rachitsky on Finding PMF).
  - `ingestion/chunker.py`: Overlapping chunking (~500 tokens / 1500 chars) retaining metadata (`episode_title`, `guest`, `topic`, `url`, `chunk_id`).
  - `backend/app/retrieval/vector_store.py`: Vector search abstraction supporting `pgvector` with automatic lightweight local store fallback (ChromaDB / SQLite-vec / Cosine similarity) so that the app runs seamlessly in all environments.
  - `ingestion/ingest.py` CLI: `python -m ingestion.ingest --refresh` to ingest, embed, and index transcripts.
- **Validation**:
  - Automated retrieval unit tests: querying "retention loops" or "activation metrics" retrieves top-k chunks with high similarity score and correct episode attribution.
- **Commit**: `feat: add transcript ingestion and chunking pipeline` & `test: add retrieval unit tests`

---

### Phase 6: Grounded RAG Conversational Assistant
- **Deliverables**:
  - `backend/app/agent/rag.py`: Orchestrated RAG workflow:
    1. Retrieve relevant transcript chunks via vector search.
    2. Format prompt with strict grounding instructions: cite source title inline `[Episode - Guest]`, never fabricate, declare if outside transcript knowledge.
    3. Invoke Model Router (`task="retrieval_qa"`).
    4. Format and extract cited references into structured source cards.
  - Integration with `POST /sessions/{id}/messages` with both JSON reply and SSE streaming endpoint `POST /sessions/{id}/chat/stream`.
  - Storage of `model_info` and `sources` in `messages` table.
- **Validation**:
  - Integration test verifying grounded citation formatting and empty-retrieval disclaimer behavior.
- **Commit**: `feat: implement grounded RAG chat with source citations`

---

### Phase 7: Ship 30 for 30 Content Creation Skill
- **Deliverables**:
  - `backend/app/skills/ship30.py`:
    - Rubric-driven atomic essay generator: strong punchy hook, 1-3-1 sentence cadence, skimmable subheadings, single core thesis, actionable takeaway, ~800–1200 words.
    - Integrated with Model Router (`task="essay_generation"`).
  - Tool trigger: `write_ship30_essay(topic, context)` that can be invoked via chat slash command, intent detection, or direct API endpoint `POST /sessions/{id}/skills/ship30`.
- **Validation**:
  - Test verifying rubric compliance, structural headers, and grounded incorporation of transcript knowledge.
- **Commit**: `feat: add Ship 30/30 essay-writing skill`

---

### Phase 8: Artifact Generation & Sandboxed Viewer
- **Deliverables**:
  - `backend/app/services/artifact_service.py`: Generates structured artifacts (HTML landing pages, growth models, calculators, interactive dashboards, markdown frameworks).
  - Persistence in `artifacts` table linked to session.
  - Frontend security-first Artifact Viewer:
    - Sandboxed iframe with `sandbox="allow-scripts"` (strictly NO `allow-same-origin`, preventing DOM access, cookie theft, or malicious top-level redirects).
    - HTML Sanitization (DOMPurify).
    - Code inspection tab with syntax highlighting, Markdown rendering tab, and 1-click Download / Copy actions.
- **Validation**:
  - Unit test for HTML sanitization and iframe sandbox attribute enforcement.
- **Commit**: `feat: add artifact generation with sandboxed HTML viewer`

---

### Phase 9: Modern Frontend Chat UI (Next.js App Router)
- **Deliverables**:
  - Next.js 14/15 App Router application with Tailwind CSS and Lucide icons:
    - `frontend/app/layout.tsx`: Dark/light elegant PM-focused theme.
    - `frontend/app/page.tsx`: Seamless redirect or default new session initialization.
    - `frontend/app/chat/[sessionId]/page.tsx`: RSC initial data load + client interactive thread.
    - `frontend/app/api/chat/route.ts`: Streaming SSE proxy route.
    - `frontend/components/layout/Sidebar.tsx`: Session list grouped by date (Today, Yesterday, Previous 7 Days), `+ New Chat` button, and `⚙ Settings` button.
    - `frontend/components/chat/MessageList.tsx`: Message bubbles with Markdown rendering, inline Provider Badge (`[Gemini Flash]`), fallback indicators (`ⓘ Fallback used: Ollama`), and interactive citation source cards.
    - `frontend/components/chat/MessageInput.tsx`: Auto-expanding text input, quick prompt chips, and Ship 30 quick action button.
    - `frontend/components/artifact/ArtifactViewer.tsx`: Two-pane desktop split (40% chat / 40% artifact / 20% sidebar) and mobile responsive sheet/modal, supporting Preview, Code, and Markdown tabs.
    - `frontend/components/settings/SettingsDrawer.tsx`: Model router configuration modal for changing per-task models and viewing live provider connectivity pings.
- **Validation**:
  - Next.js build compilation passes with zero TypeScript errors.
- **Commit**: `feat: build Next.js chat interface with session management`

---

### Phase 10: Observability & Resilience
- **Deliverables**:
  - Structured JSON logging across all backend services: timestamps, request IDs, LLM call tokens, latency in milliseconds, retrieval hit counts, and router fallback flags.
  - Unified error handling: graceful HTTP 503 on database disruption, descriptive error messages for missing keys rather than unhandled 500 exceptions, and automatic fallback notifications surfaced directly to the UI.
- **Validation**:
  - Test verifying JSON log format and graceful error responses under simulated failure scenarios.
- **Commit**: `feat: add structured logging and resilient failure handling`

---

### Phase 11: Docker Compose & Production Scaffolding
- **Deliverables**:
  - `docker-compose.yml`: Multi-service orchestration including:
    - `db`: PostgreSQL 16 with `pgvector` extension.
    - `backend`: FastAPI Python container.
    - `frontend`: Next.js production container.
    - `ollama`: Optional Ollama service container with volume persistence.
  - `.env.example`: Thoroughly documented configuration file differentiating backend secrets from public frontend environment variables.
- **Validation**:
  - Verify `docker-compose config` syntax and port mapping sanity.
- **Commit**: `chore: add Docker Compose deployment and env example`

---

### Phase 12: Comprehensive Test Suite & Manual Test Checklist
- **Deliverables**:
  - Automated test suite covering:
    - Backend API contract and status endpoints.
    - Database CRUD and session persistence.
    - Model Router fallback mechanics.
    - Vector retrieval accuracy and ranking.
    - Ship 30/30 skill generation.
    - Artifact rendering and sanitization.
  - `docs/manual_test_plan.md`: Step-by-step verification checklist for evaluators covering local Ollama execution, cloud keys, artifact interaction, and responsive design.
- **Validation**:
  - Full test suite execution passes.
- **Commit**: `test: consolidate automated test suite and add manual test plan`

---

### Phase 13: Comprehensive Documentation
- **Deliverables**:
  - `README.md`: System overview, quickstart instructions (Docker & manual), environment setup, architecture highlights, and troubleshooting.
  - `docs/PRD.md`: Refined and complete product requirements document.
  - `docs/architecture.md`: In-depth database schemas, API specifications, vector retrieval pipeline, model router design, and security sandbox policies.
  - `docs/design.md`: UI/UX design rationale, layout wireframes, state management, accessibility compliance, and mobile responsive considerations.
- **Validation**:
  - Markdown lint and link verification.
- **Commit**: `docs: complete README, architecture, and design docs`

---

### Phase 14: Coding Agent Transcripts & Audit Logs
- **Deliverables**:
  - `agent-transcripts/`: Documented session logs detailing the build process, prompt engineering iterations, test failure diagnostics, and corrections.
- **Validation**:
  - Ensure zero credential leakage or sensitive API keys in transcripts.
- **Commit**: `docs: add coding agent transcripts`

---

### Phase 15: Demo Video Script & Walkthrough Guide
- **Deliverables**:
  - `docs/demo_video_script.md`: A structured 2–3 minute video demonstration script highlighting the grounded RAG responses, switching between cloud and local Ollama models, executing the Ship 30/30 skill, interacting with the sandboxed artifact viewer, and explaining architecture trade-offs.
- **Commit**: `docs: add demo video script and presentation guide`

---

### Phase 16: Final Polish & Verification Pass
- **Deliverables**:
  - Clean linting across frontend and backend.
  - Verification of clean git commit log.
  - Final sanity check for secrets and temporary files.
- **Commit**: `chore: final polish and verification pass`
