# System Architecture: Lenny Growth Assistant

This document outlines the technical architecture, data flows, database schemas, security sandbox model, and deployment topology of the Lenny Growth Assistant.

---

## 1. High-Level Architecture

```
                                      BROWSER CLIENT
               (Next.js App Router: RSC, Client Components, Tailwind, Lucide)
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       │ HTTP / SSE Requests                       │
                       ▼                                           ▼
             /api/chat (SSE Proxy)                      /api/sessions, /api/config
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │
                                             ▼
                                  FASTAPI APPLICATION (Port 8000)
                                ┌──────────────────────────────────┐
                                │ - Observability Middleware       │
                                │ - CORS & Security Headers        │
                                │ - Session & Message Router       │
                                │ - Model Router & Fallback Chain  │
                                │ - RAG Agent & Ship 30 Engine     │
                                │ - Sandboxed Artifact Service     │
                                └──────────────────────────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               ▼                             ▼                             ▼
       MODEL ROUTER LAYER           RETRIEVAL & VECTOR STORE          PERSISTENCE
 ┌───────────────────────────┐  ┌──────────────────────────────┐  ┌──────────────────┐
 │ Gemini 2.0 Flash (Direct) │  │ BM25 / Cosine Hybrid Index   │  │ PostgreSQL 16    │
 │ OpenRouter (Claude/GPT-4o)│  │ Top-k Chunk Search           │  │ (or SQLite local)│
 │ Ollama (llama3.1:8b local)│  │ Overlapping Metadata Chunks  │  │ Sessions, Messages│
 └───────────────────────────┘  └──────────────────────────────┘  │ Artifacts        │
                                                                  └──────────────────┘
```

---

## 2. Relational Database Schema

### `sessions` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | Primary Key | UUID identifier |
| `title` | `VARCHAR(255)` | Not Null | User-editable session title |
| `created_at` | `TIMESTAMP` | Not Null | Creation timestamp (UTC) |
| `updated_at` | `TIMESTAMP` | Not Null | Last update timestamp (UTC) |
| `user_metadata`| `JSON` | Nullable | User tags, domain, or parameters |

### `messages` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | Primary Key | UUID identifier |
| `session_id` | `VARCHAR(36)` | Foreign Key (`sessions.id`) | Cascading delete relationship |
| `role` | `VARCHAR(20)` | Not Null | `user`, `assistant`, or `system` |
| `content` | `TEXT` | Not Null | Raw message text / Markdown |
| `sources_json` | `JSON` | Default `[]` | Cited podcast episodes, guests, and snippets |
| `model_info_json`| `JSON`| Default `{}` | Provider, model ID, latency, fallback flag |
| `created_at` | `TIMESTAMP` | Not Null | Message creation timestamp |

### `artifacts` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | Primary Key | UUID identifier |
| `session_id` | `VARCHAR(36)` | Foreign Key (`sessions.id`) | Cascading delete relationship |
| `message_id` | `VARCHAR(36)` | Nullable | Associated message ID |
| `title` | `VARCHAR(255)` | Not Null | Artifact display title |
| `type` | `VARCHAR(20)` | Not Null | `html` or `markdown` |
| `content` | `TEXT` | Not Null | Sanitized artifact markup or markdown |
| `model_info_json`| `JSON`| Default `{}` | Model that generated the artifact |
| `created_at` | `TIMESTAMP` | Not Null | Timestamp |

---

## 3. Dynamic Model Router & Fallback Topology

The system uses task-based routing decoupled from caller code. If a provider fails (e.g. rate limit, missing key, connection error), the router automatically attempts subsequent providers down the chain.

```
Request: Task = "retrieval_qa"
   │
   ├─► 1. Primary: Gemini 2.0 Flash (Direct)
   │     └─► [Success] ──► Return response (fallback_used: false)
   │     └─► [Error / No Key]
   │           │
   │           ▼
   ├─► 2. Secondary: OpenRouter (anthropic/claude-3.5-sonnet)
   │     └─► [Success] ──► Return response (fallback_used: true)
   │     └─► [Error / No Key]
   │           │
   │           ▼
   └─► 3. Final Fallback: Local Ollama (llama3.1:8b)
         └─► [Success] ──► Return response (fallback_used: true)
         └─► [Unavailable] ──► Friendly error returned to UI
```

### Runtime Override API
- Evaluators can reassign tasks to models live via `POST /config`:
  ```json
  {
    "task": "retrieval_qa",
    "provider": "ollama",
    "model": "llama3.1:8b"
  }
  ```

---

## 4. Security & Sandboxing Model

Rendering user/LLM-generated HTML poses severe Cross-Site Scripting (XSS) risks. We implement defense-in-depth:

1. **Strict Iframe Sandbox**:
   - Rendered using `<iframe sandbox="allow-scripts">`.
   - Strictly omitting `allow-same-origin`: the frame runs in a unique null origin, physically preventing access to the parent document, cookies, `localStorage`, or `sessionStorage`.
2. **Backend HTML Sanitization**:
   - `sanitize_html_artifact` strips external script tags `<script src="https://...">` to eliminate arbitrary remote script execution.
   - Neutralizes DOM navigation APIs (`window.top`, `window.parent`).
3. **Content Security Policy**:
   - Headers on `/artifacts/{id}/raw`:
     ```http
     Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';
     X-Frame-Options: SAMEORIGIN
     ```

---

## 5. API Endpoint Specifications

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | System health check (DB, Ollama, Cloud LLMs). |
| `GET` | `/config` | Returns active routes, providers reachability, and audit logs. |
| `POST` | `/config` | Dynamically reconfigures task-to-model assignments. |
| `GET` | `/sessions` | Lists sessions with message counts, sorted by recency. |
| `POST` | `/sessions` | Creates a new chat session. |
| `GET` | `/sessions/{id}` | Fetches session detail with message history and artifacts. |
| `DELETE`| `/sessions/{id}` | Deletes session and associated messages/artifacts. |
| `POST` | `/sessions/{id}/chat` | Grounded RAG conversational endpoint (JSON). |
| `POST` | `/sessions/{id}/chat/stream` | Token-by-token Server-Sent Events (SSE) stream. |
| `POST` | `/sessions/{id}/skills/ship30`| Executes Ship 30/30 atomic essay generator. |
| `POST` | `/sessions/{id}/artifacts` | Generates interactive HTML/Markdown artifact. |
| `GET` | `/artifacts/{id}/raw` | Serves raw HTML with CSP headers for safe iframe rendering. |
