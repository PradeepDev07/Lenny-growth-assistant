# Manual Test Plan & Evaluator Verification Checklist

Use this structured test plan to verify the Lenny Growth Assistant end-to-end.

---

## Pre-flight Setup

1. **Backend**:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r backend/requirements.txt
   PYTHONPATH=. python -m ingestion.ingest --refresh
   uvicorn backend.app.main:app --port 8000
   ```
2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

---

## Verification Test Cases

### 1. Health & Configuration Transparency
- [ ] Navigate to `http://localhost:8000/health`.
- [ ] Confirm JSON response:
  ```json
  {
    "status": "healthy",
    "db": true,
    "ollama": false,
    "cloud_llm_configured": true,
    "version": "0.1.0"
  }
  ```
- [ ] Navigate to `http://localhost:8000/config` and verify task mappings and provider health pings.

---

### 2. Grounded Q&A with In-line Citations
- [ ] **Prompt**: `"How should we measure activation metrics in B2B PLG according to Elena Verna?"`
- [ ] **Verification**:
  - Response streams in real-time token by token.
  - Per-message provider badge displays active model (e.g. `[Gemini 2.0 Flash]`).
  - Answer cites `[Elena Verna on B2B Product-Led Growth]`.
  - Under the answer, click **"Sources Cited"**: verify episode link, guest name, and transcript excerpt.

---

### 3. Anti-Hallucination & Scope Boundary
- [ ] **Prompt**: `"What is the thermodynamic efficiency of a nuclear reactor?"`
- [ ] **Verification**:
  - Assistant responds with clear disclaimer:
    > *"I could not find information on this topic in the available Lenny's Podcast transcripts. Try asking about B2B PLG, activation metrics (Elena Verna), growth loops vs funnels (Brian Balfour), or PM metrics and the LNO framework (Shreyas Doshi)."*
  - Zero fabricated citations; zero hallucinations.

---

### 4. Ship 30 for 30 Content Generation
- [ ] On the Elena Verna activation answer, click **`[Turn into Ship 30/30 post]`**.
- [ ] **Verification**:
  - Generates an Atomic Essay (~800–1200 words).
  - Verifies the 5 rubric criteria:
    1. **Hook**: Provocative, counter-intuitive single-sentence opener.
    2. **1-3-1 Cadence**: Visual rhythm with varied paragraph lengths.
    3. **Narrative Arc**: Common Trap -> Framework Shift -> 3-Step Playbook -> Golden Rule.
    4. **Grounded Credits**: Direct attribution to the guest.
    5. **Markdown Subheads**: Bold, skimmable layout.

---

### 5. Interactive Artifact Generation & Sandboxed Iframe
- [ ] Click **`[Generate Interactive Artifact]`** on any answer or ask: `"Create an interactive SaaS CAC and LTV payback calculator."`
- [ ] **Verification**:
  - Right-hand **Artifact Viewer** opens automatically in a two-pane desktop split.
  - Interactive HTML preview renders inside `<iframe sandbox="allow-scripts">` without `allow-same-origin`.
  - Test sliders and input fields inside the calculator.
  - Switch tabs: **[Preview]** -> **[Code]** (syntax preview) -> **[Raw]**.
  - Test actions: **[Copy]** to clipboard and **[Download]** as `.html` file.

---

### 6. Model Router & Live Fallback Reconfiguration
- [ ] In the sidebar, click **`⚙ Model Settings`**.
- [ ] Review provider connectivity:
  - Gemini: Connected
  - OpenRouter: Connected
  - Ollama: Local status
- [ ] Change `retrieval_qa` model to `Ollama (llama3.2:3b)`.
- [ ] Click **`Save Changes`**.
- [ ] Send another question: verify that the message badge reflects the updated route or shows the fallback badge (`ⓘ Fallback used: Ollama`) if cloud key is disabled.

---

### 7. Session Persistence & History
- [ ] Create multiple chats using **`+ New Chat`**.
- [ ] Verify sessions group cleanly into **Today**, **Yesterday**, and **Previous 7 Days**.
- [ ] Switch between chats: confirm full conversation history and generated artifacts restore instantly.
- [ ] Delete a session: verify confirmation and clean removal.

---

### 8. Responsive & Mobile Layout
- [ ] Resize viewport to mobile width (<768px).
- [ ] Confirm sidebar collapses behind the hamburger menu.
- [ ] Confirm Artifact Viewer opens as a full-width overlay when triggered.
