# What is an ALB?

A no-voiceover Manim explainer on the **AWS Application Load Balancer**: one
managed, Layer 7 front door that receives every HTTP(S) request for your app
and forwards each one to a healthy server behind it.

## What it teaches

1. **The front door** — many identical servers, one DNS name
   (`shop-alb-8f3d21a7.eu-west-1.elb.amazonaws.com`); the ALB accepts every
   request and forwards each one to a healthy target.
2. **Anatomy** — the chain inside every ALB: **listener** (port + protocol)
   → **rules** (checked in priority order) → **target group** (a named pool)
   → **target** (EC2 instance, container, private IP, or Lambda). Closes on
   the real `aws elbv2 create-rule` CLI call that wires the `/api/*` rule.
3. **Routing by content** — the Layer 7 superpower, live: `/api/orders`
   matches the path rule and lands on `api-tg`; `Host: admin.shop.com`
   matches the host rule; `/checkout` falls through to the default rule.
   Three services behind one balancer, one DNS name, one certificate.
4. **Health checks** — `GET /health` every 30 s expecting an HTTP 200; the
   real target-group defaults (interval 30 s, timeout 5 s, unhealthy after
   2 fails, healthy after 5 passes); a failing target is routed around and
   rejoins automatically.
5. **Layer 7 vs Layer 4** — a request as a sealed letter: the NLB reads only
   the address (IP : port); the ALB opens it and reads the HTTP inside.
   Side-by-side: what each balancer gives you and when to pick which.
6. **Zones and scale** — one ALB node per availability zone (at least two),
   the DNS name resolves to all of them, cross-zone routing, Auto Scaling
   targets register themselves, and the ALB scales itself: you never resize
   it. Recap chain: DNS name → listener → rule → target group → healthy target.

Facts shown on screen are the real ones: the `aws elbv2` CLI syntax, the ALB
DNS-name format, and the target-group health-check defaults from the AWS docs.

## Scenes

| scene (render.sh) | class       | beat                                  |
| ----------------- | ----------- | ------------------------------------- |
| `intro`           | `Intro`     | title card                            |
| `frontdoor`       | `FrontDoor` | one address, many servers             |
| `anatomy`         | `Anatomy`   | listener → rules → target groups      |
| `routing`         | `Routing`   | content-based routing, three requests |
| `health`          | `Health`    | health checks, fail + rejoin          |
| `layers`          | `Layers`    | ALB (L7) vs NLB (L4)                  |
| `scale`           | `Scale`     | zones, auto-registration, recap chain |
| `outro`           | `Outro`     | thank-you card                        |
| `full`            | `WhatIsAnALB` | the whole film                      |

## Render

```bash
./render.sh routing --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                   # whole film, 480p
./render.sh --stitch -q h          # final HD: render each scene and concat
```

For the final `-q h` render, point `ALB_MEDIA_DIR` at a local path (e.g.
`/tmp/alb_media`) so Manim does not write thousands of frames into the
OneDrive-synced repo, then copy the finished mp4 back.

Measured runtime of the 1080p60 deliverable: **4:46** (286.2 s), default cadence
(`media/WhatIsAnALB_1080p60.mp4`).

Pacing knobs: `ALB_QUICK=1` (collapse holds), `ALB_DELAY` (beat multiplier),
`ALB_READ` (seconds of reading time per caption).
