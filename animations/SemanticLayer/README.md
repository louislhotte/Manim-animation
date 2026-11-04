# Semantic Layers

A short (~2-minute) house-style explainer answering three questions: **what is
a semantic layer, where does it sit in the data model, and what is it actually
used for?**

No voice-over: everything is on screen, timed so you can read it before it
moves on. Uses `Text` (Pango) rather than `Tex`, so it renders with no LaTeX
toolchain. Nothing is a screenshot — the warehouse, the stack, the tool icons
and the metric card are all Manim mobjects.

## The idea

```
        ┌──────────── Consumption ────────────┐   ┐
        │   BI     ML     Apps     SQL         │   │ Business /
        └───────────────┬──────────────────────┘   │ logical model
                         │
        ┌──────── Semantic Layer ──────────────┐   │
        │  metrics · dimensions · business logic│   ┘
        └───────────────┬──────────────────────┘
                         │
        ┌──────── Warehouse / Lake ────────────┐   ┐
        └───────────────┬──────────────────────┘   │ Physical model
        ┌──────── Sources (DBs, events, APIs) ──┐   ┘
        └───────────────────────────────────────┘
```

- **The problem** — without a shared layer, every tool (BI, notebook,
  spreadsheet) queries the warehouse directly and invents its own definition
  of "Revenue." Three tools, three different numbers — and no one is
  technically wrong.
- **Where it lives** — the semantic layer sits between raw **storage**
  (warehouse/lake) and every **consumption** tool. It's the seam between the
  *physical* data model (how things are stored) and the *business* model
  (how everyone talks about the data).
- **What it is** — raw, physical columns (`orders.amount`, `orders.status`, …)
  are mapped onto named, governed business concepts — metrics, dimensions,
  hierarchies — defined once (e.g. `Revenue = SUM(orders.amount) WHERE
  orders.status = 'completed'`).
- **What it's used for** — every tool now asks the semantic layer the same
  question and gets the same answer: consistency, governance, self-service,
  trust. This is what tools like **dbt's Semantic Layer**, **LookML**,
  **Cube** and **AtScale** actually do.

## The film (`SemanticLayers`)

Bookended by the channel's intro card (a stack-of-layers glyph) and the
"Thanks for watching!" outro, four scenes:

1. **Without A Semantic Layer** — the problem: direct, ungoverned access →
   inconsistent metrics.
2. **Where It Lives In The Stack** — Sources → Storage → **Semantic Layer** →
   Consumption, plus the physical-vs-business-model brace.
3. **What It Actually Is** — physical columns mapped to business concepts;
   one metric, defined once.
4. **What It's Used For** — the same definition, fanned out to every tool;
   the consistency/governance/self-service/trust payoff; real-world tools.

## Rendering

```bash
./render.sh problem --quick    # fast sanity check of one scene
./render.sh                    # the whole film, 480p
./render.sh full -q h          # final 1080p render
./render.sh --stitch -q m      # render each scene and stitch into one film
```

Scenes: `intro · problem · stack · whatisit · usedfor · outro` (or `full` for
the whole thing). Quality: `-q l|m|h|k` (480p / 720p / 1080p / 2160p).

On first run `render.sh` reuses an existing Manim virtualenv from a
neighbouring series (`HarnessEngineering`, `Fourier` or `CNN`) if one is
present, otherwise it bootstraps a local `.venv` from `requirements.txt`.

### Env knobs

- `SEM_QUICK=1` — collapse every reading hold (and the end-holds) for a fast render
- `SEM_DELAY=1.2` — override the reading-hold multiplier (seconds per "beat")

### Measured runtime

`SemanticLayers.mp4` at 480p, real pacing (no `--quick`): **~2:07** (126.5s).
