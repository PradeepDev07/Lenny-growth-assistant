# Design Specification & UI/UX Guidelines: Lenny Growth Assistant

This document details the interface architecture, visual design system, interaction states, responsive layouts, and accessibility patterns implemented in the Lenny Growth Assistant.

---

## 1. UI/UX Principles

1. **Grounded Transparency Over Blind Confidence**:
   - Every answer displays which model served it (`[Gemini 2.0 Flash]`, `[Ollama llama3.1]`).
   - If the router had to fall back, the user is visibly notified via an inline notice (`ⓘ Fallback used: Ollama`).
   - Sources are explicitly cited inline and expandable in structured citation cards.
2. **Claude Artifacts Split Paradigm**:
   - Chat remains conversational on the left, while interactive calculators, diagrams, and atomic essays expand into an isolated right-hand panel.
3. **Frictionless Action Triggers**:
   - High-value transformations like turning answers into **Ship 30 for 30 essays** or **interactive calculators** are one-click button actions inside message cards.

---

## 2. Information Architecture (IA)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header: Session Title  ·  Model Indicator [Gemini 2.0 Flash ● Live]  ·  Menu│
├──────────────┬──────────────────────────────────┬───────────────────────────┤
│ SIDEBAR      │ CHAT PANEL                       │ ARTIFACT VIEWER           │
│              │                                  │                           │
│ + New Chat   │ User Message                     │ Tabs: [Preview] [Code][MD]│
│              │ Assistant Message                │                           │
│ Today        │  ├── Provider Badge              │ Sandboxed Interactive     │
│  - Miro PLG  │  ├── Grounded Answer             │ iframe / Code Viewer      │
│              │  ├── Sources Cited               │                           │
│ Yesterday    │  └── [Ship 30] [Artifact] CTAs   │ Actions:                  │
│  - Retention │                                  │ [Download] [Copy] [Open]  │
│              │ Message Input + Prompt Chips     │                           │
│ ⚙ Settings   │                                  │                           │
└──────────────┴──────────────────────────────────┴───────────────────────────┘
     20%                       40%                            40%
```

---

## 3. Interaction States

| State | UI Behavior | Visual Indicator |
|---|---|---|
| **Empty Chat** | Centered prompt suggestions for common Lenny topics. | Helpful prompt chips and welcome message. |
| **Retrieving Chunks** | Initial query submission before first token arrives. | Pulsing Sparkles icon + "Retrieving grounded transcripts...". |
| **Streaming Answer** | Tokens fill incrementally via Server-Sent Events. | Streaming text cursor; sources card renders when stream completes. |
| **Ungrounded Query** | User asks out-of-scope question. | Clean, polite disclaimer without fabricated citations. |
| **Fallback Invoked** | Cloud provider quota/error triggered Ollama. | Amber badge: `ⓘ Fallback used: Ollama`. |
| **Artifact Open** | Two-pane split active. | Split screen desktop view; full-width modal on mobile. |

---

## 4. Responsive & Mobile Viewport Rules

- **Desktop (≥ 1024px)**:
  - 3-column layout: 20% Sidebar, 40% Chat thread, 40% Artifact Viewer.
- **Tablet (768px – 1023px)**:
  - 2-column layout: Collapsible sidebar, 50% Chat thread, 50% Artifact Viewer.
- **Mobile (< 768px)**:
  - 1-column layout: Sidebar moves behind a hamburger drawer.
  - Artifact Viewer opens as an interactive full-screen sheet with top close button.

---

## 5. Accessibility & Design System

- **Color Palette**: Dark-mode primary theme (`#0d0f12` background, `#181a20` surface, `#6366f1` indigo primary, `#10b981` emerald status, `#f59e0b` amber fallback).
- **Keyboard Navigation**:
  - `Enter` submits prompt; `Shift + Enter` inserts a newline.
  - Tab focus rings on all buttons and selectable source cards.
- **ARIA & Screen Readers**:
  - Modals have `aria-label` and `role="dialog"`.
  - Sandboxed iframe uses explicit `title` attribute for assistive technologies.
