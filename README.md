# Lenny Growth Assistant

An AI-powered growth assistant grounded in Lenny Rachitsky's podcast interviews. It delivers verified growth frameworks, automated Ship 30 for 30 atomic essays, and sandboxed interactive artifacts with resilient multi-provider model routing across Google Gemini, OpenRouter, and local Ollama.

---

## Architecture at a Glance

```
 Browser (Next.js App Router + RSC + Route Handlers)
    │
    │ HTTPS / SSE
    ▼
 FastAPI Backend (Port 8000)
    ├── Task-based Model Router (Gemini 2.0 Flash, OpenRouter Claude/GPT-4o, Ollama Llama 3.2 3B)
    ├── BM25 / Vector Store (Curated Lenny Podcast Transcripts)
    ├── RAG Agent with In-line Citations & Strict Anti-Hallucination
    ├── Ship 30 for 30 Content Creation Skill
    ├── Sandboxed Artifact Generator & Viewer (<iframe sandbox="allow-scripts">)
    └── Structured JSON Observability & Health Probing
```

---

## Features

- **Strictly Grounded RAG Chat**: Answers questions about B2B PLG, activation metrics, growth loops, and PMF with citations linking to actual podcast episodes and guests.
- **Dynamic Model Router**: Task-based routing across Gemini, OpenRouter, and local Ollama with automatic 3-tier fallback chains and live runtime reconfigurability.
- **Ship 30 for 30 Skill**: Converts transcript insights into viral, atomic essays conforming to the 5-part Ship 30/30 writing rubric with one click.
- **Sandboxed Artifact Viewer**: Safely renders interactive HTML calculators, growth loops, and markdown frameworks inside an isolated sandbox iframe.
- **Session Persistence**: Chat sessions grouped by date (Today, Yesterday, Previous 7 Days) persisted with full message history and cited sources.
- **Full Observability**: Structured JSON logging capturing request durations, provider latency, tokens, and router fallback flags.

---

## Quickstart

### Option 1: Docker Compose (One-Command Startup)

```bash
# 1. Clone repo and enter folder
cd Lenny-growth-assistant

# 2. Configure environment keys
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY or OPENROUTER_API_KEY

# 3. Start all services (Postgres + pgvector, Backend, Frontend, Ollama)
docker compose up --build
```
- Frontend: `http://localhost:3000`
- FastAPI Backend & Swagger Docs: `http://localhost:8000/docs`

---

### Option 2: Local Standalone Development (Zero Docker Requirement)

#### 1. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Ingest and index transcripts
PYTHONPATH=. python -m ingestion.ingest --refresh

# Start FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## Running Automated Tests

Run the consolidated test suite (27 passing tests covering API contracts, persistence, routing fallbacks, retrieval precision, and HTML sandboxing):

```bash
source .venv/bin/activate
PYTHONPATH=. pytest backend/tests/ -v
```

---

## Documentation

- [**PRD & Discovery Brief**](file:///Users/macki/Desktop/Assement/Lenny-growth-assistant/docs/PRD.md): Persona definitions, success metrics, and scope boundaries.
- [**System Architecture**](file:///Users/macki/Desktop/Assement/Lenny-growth-assistant/docs/architecture.md): Database schemas, API endpoints, and sandbox security specs.
- [**Design Guidelines**](file:///Users/macki/Desktop/Assement/Lenny-growth-assistant/docs/design.md): UI wireframes, IA, and interaction states.
- [**Manual Test Plan**](file:///Users/macki/Desktop/Assement/Lenny-growth-assistant/docs/manual_test_plan.md): Step-by-step evaluator verification checklist.
- [**Combined Plan**](file:///Users/macki/Desktop/Assement/Lenny-growth-assistant/COMBAIEND%20PLAN.MD): Master execution roadmap.

---

## Model Configuration & Providers

| Task | Primary Provider | Fallback Chain |
|---|---|---|
| `retrieval_qa` | Gemini 2.5 Flash | OpenRouter (openrouter/free) -> Ollama (llama3.2:3b) |
| `essay_generation` | OpenRouter (openrouter/free) | Gemini 2.5 Flash -> Ollama (llama3.2:3b) |
| `artifact_generation` | Gemini 2.5 Flash | OpenRouter (openrouter/free) -> Ollama (llama3.2:3b) |
| `intent_routing` | Gemini 2.5 Flash Lite | Ollama (llama3.2:3b) |
| `offline_demo_mode` | Ollama (llama3.2:3b) | Local rule-based responses |

To change models dynamically at runtime, open the **Model Settings** drawer in the UI or send a `POST /config` request.
