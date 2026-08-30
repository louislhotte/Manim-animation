# Precision, Recall & F1 — a short explainer

A self-explanatory (no voice-over) Manim film that builds the **confusion
matrix** from a concrete example, defines **precision**, **recall** and **F1**,
and — the point of the piece — shows **when to maximise each**.

Running example: 20 items, 8 truly relevant; the model flags 10 of them, giving
**TP = 6, FP = 4, FN = 2, TN = 8**. Every precision / recall / F1 number on
screen is computed from those counts (and, in the trade-off scene, from the
20-item ordering itself) — nothing is faked.

## What it teaches

- **The confusion matrix.** Sort items by *(truth × decision)* into four
  outcomes: true/false positives and true/false negatives. Every metric is a
  ratio of these four numbers.
- **Precision = TP / (TP + FP)** — of everything you *flagged*, how much was
  right (the flagged **column**). = 6/10 = **60 %**.
  *Maximise it when a false alarm is costly* — spam filtering, recommendations,
  costly human review. "Be sure before you flag."
- **Recall = TP / (TP + FN)** — of everything that *mattered*, how much you
  *caught* (the relevant **row**). = 6/8 = **75 %**.
  *Maximise it when a miss is costly* — information retrieval / RAG, medical
  screening, fraud & security, legal e-discovery. "Rather over-include than miss
  what matters."
- **The trade-off.** One model, a moving decision threshold: pushing recall up
  (flag more) drops precision, and vice-versa — you can't send both to 100 %.
- **F1 = 2·P·R / (P + R)** — the *harmonic* mean, high only when *both* are high
  (100 % precision with 1 % recall averages ~50 % but scores F1 ≈ 2 %). = **67 %**.
  *Use it when you need one balanced number* / for imbalanced classes.
- **Recap card:** when to maximise recall vs precision vs F1.

## Scenes

1. **Intro** — title card.
2. **Matrix** — 20 items → the 2×2 confusion matrix (TP / FP / FN / TN).
3. **Precision** — the flagged column; when a false alarm is costly.
4. **Recall** — the relevant row; when a miss is costly.
5. **Tradeoff** — the sliding threshold, precision ↔ recall, then F1.
6. **Recap** — "When to maximise what" (recall / precision / F1).
7. **Outro** — thank-you card.

Bookended by the channel's intro / outro cards, matching the sibling explainers
(`animations/BiasVariance`, `animations/CrossValidation`, …). Uses `Text`
(Pango) only — **no LaTeX**.

## Render

```bash
./render.sh full            # whole film, 480p15 (fast)
./render.sh full -q h       # final 1080p60 (the delivered quality)
./render.sh precision       # a single scene
./render.sh matrix --quick  # collapse the reading holds for a fast layout check
./render.sh --stitch -q m   # render each scene and ffmpeg-concat to one file
```

Scenes: `full` (default) · `intro` · `matrix` · `precision` · `recall` ·
`tradeoff` · `recap` · `outro`.

`render.sh` reuses an existing Manim venv elsewhere in the repo
(HarnessEngineering / Fourier / CNN), else bootstraps a local `.venv`.

Env knobs: `PRF_QUICK=1` shortens every hold for a fast sanity render;
`PRF_DELAY=x` overrides the reading-hold multiplier.

## Runtime

Measured full-film duration (1080p60, 1920×1080): **~2 min 18 s**.

Pacing is deliberately unhurried so every line can be read before the scene
wipes: `DELAY` (reading-hold multiplier, default 1.7) and `END_HOLD` (extra hold
on each scene's final frame). Drop them via `PRF_DELAY` / `PRF_QUICK=1` to iterate
faster.
