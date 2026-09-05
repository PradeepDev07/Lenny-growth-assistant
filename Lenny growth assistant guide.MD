# Lenny Growth Assistant — Build Guide

A phase-by-phase path through the assignment, ordered so each step teaches you what the next one needs. Commit after every phase (suggested messages included) so your git history itself becomes evidence of process — which the rubric explicitly rewards ("agent transcripts," "communication," "code quality").

---

## Phase 0 — Repo scaffolding (30–60 min)

**Goal:** a repo that boots empty but correctly structured.

```
lenny-growth-assistant/
├── backend/            # FastAPI app
├── frontend/           # React/Vite app
├── ingestion/          # transcript loading + chunking scripts
├── docs/
│   ├── PRD.md
│   ├── design.md
│   └── architecture.md
├── agent-transcripts/  # your coding-agent logs, later
├── docker-compose.yml
├── .env.example
└── README.md
```

Init git, add a `.gitignore` (node_modules, .env, __pycache__, .venv, *.db), push an empty skeleton immediately.

```bash
git init && git add . && git commit -m "chore: scaffold repo structure"
git remote add origin <your-repo-url> && git push -u origin main
```

**Why first:** you want every subsequent commit to layer onto a visible structure, not arrive as one giant blob.

---

## Phase 1 — Discovery brief + PRD (before any code)

Write `docs/PRD.md` now, while the ambiguity is fresh. This is the artifact evaluators read first, and writing it before coding forces you to make (and record) the scope decisions you'll otherwise make silently and forget.

Cover, concretely:
- **User & job-to-be-done:** e.g. "a PM or growth lead who wants a fast, cited answer to 'how do I think about activation metrics' without reading 40 transcripts."
- **Success metric:** pick something measurable and honest, e.g. "≥80% of test questions answered with a correct citation to a real transcript" or "p50 response latency < 6s on local Ollama."
- **Assumptions:** which transcripts subset you'll use (the full corpus is huge — say so if you sample); which local model (Ollama); which cloud providers (Gemini direct + OpenRouter for multi-model access) and why you chose a router over the brief's single Claude/OpenAI toggle; and that orchestration uses Pi Coding Agent (or a documented hand-rolled loop) decoupled from the model layer.
- **Scope in/out:** e.g. in: RAG chat, Ship 30/30 skill, artifact viewer, local+cloud toggle. Out: multi-user auth, streaming voice, fine-tuning.
- **Risks:** hallucination, Ollama unavailability, XSS from rendered HTML artifacts, cost/latency of cloud fallback.

Commit: `docs: add PRD and discovery brief`

---

## Phase 2 — Minimal FastAPI backend with health endpoint

Stand up the smallest possible backend before touching the model or DB, so you have something to run and test at every later step.

- `backend/app/main.py` with FastAPI app
- `GET /health` returning `{status, db: bool, ollama: bool, cloud_llm_configured: bool}`
- Pydantic settings class reading from `.env`
- CORS middleware for local frontend dev

Commit: `feat: bootstrap FastAPI app with health endpoint`

**Learning note:** get this deployed via `uvicorn` and curl it before adding anything else. Every later phase should keep `/health` truthful.

---

## Phase 3 — PostgreSQL + session persistence

Now add state, since the agent and RAG layers you'll build next both need somewhere to write.

- Docker Compose service for Postgres (or point at Supabase/Railway).
- SQLAlchemy models: `Session(id, created_at, user_metadata)`, `Message(id, session_id, role, content, created_at, sources_json)`.
- Alembic (or a simple `create_all` for this scope — document which you chose and why).
- Endpoints: `POST /sessions`, `GET /sessions/{id}/messages`, `POST /sessions/{id}/messages`.
- Basic request/response Pydantic schemas + structured error responses (a consistent `{error: {code, message}}` shape).

Commit: `feat: add Postgres persistence for sessions and messages`

Write your first real test here: create a session, post a message, fetch it back. This is cheap now and painful to retrofit later.

Commit: `test: add persistence integration tests`

---

## Phase 4 — Multi-provider LLM layer (Gemini + OpenRouter + Ollama)

Build the abstraction before you build the agent that uses it, so RAG and the skill layer are provider-agnostic from day one. You're running three provider families instead of one, so the interface needs to be strict about the lowest common denominator (messages, system prompt, optional tools, optional JSON mode) rather than leaking any single provider's quirks upward.

- `backend/app/llm/base.py`: one interface every provider implements, e.g. `generate(messages, system, tools=None, response_format=None) -> LLMResponse`, where `LLMResponse` normalizes `text`, `tool_calls`, `usage`, `latency_ms`, `provider`, `model`.
- `backend/app/llm/gemini_provider.py` — calls the Google Gemini API directly (`google-generativeai` SDK or REST). Good for: large-context grounded Q&A (Gemini's long context window is a natural fit for stuffing several transcript chunks) and low-cost/low-latency calls.
- `backend/app/llm/openrouter_provider.py` — one HTTP client hitting `https://openrouter.ai/api/v1/chat/completions`, parameterized by `model` (e.g. `openai/gpt-4o`, `anthropic/claude-sonnet-4-6`, `meta-llama/llama-3.1-70b-instruct`). This is your "multi-model" tier: one integration, many models, useful when you want to A/B a task across models without writing new provider code each time.
- `backend/app/llm/ollama_provider.py` — local model, mandatory for the demo. Pull one now: `ollama pull llama3.1:8b` (or smaller if your machine is constrained).
- Config: `.env` holds `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `OLLAMA_BASE_URL`, and per-task model IDs (see Phase 4.5). `GET /config` exposes which providers are actually configured/reachable and which model is currently serving each task, so the frontend can show something like "QA: Gemini 2.0 Flash · Essay: Claude 3.7 Sonnet (via OpenRouter) · Local fallback: llama3.1:8b."
- Fallback behavior: if a cloud provider errors or has no key, log it and fall back down the chain toward Ollama rather than failing the request outright — document the exact fallback order in `architecture.md`.

Commit: `feat: add multi-provider LLM layer (Gemini, OpenRouter, Ollama)`

---

## Phase 4.5 — Model router (pick the right model per action)

This is the piece that turns "three providers wired up" into an actual system design decision worth writing about in the PRD. The router's job: given a *task type*, return the provider+model that fits it best, with a fallback chain — not the caller picking a provider by hand each time.

**Keep it rule-based for this scope.** An LLM-that-picks-the-LLM adds latency and cost for a take-home; a small deterministic config table is easier to reason about, test, and explain to an evaluator. Mention the "smarter" version (a cheap classifier model choosing the tier) as a documented future improvement rather than building it.

Suggested task types and a reasonable default mapping:

| Task type | Why this tier | Suggested default |
|---|---|---|
| `intent_routing` (is this a QA question, an essay request, or an artifact request?) | Cheap, fast, low-stakes classification | Ollama local model, or Gemini Flash |
| `retrieval_qa` (grounded chat answers) | Needs a long context window to hold several transcript chunks + history; latency-sensitive | Gemini (Flash for speed, Pro if quality suffers) |
| `essay_generation` (Ship 30/30 skill) | Needs strong long-form writing quality; latency matters less | A strong OpenRouter model (e.g. `anthropic/claude-sonnet-4-6` or `openai/gpt-4o`) |
| `artifact_generation` (HTML/Markdown) | Needs reliable structured/formatted output | Mid-tier OpenRouter model or Gemini Pro |
| `offline/local demo mode` | No cloud keys available | Ollama, always |

Implementation:
- `backend/app/llm/router.py`: `get_model_for(task: str) -> (provider, model_id)`, reading a config dict (env-overridable: `MODEL_FOR_RETRIEVAL_QA`, `MODEL_FOR_ESSAY`, etc.) so an evaluator can remap tasks to models without touching code.
- Each call site (RAG chat, Ship 30/30 skill, artifact tool) asks the router for its task type instead of hardcoding a provider.
- Fallback chain per task: e.g. `retrieval_qa` tries Gemini → OpenRouter → Ollama, in that order, on error or missing key.
- Log every routing decision (`task`, `chosen_provider`, `chosen_model`, `fallback_used: bool`) — this becomes free evidence for the "observability" rubric line later and a nice screenshot for the demo video.
- Surface the current routing table at `GET /config` so the UI can show, per message, which model actually answered it.

Commit: `feat: add task-based model router with fallback chains`

**One assignment note to record in the PRD:** the brief's "agent integration" section names the Claude Agent SDK or Pi Coding Agent specifically for the *orchestration* layer (tool-calling loop, session state), which is a different concern from which model generates text. Pi Coding Agent is model-agnostic and pairs cleanly with this router; if you use it (or a small hand-rolled tool-calling loop) for orchestration while Gemini/OpenRouter/Ollama do the actual generation, say so explicitly as a documented deviation with rationale — that's exactly the kind of trade-off call the rubric wants to see reasoned about, not hidden.

---

## Phase 5 — Ingest Lenny's transcripts

Now that you can call a model, give it something to be grounded in.

- `ingestion/load_transcripts.py`: pull a reasonable subset of Lenny's Podcast transcripts (document exactly which ones and why — full-corpus scraping is out of scope for a take-home; say so in the PRD).
- Chunk by paragraph or ~500-token windows with overlap; keep `source_title`, `source_url_or_id`, `chunk_index` on every chunk.
- Embed each chunk (OpenAI/Anthropic embeddings, or a local sentence-transformers model to avoid extra cloud dependency) and store in Postgres with `pgvector`, or a lightweight local vector store (Chroma/FAISS) if you want to avoid pgvector setup — document the trade-off either way.
- Write a small `ingest.py` CLI: `python ingest.py --refresh` so an evaluator can re-run ingestion.

Commit: `feat: add transcript ingestion and chunking pipeline`

Test: assert a known query retrieves a chunk from the expected source.

Commit: `test: add retrieval unit tests`

---

## Phase 6 — RAG conversational assistant (agent layer)

This is where the LLM layer (Phase 4), the router (Phase 4.5), and retrieval (Phase 5) meet.

- Build the orchestration with Pi Coding Agent (or a small hand-rolled tool-calling loop, documented as such): a `retrieve_transcripts` tool the agent calls, then answers using only retrieved chunks. The agent asks the router for `task=retrieval_qa` rather than calling a provider directly, so swapping the underlying model later never touches this layer.
- System prompt: instruct the model to cite `source_title` inline and to say explicitly when the corpus doesn't support an answer — don't let it silently hallucinate.
- Wire into `POST /sessions/{id}/messages`: load prior messages for context, route + call the model, persist the reply with its sources **and** which provider/model actually answered (from the router's log).
- Handle empty retrieval gracefully (return "not covered by the transcripts I have" rather than a generic LLM guess).

Commit: `feat: implement grounded RAG chat with source citations`

Manual test now: ask a real PM question, confirm the citation is real and correct.

---

## Phase 7 — Ship 30 for 30 content skill

With grounded Q&A working, add the first "skill" as a structured tool rather than an ad-hoc prompt.

- Read the Ship 30/30 guide, distill it into an explicit rubric (hook, narrative arc, skimmable structure, one clear takeaway) and encode that rubric as a system prompt / few-shot template in `backend/app/skills/ship30.py`.
- Expose it as an agent tool: `write_ship30_essay(topic)` that first calls retrieval, then asks the router for `task=essay_generation` (should land on your stronger OpenRouter model per the Phase 4.5 table), generates ~1,250 words following the rubric, and checks word count/structure before returning.
- Trigger it from chat via an explicit command or intent classification (e.g. "turn this into a Ship 30/30 post").

Commit: `feat: add Ship 30/30 essay-writing skill`

---

## Phase 8 — Artifact generation + viewer

- Backend: an `artifact` tool/endpoint that requests `task=artifact_generation` from the router, returns `{type: "markdown"|"html", content, id, provider, model}`, and persists it linked to the session.
- Frontend: a two-pane layout (chat left, Artifact Viewer right) — the recognizable Claude Artifacts pattern.
- **Security:** render HTML artifacts inside a **sandboxed `<iframe sandbox="allow-scripts">`** (no `allow-same-origin` unless you truly need it), strip `<script src=...>` to external hosts, and/or sanitize with something like DOMPurify before ever injecting raw HTML into the parent DOM. Document exactly what's allowed (basic CSS/JS in the sandbox) vs blocked (top-level navigation, cookie/localStorage access, network calls to arbitrary hosts) in `architecture.md`.
- Markdown artifacts: render with a standard markdown renderer (react-markdown) — much lower risk, no sandboxing needed.

Commit: `feat: add artifact generation with sandboxed HTML viewer`

---

## Phase 9 — Frontend chat UI

- Session list / "new chat" button, message thread, streaming or simple polling response, provider indicator ("Anthropic" / "Ollama llama3.1"), loading and error states, empty states ("no answer found in transcripts").
- Responsive layout, keyboard accessibility, visible focus states — cheap wins for the UI/UX rubric line.

Commit: `feat: build chat interface with session management`

---

## Phase 10 — Observability & resilience

- Structured logging (JSON logs) around: LLM calls (provider, latency, tokens), retrieval (hit count, empty-result flag), DB errors, artifact render events.
- Graceful handling: missing API key → clear error surfaced in UI, not a 500; Ollama down → fallback message or auto-switch if configured; DB down → `/health` reflects it, endpoints return a clean 503.

Commit: `feat: add structured logging and resilient failure handling`

---

## Phase 11 — Docker Compose + one-command startup

- `docker-compose.yml`: postgres, backend, frontend, and an `ollama` service (or documented "install Ollama locally, we don't containerize GPU access" — be explicit).
- `.env.example` with every variable, sensible defaults, and comments on required vs optional.
- Confirm `docker compose up` from a clean clone actually works — test this in a fresh directory.

Commit: `chore: add Docker Compose deployment and env example`

---

## Phase 12 — Tests (fill remaining gaps)

By now you have scattered tests; consolidate:
- API contract tests (validation, error shapes)
- Retrieval correctness tests
- Agent routing test (does "make this a Ship 30 post" actually invoke the skill?)
- Persistence round-trip test
- A short **manual UI test plan** as a markdown checklist in `docs/`

Commit: `test: consolidate automated test suite and add manual test plan`

---

## Phase 13 — Write the remaining docs

- `README.md`: architecture overview, prerequisites, install, env vars, local + cloud model setup, run commands, tests, troubleshooting. Assume the reader has never seen the repo.
- `docs/architecture.md`: DB schema, API endpoints, ingestion/retrieval flow, agent routing, model toggle, security model, deployment topology.
- `docs/design.md`: UI/UX principles, IA, key interaction states, responsive behavior, accessibility notes.

Commit: `docs: complete README, architecture, and design docs`

---

## Phase 14 — Agent transcripts

Copy your coding-agent session logs (Claude Code, Cursor, etc.) into `agent-transcripts/`, including at least one failed attempt and the fix — scrub any secrets first.

Commit: `docs: add coding agent transcripts`

---

## Phase 15 — Demo video

Record 2–3 minutes, camera on: state the problem, show the chat answering with citations, switch the provider toggle to show Ollama running locally, and explain one real trade-off you made (e.g. why you sandboxed HTML instead of blocking it entirely). Upload to YouTube, link it in the README.

---

## Phase 16 — Final pass

- Re-clone the repo into a scratch folder and follow your own README literally, end to end, to catch anything that only works "on your machine."
- Squash any embarrassing WIP commits if you want a cleaner history (optional — a messy-but-honest history is fine too).
- Final commit: `chore: final polish and README verification pass`
- Push, then open the GitHub repo settings to confirm no secrets leaked (`git log -p | grep -i api_key` as a sanity check before your last push).

---

### Suggested order recap
Scaffold → PRD → FastAPI skeleton → Postgres/sessions → multi-provider LLM layer → model router → ingestion → RAG agent → Ship 30/30 skill → artifacts + viewer → chat UI → observability/resilience → Docker Compose → tests → docs → agent transcripts → demo video → final pass.

Each phase is independently committable and independently demoable — if you run out of time, you'll still have a coherent, working subset rather than a half-built everything.
