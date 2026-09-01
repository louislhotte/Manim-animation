# The Bitter Lesson

A short, no-voiceover Manim explainer of Richard Sutton's 2019 essay
**“The Bitter Lesson.”** The one-line thesis: across 70 years of AI research,
*general methods that leverage computation* end up winning — and by a large
margin — over methods that try to build in what humans already know.

> “The biggest lesson that can be read from 70 years of AI research is that
> general methods that leverage computation are ultimately the most effective,
> and by a large margin.” — Rich Sutton, 2019
> ([essay](http://www.incompleteideas.net/IncIdeas/BitterLesson.html))

It's a companion to the `Transformer`, `KVCache` and `Mixtral` films and shares
their dark palette and typographic style.

## What it teaches

- **The two roads.** Every AI system is pulled between building in *human
  knowledge* (rules, features, expertise) and leaning on *computation* (general
  methods that just scale).
- **The exponential engine.** The ultimate cause is Moore's Law: compute gets
  exponentially cheaper. Hand-crafted knowledge gives fast early gains and then
  plateaus; a general method starts behind but rides compute past it. Short
  term, knowledge leads. Long term, computation wins.
- **The same defeat, again and again.** Chess (Deep Blue, 1997), Go (AlphaGo /
  AlphaZero, 2016), speech recognition (statistics → deep learning), and vision
  (SIFT/edges → deep conv nets, ImageNet 2012) all told the same story.
- **What actually scales.** Only two techniques scale arbitrarily with compute —
  **search** and **learning**. Everything else is a detour.
- **Why it's *bitter*, and what to build instead.** Building in what we know is
  satisfying and helps at first, but it plateaus and even blocks the general
  methods. The deeper lesson: don't hand-code the *contents* of a mind (they're
  endlessly complex) — build in the *meta-methods* that can discover that
  complexity. *Build agents that can discover like we can, not agents that
  contain what we've already discovered.*

## Scenes

| # | Scene     | Class     | Beat |
|---|-----------|-----------|------|
|   | Intro     | `Intro`   | Title card |
| — | Roads     | `Roads`   | The thesis; two roads to intelligence (knowledge vs. computation) |
| 1 | Moore     | `Moore`   | The exponential engine: knowledge plateaus, compute overtakes |
| 2 | Pattern   | `Pattern` | The same defeat, again and again — chess, Go, speech, vision |
| 3 | Scale     | `Scale`   | The only two things that scale: search & learning |
| 4 | Lesson    | `Lesson`  | Why it's *bitter*, and what to build instead (meta-methods) |
|   | Recap     | `Recap`   | One-breath summary |
|   | Outro     | `Outro`   | Thank-you card |

The whole film is the `BitterLessonFilm` class.

## Rendering

```bash
./render.sh moore --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                 # whole film, 480p
./render.sh full -q h            # final HD (1080p60)
./render.sh --stitch -q m        # render each scene and concat (720p30)
```

`render.sh` reuses an existing Manim venv elsewhere in the repo (the
`HarnessEngineering`, `Fourier` or `CNN` series' `.venv`) if present, otherwise
it bootstraps a local `.venv`. Everything is drawn with Pango `Text` — no LaTeX.

### Pacing knobs

- `BL_QUICK=1` (or `--quick`) collapses every on-screen hold for fast iteration.
- `BL_DELAY=..` scales the pauses *between* animation steps.
- `BL_READ=..` sets the absolute per-subtitle reading hold (default ~2.6 s).

## Runtime

Measured full film (real pacing): **3:35** (214.9 s, 1080p60). The final
deliverable is `media/videos/bitter_lesson/1080p60/BitterLessonFilm.mp4`
(1920×1080, 60 fps).
