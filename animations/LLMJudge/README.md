# LLM-as-a-Judge

A ~2m45s, no-voiceover Manim explainer on using an LLM to grade another LLM's
output as an observability signal — how you actually build one, and where the
technique itself falls short.

## What it teaches

1. **The observability gap** — latency, error rate and token counts all stay
   green even when the model's *answer* is flat-out wrong; nothing in standard
   observability catches that.
2. **The idea** — hand the input/output pair to a second LLM with a rubric; it
   returns a `{score, reasoning}` verdict. Plus the three ways to ask a judge:
   **direct score**, **pairwise** (A vs B), and **reference-based** (vs a gold
   answer).
3. **Anatomy of a judge** — the actual prompt, broken into its three working
   parts: the rubric (what a 5 vs a 1 means), the inputs (context / question /
   answer), and the demand for structured JSON output — then the verdict it
   returns.
4. **Custom evaluators** — real, idiomatic Anthropic Python SDK code: a reusable
   `judge()` function using `client.messages.parse(..., output_format=Verdict)`
   for a validated `{score, reasoning}`. Because the criterion is just an
   argument, you can define **any** criterion and run them as a suite
   (Groundedness / Tone / Policy → three independent scores).
5. **Judges in the stack** — the verdict is appended onto the request trace,
   turning "quality" into a graphed, thresholded, alertable metric; a bad model
   rollout shows up as a visible dip and pages someone.
6. **Blind spots** — **position bias shown live** (swap answer A and B → the
   verdict flips, because the judge tracks order not quality), plus verbosity
   bias, cost & latency, and self-preference. Closes on the discipline:
   calibrate against human labels, and treat the score as a signal, not ground
   truth.

The judge prompt and the Python evaluator are set in Menlo and syntax-coloured.
Nothing is a screenshot — the judge, the scale, the trace, the dashboard and the
bias demo are all Manim mobjects.

## Scenes

`animations/LLMJudge/llm_judge.py`, one film built from six sections:

- `Intro` — title card (a balance-scale motif)
- `Gap` (01) — the observability gap
- `Idea` (02) — the core idea + the three judging modes
- `Prompt` (03) — anatomy of a judge prompt → the verdict
- `Evaluators` (04) — custom evaluators in Anthropic SDK code + a criteria suite
- `Pipeline` (05) — traces gain a judge score; it becomes a dashboard metric
- `Limits` (06) — position bias (live) + other blind spots + calibration
- `Outro` — closing card

`LLMAsJudge` runs the whole film end-to-end.

## Rendering

```bash
./render.sh prompt --quick -q l    # fast layout check of one scene
./render.sh full                   # whole film, 480p (default)
./render.sh full -q h              # final HD (1080p60)
./render.sh --stitch -q m          # render each scene and ffmpeg-concat
```

Reuses the shared `HarnessEngineering/.venv` Manim environment — no local
install needed. Env knobs: `LLMJ_QUICK=1` (collapse holds for a fast test),
`LLMJ_DELAY=<seconds>` (override the reading-hold multiplier).

**Measured runtime:** 2:44 (164s) at the default pacing, 1080p60.
