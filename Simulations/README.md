# Simulations

Interactive, dynamics-driven simulations that don't fit Manim's scripted,
frame-by-frame model. These run their own physics/agent loop and visualise with
matplotlib (fast to iterate, easy to export to mp4).

| module | what it is |
|--------|------------|
| [`PredatorPrey/`](PredatorPrey/) | A school of fish evading a hunting shark; a testbed for growing *collective intelligence* with reinforcement learning (survivors = fitness). |

Each module has its own `render.sh` that bootstraps a local `.venv` (no shared
Manim environment needed).
