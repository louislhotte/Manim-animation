# Harness Engineering

A ~6-minute, house-style explainer on **harness engineering** — engineering the
*whole system around* a language model, not just the model itself. Boxes,
arrows and small graphs; no equations, so it renders without LaTeX.

![nested layers: Prompt ⊂ Context ⊂ Harness](media/preview.png)

## The film (`HarnessEngineering`)

Bookended by the channel's intro card and the "Thank you for watching!" outro,
six roughly one-minute scenes:

1. **What is Harness Engineering** — the naïve `prompt → model → output` picture
   gives way to the nested one: **Prompt ⊂ Context ⊂ Harness** around the model.
2. **Prompt Engineering** — what you *say*: role, instructions, format, few-shot;
   a vague-vs-structured comparison; where prompting alone hits a ceiling.
3. **Context Engineering** — what the model *sees*: the context window as a token
   **budget**, fed by the system prompt, RAG, tools, memory and examples;
   relevance beats volume.
4. **Harness Engineering** — the system it *runs in*: the **agent loop**
   (decide → act → observe), orchestration, tools, verification, memory,
   sub-agents, guardrails, and a self-correcting retry.
5. **Harness Pipeline Example** — a coding agent: `Task → Plan → Gather context →
   Act → Verify → Reflect → Done`, with a task token that fails the tests, loops
   back, and passes on attempt 2.
6. **Why it matters** — reliability climbs Prompt → Context → Harness (same
   model), the benefits, and the punchline: *the moat isn't the model, it's the
   harness around it.*

## Rendering

```bash
./render.sh what --quick      # fast sanity check of one scene
./render.sh                   # the whole film, 480p
./render.sh full -q h         # final 1080p
./render.sh --stitch -q m     # render each scene and join into one 720p film
```

`render.sh` reuses the CNN or Fourier series' `.venv` if it finds one (so Manim
isn't reinstalled), otherwise it bootstraps a local `.venv` from
`requirements.txt`.

Individually renderable scenes: `intro` · `what` · `prompt` · `context` ·
`harness` · `pipeline` · `why` · `outro` (or `full`, the default).

`HARNESS_QUICK=1` (or `--quick`) shortens the on-screen holds while iterating.
Tunables (palette, timings) live at the top of `harness_engineering.py`.
