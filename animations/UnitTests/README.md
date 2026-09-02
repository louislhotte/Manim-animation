# Unit Tests — a short explainer

A no-voiceover, house-style Manim film on **what a unit test is and why a green
suite is worth the keystrokes**. It builds the whole idea around one small, real,
deterministic function — `is_leap_year` — whose famous century edge case (1900 is
*not* a leap year, 2000 *is*) makes the point better than any toy `add(a, b)`.

Every result, tick and cross on screen is **genuinely computed**: the leap-year
functions are run at import time, so the pass/fail you see is what Python actually
returns — nothing is faked.

## What it teaches

1. **The unit** — a unit is the smallest piece of behaviour you can test on its
   own: inputs in, one output out, no database, no network. Just logic.
2. **Anatomy of a test** — every test is **Arrange · Act · Assert**: set up the
   inputs, call the unit once, assert what must be true.
3. **Expected vs actual** — an assertion is a claim. Match → green, mismatch →
   red. Change the code (drop the `== 0`) and the *same* test goes red: a
   regression tripwire.
4. **Edge cases** — the happy path passes while a real bug hides at the boundary.
   An edge case (`1900`) catches it; the Gregorian fix (`% 400`) turns it green.
5. **The safety net** — a passing suite is a net. Refactor freely; if you break
   behaviour a test fires in seconds, on every commit — not in production.

Closes on a one-line recap: *Red, green, refactor — with a net.*

## Scenes

`Intro · Unit · Anatomy · Assertion · Edges · Net · Recap · Outro`

Each renders on its own; `UnitTestsFilm` renders the whole thing end to end.

## Render

```bash
./render.sh anatomy --quick     # fast layout check of one scene (480p15)
./render.sh                     # whole film, 480p
./render.sh full -q h           # final 1080p60 (HQ)
./render.sh --stitch -q m       # render each scene and concat (720p30)
```

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering /
Fourier / CNN) if present, otherwise bootstraps a local `.venv`. No LaTeX — all
text is Pango `Text`; code is set in Menlo.

Pacing knobs: `UT_QUICK=1` collapses the reading holds for fast iteration;
`UT_DELAY` / `UT_READ` fine-tune the cadence.

## Runtime

Measured full-film duration (`UnitTestsFilm`, 1080p60): **2:54** (174.1 s),
1920×1080 @ 60 fps. Edge-bleed scan clean across the whole film.
