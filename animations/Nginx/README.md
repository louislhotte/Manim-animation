# nginx — a short, house-style explainer

A no-voiceover Manim film on **what nginx actually is and why it's fast**. It
frames nginx as one process wearing three coats — web server, reverse proxy,
load balancer — and shows the event-driven architecture that let it beat the
C10K problem.

**Measured runtime: ~3:10** (190 s, 480p15, real reading cadence — not `--quick`).

## What it teaches

- **Reverse proxy** — nginx sits at the edge; every request hits it first. The
  client thinks it's talking to your site; it's talking to nginx.
- **The event loop (why it's fast)** — the old model gives every connection its
  own thread and blocks on I/O, so 10,000 connections means 10,000 stacks and the
  machine runs out of RAM. nginx instead runs a handful of worker processes, each
  a single non-blocking **event loop** that only touches sockets when they're
  ready. That is the C10K solution.
- **Load balancing** — a pool of identical backends behind one address; requests
  spread round-robin (or `least_conn`); a dead backend is skipped automatically.
  Backed by the **real `nginx.conf`**: an `upstream` block + `proxy_pass`.
- **At the edge** — TLS termination, static files, response caching, and gzip all
  happen at nginx; static/cached responses never touch your app, only dynamic
  ones get proxied on.

## Scenes

| # | Scene       | Class       | Beat |
|---|-------------|-------------|------|
| — | Intro       | `Intro`     | Title card |
| 1 | Front door  | `FrontDoor` | client → nginx → app; what a reverse proxy is |
| 2 | Why it's fast | `EventLoop` | thread-per-connection vs. one non-blocking loop (C10K) |
| 3 | Load balancing | `Balance` | upstream pool, round-robin, reroute-on-failure, real `nginx.conf` |
| 4 | More than a proxy | `Edge` | TLS · static · cache · gzip; static served at the edge, dynamic proxied |
| — | Outro       | `Outro`     | Thanks card |

The whole film is the `HowNginxWorks` class.

## Render

```bash
./render.sh balance --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                   # whole film, 480p (default)
./render.sh full -q h              # final HD (1080p60) — slow; run in background
./render.sh --stitch -q m          # render each scene and ffmpeg-concat to one file
```

Quality: `-q l|m|h|k` = 480p15 / 720p30 / 1080p60 / 2160p60. Scene names:
`intro`, `frontdoor`, `eventloop`, `balance`, `edge`, `outro`, `full`.

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering /
Fourier / CNN) if present, else bootstraps a local `.venv` — so Manim isn't
reinstalled. Pacing knobs: `NGINX_QUICK=1` collapses every hold; `NGINX_DELAY` /
`NGINX_READ` tune the reading rhythm.

## Notes

- Pure Manim `Text` (Pango) — **no LaTeX**. The `nginx.conf` panel is set in Menlo
  with hand-rolled syntax colouring.
- Everything is hand-drawn vector mobjects (no image assets): the nginx card and
  N-in-a-ring emblem, browser/client, backend servers, the event-loop ring, and
  the RAM meters.
