# Kubernetes & Continuous Delivery

A house-style explainer (~3.5 min) that builds the Kubernetes mental model one
layer at a time — **container → Pod → Node → Cluster** — then puts it to work in
a real CD pipeline (a Dockerfile and a GitHub Actions workflow, both on screen).

No voice-over: everything is on screen, and every hold is timed so you can read
it before it moves on. Uses `Text` (Pango) rather than `Tex`, so it renders with
no LaTeX toolchain. Code (the Dockerfile and the workflow YAML) is set in Menlo,
syntax-coloured, and highlighted line-by-line as it's explained. Nothing is a
screenshot — the whale, the pods, the nodes and the pipeline are all Manim
mobjects.

## The idea

Every term the brief asked for is defined on screen as its glyph appears:

```
        ┌──────────────── Cluster ────────────────┐
        │  ┌─── Node ───┐   ┌─── Node ───┐   ┌──────────────┐
        │  │ ⬡    ⬡     │   │ ⬡    ⬡     │   │ Control Plane │
        │  │ Pod  Pod   │   │ Pod  Pod   │   │ API·Sched·... │
        │  └────────────┘   └────────────┘   └──────────────┘
        └──────────────────────────────────────────────────┘
```

- **container** → your code + all its deps, sealed into one immutable, portable unit
- **Pod**       → the smallest thing K8s runs — usually a single container
- **Node**      → a worker machine (a VM or a physical box) that runs pods
- **Cluster**   → all your nodes, plus a **Control Plane** that decides what runs where
- **replicas**  → a **Deployment** keeps *N* identical pods alive (self-healing + scaling)
- **Service**   → one stable address that load-balances across the replicas

Colours are consistent throughout: Kubernetes **blue**, Docker blue for
containers, teal for nodes, blue for pods, purple for the control plane, orange
for the service, and GitHub purple for the CD pipeline.

## The film (`KubernetesCD`)

Bookended by the channel's intro card (a spinning ship's-helm / K8s wheel) and
the "Thanks for watching!" outro, six scenes in build-up order:

1. **Why Kubernetes?** — one app on one server can't handle a traffic spike and
   won't recover when it falls over. We want many identical copies, spread across
   machines, that heal and update themselves. *That's the road map.*
2. **Containers** — a real **Dockerfile** → `docker build` turns each instruction
   into a cached **layer** → an **image** → `docker run` starts a **container**
   (code + runtime + deps, sealed in). *Same box on your laptop and in the cloud.*
3. **The Cluster** — build the object model bottom-up: a container ⊂ a **Pod** ⊂ a
   **Node**; many nodes + a **Control Plane** = a **Cluster**. You declare desired
   state; the control plane schedules pods onto nodes.
4. **Replicas** — a **Deployment** (`replicas: 3`) keeps 3 pods alive. Kill one →
   K8s reschedules it (**self-healing**). Change one number → **scale** to 5. A
   **Service** gives them one address and spreads traffic across them.
5. **Continuous Delivery** — a real **GitHub Actions** workflow: on every push to
   `main`, checkout → `docker build` → push to registry → `kubectl set image`.
   The image is tagged with the commit SHA, and the cluster does a **rolling
   update** (v1 → v2, a few pods at a time) with zero downtime — roll back if it breaks.
6. **A Strong CD Needs…** — the checklist: immutable SHA-tagged images · automated
   tests as a gate · declarative manifests in Git (GitOps) · health probes
   (liveness/readiness) · rolling updates + fast rollback · config & secrets outside
   the image · observability on every release.

## Rendering

```bash
./render.sh containers --quick   # fast sanity check of one scene
./render.sh                      # the whole film, 480p
./render.sh full -q m            # final 720p render
./render.sh --stitch -q m        # render each scene and stitch into one film
```

Scenes: `intro · why · containers · cluster · replicas · pipeline · checklist · outro`
(or `full` for the whole thing). Quality: `-q l|m|h|k` (480p / 720p / 1080p / 2160p).

On first run `render.sh` reuses an existing Manim virtualenv from a neighbouring
series (`HarnessEngineering`, `Fourier` or `CNN`) if one is present, otherwise it
bootstraps a local `.venv` from `requirements.txt`.

### Env knobs

- `K8S_QUICK=1` — collapse every reading hold (and the end-holds) for a fast render
- `K8S_DELAY=1.2` — override the reading-hold multiplier (seconds per "beat")
