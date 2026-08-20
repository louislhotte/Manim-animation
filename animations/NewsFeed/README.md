# Designing the News Feed — Push, Pull & the Celebrity Problem

A ~3-minute, no-voiceover Manim explainer on how a social-media home feed is
actually built at scale — and the one design decision that makes or breaks it:
**fan-out**. Everything on screen is a Manim mobject (phones, avatars, databases,
the Redis cache, the Kafka log, the API gateway, the CDN), drawn as clean,
high-level service icons.

## What it teaches

Every service is drawn from a small, consistent **SVG icon design system**
(Lucide-style line-art on a 24 px grid, uniform stroke) in `assets/icons/`, loaded
via `SVGMobject` and recoloured per node — so the diagram reads like a real
architecture whiteboard rather than a pile of ad-hoc shapes.

The central tension the film makes concrete:

> An average user has ~**200** followers — posting delivers to 200 feeds.
> A celebrity has **100,000,000** followers — the *same* code path would deliver
> to a hundred million feeds. One design cannot naively do both.

The answer is a **hybrid push / pull fan-out** built around Redis.

### The corrected, production-level design

The naive design ("copy every post into every follower's feed") is **pure
fan-out on write**. It's perfect for normal users and catastrophic for
celebrities. The production system uses *both* strategies and picks per author:

| | **Push** — fan-out on *write* | **Pull** — fan-out on *read* |
|---|---|---|
| When | normal authors (`followers < LIMIT`) | celebrities / power users |
| On post | copy post-id into every follower's Redis feed list | do nothing (keep it in a hot cache) |
| On read | read your prebuilt feed — **O(1)** | gather the author's recent posts and merge |
| Write cost | O(followers) | O(1) |
| Read cost | O(1) | O(followees you pull) |
| Failure it avoids | slow reads | the **write storm** (100 M writes / post) |

**The read path merges the two:** your timeline = *(your pushed Redis feed)* ⊕
*(a pull of recent posts from the few celebrities you follow)* → **rank** →
hydrate → return. Writes stay bounded (no 100 M-write storms); reads stay bounded
(you only follow a handful of celebrities).

### Production components (each gets an icon in the film)

- **Client** (mobile) → **API Gateway + Load Balancer** (auth, rate-limit, TLS)
- **Post / Write Service** → persists to the **Post DB** (sharded source of
  truth) and writes media to **Object Storage** (served via **CDN**)
- **Kafka** decouples the write from the fan-out (a durable log, back-pressure)
- **Fan-out Workers** consume post events, read the **Social Graph DB**, and — per
  the push/pull decision — write into **Redis** feed lists
- **Redis Feed Cache** — one precomputed home-timeline list per user
- **Timeline / Read Service** — reads Redis, pulls celebrity posts, merges, ranks
  and hydrates the feed for the client

## Scenes

1. **Your Feed** — how a user interacts: open the app, the feed is instantly
   there, you scroll & like; it's the latest posts from who you follow.
2. **Fan-out on Write · Push** — Alice (200 followers) posts; the post is copied
   into every follower's Redis feed list; reads are O(1).
3. **The Celebrity Problem** — the same push at 100 M followers: a write storm,
   the queue backs up, shards go hot, feeds lag for minutes.
4. **Push for the Many, Pull for the Few** — the fan-out worker's push/pull
   decision, then the read-time **merge + rank** into your timeline.
5. **The Production Architecture** — the full system with every service icon; a
   write flows through (blue), then a read flows through (green).
6. **The Takeaway** — push for the many, pull for the few; Redis holds every
   feed; merge then rank.

Plus the house intro/outro cards.

## Rendering

```bash
./render.sh push --quick -q l     # fast layout check of one scene (480p15)
./render.sh full                  # whole film, 480p
./render.sh full -q m             # 720p30
./render.sh full -q h             # final 1080p60 (slow; run in background)
./render.sh --stitch -q m         # render each scene and ffmpeg-concat
```

Scenes: `intro feed push celebrity hybrid architecture recap outro` (and `full`).

Env knobs:

- `NF_QUICK=1` (or `--quick`) collapses every reading hold for a fast render.
- `NF_DELAY=1.2` overrides the reading-hold multiplier (seconds per "beat").

Text is Pango `Text` rendered large and scaled down (crisp spacing); no LaTeX.
The one code snippet (`fanout_worker.py`) is set in Menlo.

## Measured runtime

- Full film, real pacing (720p30): **3:11** (192 s, 158 animations), measured
  with `ffprobe -show_entries format=duration`.
