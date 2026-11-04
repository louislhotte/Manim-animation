# What is Next.js?

A ~3:42 no-voiceover Manim explainer answering two questions: **what is
Next.js**, and **how does it give a React app a real backend**. The through
line: a classic React SPA ships an empty div and needs a second application
for its data; Next.js folds that second application into the framework.

## Real data, not mockups

Every terminal panel in the film shows **real captured output** baked by
`generate_assets.py` from a genuine, minimal Next.js 16.4.3 app (`demo/`,
backed by `node:sqlite`) that was actually npm-installed, built, and served:

- `assets/spa.json` — the built `dist/index.html` of a real Vite 8.3.5 React
  SPA (the famous "one empty div" a SPA server sends).
- `assets/next.json` —
  - `curl -s localhost:3000/books`: server-rendered HTML with the five books
    already in it, plus a per-request timestamp; captured **twice**, and the
    two differing timestamps on screen are the proof of per-request SSR;
  - `curl -i localhost:3000/api/books`: `HTTP/1.1 200 OK`,
    `content-type: application/json`, rows straight from SQLite;
  - the verbatim `next build` route table with its `○ (Static)` /
    `ƒ (Dynamic)` legend.

`generate_assets.py` copies `demo/` to a temp dir (never installs
`node_modules` into the synced repo), seeds SQLite, builds, serves, captures,
and asserts the content (5 books, 1975 first, two distinct timestamps).
Network-dependent; run manually, not at render time.

## Scenes (`render.sh` name → class)

1. `intro` → `Intro` — house title card.
2. `problem` → `Problem` — React alone stops at the browser: the real Vite
   `index.html` (one empty div), the download → run → fetch → paint wait, and
   the separate Express backend you still have to build.
3. `definition` → `Definition` — what Next.js is, and file-system routing:
   the project tree maps onto `/`, `/books`, `/api/books`; `lib/db.js` has no
   URL and stays server-only.
4. `server` → `ServerComponents` — `app/books/page.jsx` queries SQLite
   directly inside the component; the real curl'd HTML with the data already
   in it; the timestamp changes between two requests.
5. `api` → `ApiRoutes` — `app/api/books/route.js` becomes an HTTP endpoint;
   real `curl -i` response; pages, mobile apps, and other services call it.
6. `modes` → `RenderModes` — the real `next build` table: static vs dynamic
   vs revalidate, chosen route by route.
7. `fullstack` → `FullStack` — one picture: browser → middleware → Server
   Components / Route Handlers → SQLite; one repo, one build, one deploy;
   Server Actions get a mention.
8. `outro` → `Outro` — thank-you card.

Full film: `WhatIsNextJS` (**3:42 measured** on the 1080p60 deliverable,
3:44 at 480p15 wait-rounding).

## Rendering

```bash
./render.sh server --quick -q l   # fast layout check of one scene
./render.sh full                  # whole film, 480p
NX_MEDIA_DIR=/tmp/nx_media ./render.sh full -q h   # final 1080p60 (local dir, then copy back)
```

Reuses the HarnessEngineering/Fourier/CNN venv if present. Pacing knobs:
`NX_QUICK=1`, `NX_DELAY` (default 1.0), `NX_READ` (default 2.35).
