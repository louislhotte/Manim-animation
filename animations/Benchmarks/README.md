# How AI Benchmarks Work

A no-voice-over Manim explainer on what an AI benchmark actually is, the three
ways models get graded, and why a high score is only ever a proxy for the real
skill. Built in the house style (dark palette, crisp Pango text, intro / outro
bookend, "Created by Ptolémé").

## What it teaches

- **A benchmark = a fixed set of tasks + a fixed grader + one score.** Because
  every model sits the same exam and is graded the same way, the scores can be
  compared and ranked into a leaderboard.
- **Different benchmarks probe different skills:** MMLU (broad knowledge),
  GSM8K / MATH (math word problems), HumanEval (writing code), SWE-bench (fixing
  real GitHub bugs).
- **Grading, up close.** *Multiple choice* is just counting: accuracy is the
  fraction correct across the test. *Exact match* compares the model's final
  answer to a stored one (shown on the canonical GSM8K problem, 48 + 24 = 72).
- **SWE-bench, in detail:** a real GitHub issue → the model writes a patch → the
  patch is applied to a clean checkout → the project's own hidden test suite is
  run. Some tests must flip from failing to passing; others must stay passing.
  The score is the percentage of issues *fully resolved* across 500 tasks. No
  partial credit, no human judge.
- **One try, or many? (pass@k).** Let a model attempt a task `k` times and score
  it solved if any attempt passes: `pass@k = 1 - (1 - p)^k`. A model that
  succeeds ~40% of the time per try reaches ~99% at pass@10, so a headline number
  is meaningless without the `k` behind it.
- **When there is no right answer.** Open-ended tasks have nothing to match
  against, so two responses are shown and a human (or a model judge) votes for
  the better one. Thousands of votes give each model an **Elo** rating, like
  chess. This is how the LMArena / Chatbot Arena leaderboard is built.
- **Progress is real and fast:** SWE-bench Verified went from ~33% to ~93% in
  under two years, while older tests (MMLU, GSM8K) are already near human level
  and saturated — which is why the field keeps building harder ones.
- **The catch:** contamination (the test leaking into training data), Goodhart's
  law (a measure that becomes a target stops being a good measure), and
  saturation. A benchmark is a proxy for a skill, not the skill itself.

## Scenes

1. **Intro** — title card.
2. **Whatis** — the definition (task set → model → grader → score) and the
   comparability leaderboard.
3. **Tour** — four benchmarks, four skills, and the two grading families.
4. **Grading** — multiple-choice accuracy and exact match, up close.
5. **SweBench** — the execution-graded pipeline, end to end.
6. **PassK** — one try vs many; the pass@k curve.
7. **Arena** — preference / Elo grading when there is no gold answer.
8. **Progress** — SWE-bench Verified best score over time, plus saturation.
9. **Catch** — contamination, Goodhart's law, saturation.
10. **Outro** — thank-you card.

## Rendering

```bash
./render.sh                 # whole film, 480p (fast default)
./render.sh passk --quick -q l      # one scene, fast layout check
./render.sh full -q h       # final 1080p60 (the deliverable)
./render.sh --stitch -q m   # render each scene and ffmpeg-concat them
```

`render.sh` reuses an existing repo Manim venv (HarnessEngineering / Fourier /
CNN) if present, otherwise bootstraps a local `.venv`. Pacing knobs: `BM_QUICK=1`
collapses the reading holds; `BM_DELAY=x` overrides the hold multiplier.

Scene names: `intro whatis tour grading swebench passk arena progress catch outro`
(or `full` for the whole film).

## Measured runtime

**4:01** (241.4 s) for the full film (`AIBenchmarks`), measured on the delivered
1080p60 render at `media/videos/benchmarks/1080p60/AIBenchmarks.mp4`. Layout is
identical at every quality; only render time changes.

## Real data / sources

On-screen numbers are real, published milestones or clearly-labelled
illustrations. The hard facts are asserted at import in `benchmarks.py`:

- **GSM8K worked answer** — the canonical first GSM8K problem (Natalia: 48 clips
  in April, half as many in May) → 48 + 24 = **72** (`GSM8K_ANSWER`). Dataset:
  Cobbe et al., "Training Verifiers to Solve Math Word Problems," 2021.
- **SWE-bench Verified size** — **500** human-validated tasks (`SWE_N`). OpenAI,
  "Introducing SWE-bench Verified," Aug 2024. The FAIL_TO_PASS / PASS_TO_PASS
  test split shown in the pipeline is the real SWE-bench evaluation protocol.
- **pass@k** — `pass@k = 1 - (1 - p)^k` with the per-try rate `p = 2/5`
  (asserted → 40 / 78 / 92 / 99% for k = 1 / 3 / 5 / 10). Estimator from Chen et
  al., "Evaluating Large Language Models Trained on Code" (HumanEval), 2021.
- **Progress bars** — SWE-bench Verified best score over time:
  33% (Claude 3.5 Sonnet, Jun 2024) → 49% (Claude 3.5 Sonnet upgrade, Oct 2024)
  → ~72% (2025 frontier) → ~93% (2026 frontier). The two 2024 points are the
  reported Claude 3.5 Sonnet figures; 2025/2026 are representative of the
  published frontier (Claude Opus / Fable-class and GPT-5.x-class models were
  reported in the 85–97% range by 2026). Sources: the public SWE-bench
  leaderboard (swebench.com) and trackers such as codeant.ai/blogs/swe-bench-scores
  and leaderboard.steel.dev.
- **Saturation note** — MMLU and GSM8K frontier scores sit near 90–100%, close
  to human expert level (MMLU human expert ≈ 89.8%, Hendrycks et al., 2021).
- **Illustrative, labelled on screen:** the Model A/B/C leaderboard in "Whatis"
  (82/74/61%), the 17/20 accuracy grid in "Grading", and the Elo ratings in
  "Arena" (1361/1327/1294/1248). These sketch how scores rank; they are not real
  model results. The preference-vote / Elo mechanism is real (LMSYS Chatbot
  Arena / LMArena).
- The SWE-bench pipeline example (a `django/django` `TimeField` serialization
  bug and its patch/tests) is a representative illustration of the task format,
  not a verbatim transcript of a specific instance.
