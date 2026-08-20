# Load Balancers — a short explainer

A ~3-minute, no-voice-over Manim film on what a load balancer is, what it does
under the hood, and why it is non-negotiable for scaling and staying up in
production. Replicas are assumed known (see the Kubernetes film) — this picks up
the question *"once there are many identical servers, who do clients talk to?"*

Everything is drawn with Manim `Text` (Pango), never `Tex`, so there is **no
LaTeX toolchain**. Nothing is a screenshot: the clients, the balancer, the
servers, the requests and the `nginx.conf` panel are all mobjects.

## What it teaches

1. **Why we need one** — one server overloads and is a single point of failure;
   replicas fix capacity, but now there are many addresses to reach.
2. **One front door** — the balancer exposes a single stable address (a VIP) in
   front of a pool of identical replicas and spreads requests across them.
3. **Choosing a server** — the algorithms: round-robin, least-connections,
   weighted, and sticky sessions (session affinity).
4. **Health checks & failover** — the balancer probes each server (`/healthz`),
   pulls a sick one out of rotation, reroutes traffic, and lets it rejoin when it
   self-heals. No single server is a single point of failure.
5. **L4, L7 & the edge** — L4 forwards TCP/UDP by IP+port; L7 reads HTTP and
   routes by path/host; TLS terminates at the edge — shown against a real nginx
   `upstream` config.
6. **Why it's paramount** — scale out live with zero downtime; the checklist of
   what a load balancer buys you, and the one-line takeaway.

Bookended by the channel intro card and the "Thanks for watching!" outro.

## Scenes

| CLI name  | Class          | Beat                                  |
|-----------|----------------|---------------------------------------|
| `intro`   | `Intro`        | Title card                            |
| `why`     | `Why`          | Overload + single point of failure    |
| `what`    | `Frontdoor`    | One address, a pool behind            |
| `choose`  | `Choosing`     | Round-robin / least-conn / weighted / sticky |
| `health`  | `Health`       | Health checks & failover              |
| `layers`  | `Layers`       | L4 vs L7 + TLS termination            |
| `scale`   | `Scale`        | Scale-out + checklist + takeaway      |
| `outro`   | `Outro`        | Thanks-for-watching card              |
| `full`    | `LoadBalancer` | The whole film, intro → outro         |

## Rendering

```bash
./render.sh what --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                # the whole film, 480p (default)
./render.sh full -q h           # final 1080p60 (slow)
./render.sh --stitch -q m       # render each scene and ffmpeg-concat to one file
```

`render.sh` reuses an existing Manim venv (`HarnessEngineering`, `Gravity`,
`Fourier` or `CNN`) if present, otherwise bootstraps a local `.venv`.

### Pacing knobs

| Env var        | Default | Effect                                        |
|----------------|---------|-----------------------------------------------|
| `LB_QUICK=1`   | off     | collapse every reading hold for a fast render |
| `LB_DELAY`     | `1.5`   | seconds-per-beat reading rhythm               |
| `LB_ANIM_SLOW` | `1.15`  | stretch every animation's run-time            |
| `LB_END_HOLD`  | `1.8`   | hold at the end of each scene before the wipe |

## Measured runtime

**~3m00s** at the default pacing (183 s at 480p15, 180 s at 1080p60). `edgecheck.py`
is clean on every scene and on the full film at both resolutions (no content
within 9 px of an edge). Final deliverable rendered at **1080p60**:
`media/videos/load_balancer/1080p60/LoadBalancer.mp4`.
