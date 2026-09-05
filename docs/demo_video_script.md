# Demo Video Script & Walkthrough Guide (2–3 Minutes)

This script provides a concise, high-impact demonstration flow aligned with the evaluation rubric.

---

## Video Timeline Overview

| Timestamp | Section | Key Talking Points & Screen Actions |
|---|---|---|
| **0:00 – 0:30** | **The Problem & Setup** | State problem: PMs need fast, authoritative answers from Lenny's transcripts without reading hundreds of pages. Introduce the architecture (Next.js, FastAPI, multi-provider model router). |
| **0:30 – 1:15** | **Grounded RAG Chat & Citations** | Ask: *"How should we measure activation metrics in B2B PLG according to Elena Verna?"* Show live SSE token stream. Highlight the **`[Gemini 2.0 Flash]`** badge. Expand **"Sources Cited"** showing exact episode and quote. |
| **1:15 – 1:45** | **Ship 30 for 30 Content Skill** | Click **`[Turn into Ship 30/30 post]`**. Point out the 5-rule rubric: provocative 1-sentence hook, 1-3-1 cadence, actionable 3-step playbook, and attributed credit to Elena Verna. |
| **1:45 – 2:15** | **Sandboxed Artifact Viewer** | Click **`[Generate Interactive Artifact]`** or ask for a CAC/LTV calculator. Demonstrate the two-pane Claude-style split. Show tabs: **[Preview]**, **[Code]**, **[Raw]**. Explain the security trade-off: why HTML is sandboxed in an `<iframe>` without `allow-same-origin` rather than banned outright. |
| **2:15 – 2:45** | **Dynamic Model Router & Local Ollama** | Open **`⚙ Model Settings`**. Show live provider status (Gemini, OpenRouter, Ollama). Switch `retrieval_qa` to **`Ollama (llama3.2:3b)`**. Submit query and show the inline badge: **`[Ollama Llama 3.2] (Local)`** proving air-gapped demo capability. |
| **2:45 – 3:00** | **Wrap Up & Architecture Summary** | Highlight clean test suite (27 passing tests), Docker Compose one-command launch, and git commit history reflecting every step of the process. |

---

## Detailed Spoken Script

### 1. Introduction (0:00 - 0:30)
> *"Hi everyone! Today I’m demonstrating the Lenny Growth Assistant—an AI copilot built specifically for PMs, growth leads, and founders who want rapid, grounded answers from Lenny Rachitsky's podcast repository without sifting through hours of transcripts.
>
> On the frontend, we have Next.js App Router with server-rendered sessions and real-time SSE streaming. On the backend, we have a modular FastAPI service powered by a dynamic model router that balances Google Gemini 2.0 Flash, OpenRouter for Claude and GPT-4o, and local Ollama for offline execution."*

### 2. Grounded Q&A (0:30 - 1:15)
> *"Let's ask a nuanced growth question: 'How should we measure activation metrics in B2B PLG according to Elena Verna?'
>
> As you can see, the response streams in immediately via Server-Sent Events. Notice the model badge: this was answered by Gemini 2.0 Flash in under 200 milliseconds. More importantly, notice the inline attribution: Elena Verna's rule about time to value and Miro's 4x retention milestone. Underneath, our expandable Sources card cites the exact episode title, guest name, and transcript snippet. And if I ask something outside the corpus like quantum mechanics, it declines politely rather than hallucinating."*

### 3. Ship 30 for 30 Skill (1:15 - 1:45)
> *"Now let's turn this insight into a viral Atomic Essay. With one click on `[Turn into Ship 30/30 post]`, our agent triggers our Ship 30 content skill using Claude 3.7 Sonnet via OpenRouter.
>
> It follows the strict 5-part rubric: a counter-intuitive hook questioning vanity signups, the 1-3-1 cadence that gives text breathing room, a tactical 3-step playbook, and a punchy golden rule."*

### 4. Sandboxed Artifact Viewer & Security Architecture (1:45 - 2:15)
> *"Next, let's look at Artifacts. When we generate an interactive calculator, the interface dynamically splits into a two-pane layout inspired by Claude Artifacts.
>
> Here’s an important architectural decision: instead of blocking HTML or using risky innerHTML injection, our backend sanitizes external scripts and renders the HTML inside an isolated `<iframe>` with `sandbox="allow-scripts"`. By strictly omitting `allow-same-origin`, the artifact cannot access parent cookies, localStorage, or DOM elements. Evaluators can also inspect the code or download the file with one click."*

### 5. Dynamic Model Router & Local Ollama (2:15 - 2:45)
> *"Finally, let’s look at resilience. In Model Settings, our router exposes the live connectivity of Gemini, OpenRouter, and Ollama.
>
> Rather than a static toggle, our router uses task-based fallback chains. If I switch the QA task to Ollama, or if cloud API keys are disabled, the system seamlessly falls back to our local `llama3.2:3b` model running offline. The UI transparently updates the provider badge to inform the user that a fallback occurred."*

### 6. Closing (2:45 - 3:00)
> *"The repository includes a complete automated test suite with 27 passing tests, full Docker Compose deployment with PostgreSQL and pgvector, and an honest git commit history representing every phase. Thank you!"*
