# JWT Authentication — a ~4-minute explainer

How a **signed token** lets a server trust you *without remembering you*. A
no-voiceover, house-style Manim film on JSON Web Tokens: from the stateless-HTTP
problem, through the anatomy of a token and the signature that makes it
tamper-proof, to the full login → verify round trip and the trade-offs.

The base64 on screen is **real** — the token is signed with HS256 at import time,
so the tamper attack in scene 4 shows a genuine signature mismatch, not a mock-up.

## What it teaches

1. **HTTP has no memory** — every request stands alone; the classic fix
   (server-side sessions) puts all the state back on the server and turns the
   session store into the thing that has to scale.
2. **Don't remember — verify** — flip it: sign a tamper-proof token once and hand
   it to the client. The server keeps nothing but the secret used to check it.
3. **Anatomy of a token** — `header.payload.signature`, three Base64url parts.
   The header names the algorithm, the payload carries the claims, the signature
   proves integrity — and the twist: **the payload is only Base64, not
   encrypted**, so anyone can read it.
4. **The signature** — `HMAC-SHA256(header + "." + payload, secret)`. At login the
   server signs; on every request it recomputes and compares. Then the **tamper
   attack**, live: an attacker flips `"role": "user"` → `"admin"`, the recomputed
   signature no longer matches the one in the token → **REJECTED**. Forgery needs
   the secret, and the secret never leaves the server.
5. **The round trip** — a sequence diagram: `POST /login` → sign & return a JWT →
   `Authorization: Bearer …` on every request → verified locally, no DB. And why
   it scales: any server behind a load balancer can verify with the same secret —
   no shared session store to bottleneck.
6. **The catch** — the honest trade-offs: the payload is readable (keep secrets
   out), tokens are hard to revoke (expire fast, refresh), and the `alg:none`
   attack (always pin the algorithm you verify with).

Grounded in the standards: **JWT — RFC 7519**, **JWS (signatures) — RFC 7515**,
**HMAC — RFC 2104**.

## Scenes

`Intro · Problem · Idea · Anatomy · Sign · Flow · Catch · Recap · Outro`

Each renders alone; `JWTAuthFilm` is the whole thing end-to-end.

## Render

```bash
./render.sh anatomy --quick -q l   # fast layout check of one scene (480p15)
./render.sh                        # whole film, 480p
./render.sh full -q h              # final 1080p60 (slow; run in background)
./render.sh --stitch -q m          # render each scene and ffmpeg-concat
```

Everything uses `Text` (Pango), no LaTeX. `render.sh` reuses a sibling Manim venv
(HarnessEngineering / Fourier / CNN) if present.

Pacing knobs (tuned for readable, no-voiceover subtitles):
- `JWT_READ`  — absolute reading hold after each block of text (default **2.6 s**).
- `JWT_DELAY` — the small pauses *between* animation steps (default `1.0`).
- `JWT_QUICK=1` collapses every hold for fast iteration.

Every subtitle stays up long enough to read; animations are stretched 1.25× so
transitions aren't abrupt.

**Measured runtime:** 4:01 (240.7 s) at the default cadence. Verified with
`edgecheck.py` (no edge bleed on any scene — the one full-frame hit is the
deliberate red "REJECTED" flash) and by eyeballing key frames of every scene
(no overlaps, boxes fit, arrows clean).
