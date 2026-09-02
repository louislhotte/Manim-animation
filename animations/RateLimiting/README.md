# Rate Limiting — a short, house-style explainer

A no-voice-over Manim film on **rate limiting**: why every serious backend needs
it, and how the classic algorithms actually work. It's built to be a little
*sensational* — it opens by melting a server under a flood — while still giving
your eyes time to read every beat.

## What it teaches

1. **The flood** — with no limits, one abusive client (or a traffic spike)
   buries a server: the load gauge redlines, it overheats, cracks and **crashes
   (503)** — taking every honest user down with it.
2. **The limiter** — put a gate in front. Requests under the limit pass (**200
   OK**); over the limit, a shutter drops and they **bounce (429)**. The server
   behind stays cool.
3. **The token bucket** — the popular algorithm, animated end-to-end: tokens
   drip into a bucket at a fixed rate; each request spends one; a **full bucket
   absorbs a burst**; an **empty bucket returns 429** until it refills. Refill
   rate = your steady limit; bucket size = the burst you tolerate.
4. **Four ways to count** — fixed window, sliding window, token bucket, leaky
   bucket, and the trade-off each one makes.
5. **In practice** — the **429** response (`Retry-After`, `X-RateLimit-*`
   headers), where limits live (per IP / per key / per endpoint, at the edge,
   shared in Redis), and *why* teams add them: abuse & DDoS, fairness, cost
   control (LLM/API spend), and stopping a cascading failure.

Bookended by the channel's intro card and the "Thank you for watching!" outro.

## Scenes

| Scene         | Class          | Beat                                             |
|---------------|----------------|--------------------------------------------------|
| `intro`       | `Intro`        | Title card                                       |
| `flood`       | `Flood`        | No limits → overload → 503 → collateral damage   |
| `limiter`     | `Limiter`      | A gate in front: 200 under, 429 over             |
| `bucket`      | `TokenBucket`  | The token-bucket algorithm, animated             |
| `algos`       | `Algorithms`   | Fixed / sliding window · token / leaky bucket    |
| `practice`    | `Practice`     | 429 headers, where limits live, why, takeaway    |
| `outro`       | `Outro`        | Thank-you card                                   |
| *(whole film)*| `RateLimiting` | intro → … → outro                                |

## Rendering

```bash
./render.sh flood --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                 # the whole film, 480p
./render.sh full -q h            # final HD (1080p60) — slow; run in background
./render.sh --stitch -q m        # render each scene and concat to one file (720p)
```

`render.sh` reuses an existing Manim venv elsewhere in the repo (Harness­Engineering /
Fourier / CNN) if present, otherwise bootstraps a local `.venv`. No LaTeX — every
label is Pango `Text`.

### Pacing knobs

Reading holds and animation speed are separate, so nothing feels rushed:

- `RL_DELAY` — the rhythm *between* animation steps (default `1.1`).
- `RL_READ` — the absolute hold after a subtitle lands (default `2.9 s`).
- `RL_QUICK=1` (or `--quick`) — collapse every hold for a fast iteration render.

## Notes on accuracy

- The **token bucket** is modelled faithfully: capacity `C = 8`, one token per
  request, bursts drain the bucket, an empty bucket yields 429, and the drip
  refill rate is what caps the long-run throughput.
- The `429 Too Many Requests` response and the `Retry-After` / `X-RateLimit-Limit`
  / `X-RateLimit-Remaining` / `X-RateLimit-Reset` headers are the real,
  widely-used convention.

Runtime (measured, 480p, default cadence): **3:27** (207.7 s, 214 animations) —
`media/videos/rate_limiting/480p15/RateLimiting.mp4`.
