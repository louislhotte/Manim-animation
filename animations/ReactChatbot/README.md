# React.js & a Chatbot System Design

A **~3-minute** explainer in two halves. First, what **React.js** actually is —
past the one-liner "it's for frontends" — and then a concrete **system design**:
a document-aware chatbot, drawn front to back.

Rendered with [Manim](https://www.manim.community/). Everything uses `Text`
(Pango), never `Tex`, so **no LaTeX toolchain is required**.

## The story

**Part A — what React is**

1. **What is React?** — a JavaScript *library* for building user interfaces:
   **declarative** (you describe the UI for a given state) and **component-based**
   (build the screen from small, reusable pieces). Open-sourced by Meta in 2013.
2. **Components** — the UI is one **tree** of components (`<App>` → `<ChatWindow>`
   → `<MessageList>` → `<Message/>`). Props flow **down**, events bubble **up**,
   and the same `<Message/>` is reused for every line.
3. **How React updates the screen** — the deeper bit. Change **state** →
   React **re-renders** to a new **Virtual DOM** → **diffs** it against the
   previous tree (**reconciliation**) → applies the **minimal** real-DOM patch.
   Only what changed is touched. Plus the hooks you actually use: `useState`,
   `useEffect`.
4. **What it's used for** — SPAs, dashboards, realtime/chat UIs, design systems;
   and the ecosystem around it (Next.js, React Native, npm).

**Part B — a chatbot, front to back**

5. **Architecture** — the whole system as a **two-swimlane** diagram with clean
   right-angle, arrowed connectors:
   - an **Online · chat** lane: **User → Frontend (React.js) → Backend API
     (FastAPI/Python) → LLM**
   - an **Offline · ingestion** lane: **Data service (Python) → Celery workers →
     Docling (OCR)**
   - a **shared storage band** between them — **Observability** (traces · tokens ·
     cost), **Vector store** (chunks + embeddings), **Database — Postgres**
     (sessions & messages)
   - the two lanes **meet only at the vector store** (the API reads it for
     retrieval; Docling writes embeddings into it) — the key decoupling insight.
6. **The two flows** — the same diagram, brought to life along two planes:
   - **① Ingestion (offline, async):** upload a PDF → data-service enqueues
     **Celery** tasks → a worker runs **Docling** OCR → chunk · embed · index into
     the vector store. Heavy work runs in the background so the chat stays fast.
   - **② Chat (online, streaming):** you ask → **retrieve** relevant chunks
     (RAG) → prompt + context → **LLM** → **stream** tokens back to the browser →
     **persist** the session → **observe** cost & latency.

## Why this shape

The point of the design scene is *separation of concerns*: the **streaming path**
(must feel instant) is decoupled from **heavy ingestion** (OCR, embedding) via a
**Celery** queue, while **observability** and the **database** cut across both.
React is simply the frontend that consumes the stream.

## Render

```bash
./render.sh                    # whole film, 480p (fast)
./render.sh reconcile --quick  # one scene, holds collapsed — quick sanity check
./render.sh full -q h          # final 1080p60 render
./render.sh --stitch -q m      # render each scene and stitch (720p)
```

`render.sh` bootstraps a local `.venv` on first run, or reuses the
HarnessEngineering / Fourier / CNN venv if one already exists.

Scenes render individually too: `intro · whatis · components · reconcile ·
usedfor · architecture · flows · outro`.

## Knobs

- **`RC_QUICK=1`** (or `--quick`) — collapse every reading hold *and* the fixed
  end-of-scene holds, for fast iteration.
- Pacing lives in one constant, `DELAY`, at the top of `react_chatbot.py`
  (with `ANIM_SLOW` for play speed and `SCENE_GAP` for the end-of-scene hold).
