# IntersectionObserver in React

A no-voiceover, house-style Manim explainer on the browser's
`IntersectionObserver` API and how you use it in React. Built around exactly one
concrete demand: **a strict scrolling example with a live count.**

Everything is `Text` (Pango), never `Tex`, so there is no LaTeX toolchain. Code is
set in Menlo. Nothing is a screenshot: the browser frame, the cards, the sentinel
spinner and the cursor are all drawn Manim mobjects.

## What it teaches

Scrolling a long list and reacting when items come into view (infinite scroll,
lazy images, "mark as seen" analytics) is one of the most common front-end jobs.
The naive way listens for every `scroll` event and calls `getBoundingClientRect()`
by hand, on the main thread, on every pixel of scroll.

`IntersectionObserver` inverts it: you hand the browser a list of targets and a
callback, and the browser tells you *asynchronously* when a target crosses a
visibility threshold you defined. In React you wire it up once inside a
`useEffect` (create the observer, `observe` your nodes) and tear it down in the
cleanup (`disconnect`).

## The star scene (`count`) is a real, verified count

The scrolling viewport is not smoke and mirrors. Every card has a known position;
a single updater moves the whole list by a `scroll` `ValueTracker` and, every
frame, counts how many card centers have risen past the gold threshold line. The
big "items seen" number **is** that count, so it is provably correct (monotone in
the scroll offset). Each card latches green with a check the instant it crosses,
`unobserve` is highlighted to explain why it counts only once, and a **sentinel**
row triggers `load more` so the same observer keeps counting into an infinite
scroll (the tally climbs to 11).

## Scenes

| # | scene      | class      | what happens |
|---|------------|------------|--------------|
| — | intro      | `Intro`    | title card + spinning React atom |
| 1 | problem    | `Problem`  | the old way: `scroll` listener + `getBoundingClientRect()`, a runaway event counter, main-thread reflow |
| 2 | idea       | `Idea`     | hand the browser targets + a callback; `root` / `rootMargin` / `threshold` |
| 3 | api        | `Api`      | `new IntersectionObserver(cb, opts)`, `entries`, `entry.isIntersecting`, `observe` / `unobserve` / `disconnect` |
| 4 | count ★    | `Count`    | the React hook next to a scrolling viewport with a live, deterministic "seen" count + sentinel/load-more |
| 5 | recap      | `Recap`    | the mental model in three lines |
| — | outro      | `Outro`    | thanks card |

Full film class: `IntersectionObserverReact`.

## Render

```bash
./render.sh count --quick -q l   # fast layout check of the star scene (480p15)
./render.sh full                 # whole film, 480p, real cadence
./render.sh full -q h            # final 1080p60 (slow; run in background)
./render.sh --stitch -q m        # render each scene and ffmpeg-concat (720p)
```

`render.sh` reuses an existing repo Manim venv (HarnessEngineering / Fourier /
CNN) if present, so Manim is not reinstalled. Pacing knobs: `IO_QUICK=1` collapses
every reading hold; `IO_DELAY=<seconds>` overrides the reading-hold multiplier
(default 2.2).

## Measured runtime

Full film at real cadence: **2:22** (142.4 s; measured on the `IntersectionObserverReact` render).
Verified per the house checklist: `edgecheck.py` clean on all seven scenes, and
key frames of every scene eyeballed (no overlaps, nothing cut off, arrows clean,
the star scroll/count correct end to end).
