# Product Requirements Document (PRD) & Discovery Brief: Lenny Growth Assistant

**Document Status:** Approved & Active  
**Author:** AI Product Engineering  
**Target Delivery:** Production-grade take-home implementation  

---

## 1. Executive Summary & Problem Statement

Lenny Rachitsky's podcast repository comprises hundreds of hours of interviews with world-class product, growth, and engineering leaders (e.g., Elena Verna, Brian Balfour, Shreyas Doshi, Sean Ellis). Product Managers, Growth Leads, and Startup Founders regularly face tactical growth and product strategy challenges (e.g., *How do we construct retention loops?*, *What activation metrics matter in B2B PLG?*), but finding specific, high-signal, battle-tested insights requires manually sifting through hours of transcripts.

**The Lenny Growth Assistant** is a specialized, grounded conversational intelligence platform that:
1. Answers nuanced growth and product inquiries with strict transcript grounding and inline verifiable citations.
2. Formats actionable synthesis into viral content frameworks using the **Ship 30 for 30** atomic essay skill.
3. Generates interactive growth calculators, roadmaps, and cheat sheets within a **sandboxed artifact environment**.
4. Delivers resilient multi-provider model routing across **Google Gemini (Direct)**, **OpenRouter (Multi-model: Claude 3.7 / GPT-4o)**, and **local Ollama (`llama3.1:8b`)**, enabling seamless offline local execution and cloud cost-performance optimization.

---

## 2. Target Users & Jobs-to-be-Done (JTBD)

### Primary Personas
1. **Growth Lead / Head of Growth**: Needs rapid benchmarking on acquisition channels, conversion funnels, and activation tactics backed by exact quotes from industry pioneers.
2. **Product Manager (0-to-1 / Scale-up)**: Needs frameworks to define North Star metrics, retention curves, and customer feedback loops without getting generic LLM fluff.
3. **Founder / Solo Operator**: Needs actionable frameworks to draft viral LinkedIn/Substack essays ("Ship 30 for 30" style) synthesizing growth advice into audience-building assets.

### Core Jobs-to-be-Done
- *When I am* planning an activation experiment, *I want to* query Elena Verna's exact advice on time-to-value, *so that I can* cite authoritative precedents in our product spec.
- *When I have* extracted a high-value insight on growth loops, *I want to* convert it into a structured Ship 30/30 atomic essay with one click, *so that I can* share actionable takeaways with my team and audience.
- *When I am* demonstrating the assistant in an offline or air-gapped environment, *I want the system to* seamlessly fall back to local Ollama (`llama3.1:8b`), *so that I can* run the application without cloud API dependencies.

---

## 3. Success Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| **Citation Precision** | **≥ 85%** | Percentage of test answers containing verified episode, guest, and timestamp/chunk attribution. |
| **Grounded Faithfulness** | **≥ 95%** | Retrieval verification: answers only cite verified transcript content; declines to answer when knowledge is absent. |
| **Response Latency (Cloud)** | **p50 < 2.5s** | End-to-end time to first token using Gemini 2.0 Flash via SSE stream. |
| **Response Latency (Local)** | **p50 < 6.0s** | End-to-end time to first token on local Ollama (`llama3.1:8b`). |
| **Sandbox Security Violations** | **0%** | Sandboxed iframe tests: zero cookie access, zero top-level window redirects, zero parent DOM leakage. |

---

## 4. System Assumptions & Strategic Trade-offs

1. **Transcript Corpus Sampling**:
   - *Assumption*: Full ingestion of all 200+ podcast episodes exceeds take-home storage constraints and adds redundant token ingestion overhead.
   - *Decision*: Curate a high-signal canonical corpus representing core growth pillars:
     - Elena Verna (B2B Product-Led Growth & Activation)
     - Brian Balfour (Growth Loops vs. Traditional Funnels)
     - Shreyas Doshi (High-Agency PMing & Good vs. Great Product Metrics)
     - Lenny Rachitsky (Finding Product-Market Fit & 0-to-1 Playbooks)
   - *Extensibility*: Ingestion CLI (`python -m ingestion.ingest --refresh`) is built to batch-process arbitrary transcript additions dynamically.

2. **Model Router vs. Hardcoded Toggle**:
   - *Trade-off*: The rubric asks for model flexibility. Rather than a static toggle, we implement a **task-based model router** with automated 3-tier fallback (`Gemini` -> `OpenRouter` -> `Ollama`).
   - *Rationale*: Different tasks have divergent requirements:
     - Retrieval QA demands large context and speed -> Gemini 2.0 Flash.
     - Long-form essays require nuanced rhetorical styling -> Claude 3.7 Sonnet / GPT-4o via OpenRouter.
     - Local demonstration demands zero cloud connectivity -> Ollama.

3. **Orchestration Layer**:
   - *Architecture*: Model-agnostic agent orchestration. The tool-calling and retrieval loops are decoupled from model providers, allowing hot-swapping of models at runtime.

4. **Dual Vector Store Strategy**:
   - *Decision*: Native support for `pgvector` in PostgreSQL for Docker deployments, with an automated, zero-config local vector store fallback for local development and unit testing without requiring an external PostgreSQL instance.

---

## 5. Scope Boundaries

### In Scope
- **RAG Chat Experience**: Next.js App Router UI with real-time SSE streaming, collapsible citation source cards, and per-message model provider badges.
- **Dynamic Model Router**: Live runtime model overrides via Settings Drawer with automatic fallback chains and reachable provider health pings.
- **Ship 30 for 30 Skill**: Rubric-based generator crafting atomic essays (Hook, 1-3-1 cadence, skimmable structure, actionable conclusion, ~1,000 words).
- **Sandboxed Artifact Viewer**: Two-pane Claude-style viewer rendering HTML and Markdown with strict iframe sandboxing (`sandbox="allow-scripts"`).
- **Session Management**: Session history grouped by recency (Today, Yesterday, Previous 7 Days) persisted in relational storage.
- **Docker Compose**: One-command initialization of PostgreSQL + pgvector, FastAPI, and Next.js frontend.

### Out of Scope (Deferred to Future Milestones)
- Multi-user authentication & role-based access control (OAuth/Clerk).
- Speech-to-speech / real-time audio generation.
- Full model fine-tuning (LoRA/QLoRA).
- Full 200+ episode automated YouTube transcript scraper.

---

## 6. Risk Analysis & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| **Hallucination on ungrounded queries** | High | System prompt explicitly forbids guessing. If retrieval score is below threshold, output clean: *"This topic is not covered in the curated transcripts."* |
| **Ollama Service Unavailable Locally** | Medium | `/health` and model router detect Ollama status; gracefully falls back to cloud providers or alerts user in UI with actionable setup command. |
| **XSS / Malicious Script in Artifacts** | Critical | HTML artifacts render exclusively inside `<iframe sandbox="allow-scripts">` without `allow-same-origin`. Script tags to external hosts are stripped. |
| **Cloud API Quota / Rate Limits** | Medium | Transparent fallback chain: if Gemini fails or lacks key, router falls back to OpenRouter, then to Ollama, annotating the UI message with `ⓘ Fallback used: [Provider]`. |
| **Frontend-Backend Desynchronization** | Low | Next.js route handlers act as a typed Backend-for-Frontend (BFF), proxying requests and keeping cloud API keys strictly backend-side. |
