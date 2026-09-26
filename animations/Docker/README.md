# Docker, Visually

A no-voiceover, house-style Manim explainer that answers "what is a container,
really?" by drawing containers as what they literally are: **boxes**. The hero
scenes are genuine 3D, with the camera slowly orbiting translucent neon "crates"
standing on a shared host slab, so you see a container as a solid object from
every angle. The command and Dockerfile scenes are deliberately flat and static
(a top-down 2D view), because there is nothing 3D to reveal there. The film ends
by handing the fleet off to Kubernetes, echoing the sibling `Kubernetes`
explainer's visual language.

## What it teaches

- **The problem.** The same code runs on your laptop and crashes on the server,
  because the environments differ. "It works on my machine."
- **The container.** One sealed box holds your app plus its libraries and
  runtime. It shares the host operating system kernel, so it stays small and
  starts fast, and the box is identical on every machine.
- **Images & layers.** A Dockerfile builds an image as a stack of read-only,
  cached layers. Running it adds a thin writable layer on top: that is a
  container. Many containers can share the same image layers.
- **The main commands.** `docker build` makes an image, `docker run` starts a
  container, `docker ps` lists them, `docker stop`/`rm` clean up, and
  `docker push`/`pull` share images through a registry like Docker Hub.
- **How containers interact.** Isolated containers talk over a Docker network
  (bridge); a volume gives the database storage that outlives the container;
  `docker-compose.yml` wires a web/api/db app together.
- **Why so light.** A virtual machine ships a full guest OS per app (gigabytes,
  minutes to boot). Containers share the host kernel through the Docker engine,
  so they are megabytes and start in milliseconds.
- **Scaling up (the Kubernetes link).** One machine runs a handful of
  containers; Kubernetes schedules, heals, and scales thousands across a cluster
  of machines. Continue with the `Kubernetes` explainer.

## Scenes

| # | Scene       | Camera        | What it shows                                             |
|---|-------------|---------------|----------------------------------------------------------|
| — | `intro`     | flat card     | Title card, Docker whale motif.                          |
| 1 | `problem`   | flat 2D       | "It works on my machine": two mismatched environments.   |
| 2 | `container` | **3D orbit**  | One 3D crate on the host slab: app + libs + runtime.     |
| 3 | `layers`    | **3D orbit**  | Image as stacked read-only layers + writable top.        |
| 4 | `commands`  | flat 2D       | Dockerfile + the build/run/ps/stop/pull/push lifecycle.  |
| 5 | `network`   | **3D orbit**  | web/api/db crates talking over a Docker network + volume.|
| 6 | `vms`       | **3D orbit**  | VM stack (tall) vs container stack (short).              |
| 7 | `kube`      | 3D → flat     | Crowded host → the Kubernetes cluster handoff.           |
| — | `outro`     | **3D orbit**  | Thank-you over a gently orbiting row of crates.          |

The camera only moves for the genuinely-3D scenes (per the house rule: camera
control is reserved for real 3D geometry, never for flat text or diagrams).

## Rendering

```bash
./render.sh container --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                     # whole film, 480p15
./render.sh full -q h                # final 1080p60 (slow; run in background)
./render.sh --stitch -q m            # render each scene and concat (720p30)
```

Scene names: `intro problem container layers commands network vms kube outro`
(plus `full`). `render.sh` reuses an existing repo Manim venv
(HarnessEngineering / Fourier / CNN) if present, else bootstraps a local
`.venv`. It renders into `/private/tmp/dk-media` by default (writing Manim's many
partial-movie files into the OneDrive-synced repo stalls on I/O); override with
`DK_MEDIA_DIR=…`.

Pacing knobs: `DK_QUICK=1` collapses every reading hold for a fast iteration;
`DK_DELAY=<seconds>` overrides the reading-rhythm multiplier (default 2.3).

## Runtime

Measured full-film duration: **4:33 (272.9 s)**, rendered at 1080p60
(`DockerVisually_1080p60.mp4`, ~23 MB). The four orbiting 3D scenes keep prism
counts low, so the whole HD film renders in ~5 minutes.

Built on the `Quantization` 3D `ThreeDScene` base (orbiting camera + fixed-in-
frame HUD) and the `Kubernetes` explainer's 2D glyphs (`pod_hex`, `node_box`,
`control_plane`, `code_panel`, the Docker whale), so the Kubernetes handoff at
the end shares that film's visual language. Everything is `Text` (Pango), no
LaTeX; code is set in Menlo and syntax-coloured.
