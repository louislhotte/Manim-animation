# React Hooks & useEffect

A dynamic **~3-minute** explainer on what React **hooks** are and how **`useEffect`**
works — built around the exact use-case everyone hits first: **click a button, watch
it load, and see the component update itself**.

Rendered with [Manim](https://www.manim.community/). Everything uses `Text` (Pango),
never `Tex`, so **no LaTeX toolchain is required**. Code is set in Menlo; the mock
app, spinner, cursor and profile cards are all drawn mobjects — no images, no
browser embedded.

Designed to be understood **without narration** — captions carry the story and
every screen holds long enough to read.

## The story

1. **What is a hook?** — a component is *just a function that returns UI*, and a
   plain function forgets everything when it returns. Hooks let it *"hook into"*
   React: `useState` → memory, `useEffect` → lifecycle. (Every hook's name starts
   with `use`.)
2. **useState — memory** — `const [count, setCount] = useState(0)`, with a live
   counter: click `+1` → call `setCount` → **React re-renders** with the new value.
3. **Why useEffect?** — rendering should be *pure* (`UI = f(state)`); fetching,
   timers and subscriptions are **side effects**. `useEffect` runs them **after**
   the screen paints, so render stays clean.
4. **Anatomy** — `useEffect(fn, [deps])` + cleanup. The **dependency array** is the
   whole game: `[]` runs once (mount), `[a, b]` re-runs when `a`/`b` change, and
   omitting it runs after *every* render.
5. **The example ★** — a real `UserProfile` component, code on the left and a live
   mock app on the right, kept in lock-step. The effect fetches on mount → spinner →
   profile. Then you **click "Next user"**: `setUserId(1 → 2)`; because `userId` is
   in `[userId]`, the effect **re-runs** → spinner → the UI **updates** to the next
   user — no manual redraw anywhere.
6. **The render cycle** — the loop, spelled out: `state changes → React re-renders →
   screen paints → effect runs (only if deps changed) → …`, with the classic
   "no deps + setState = infinite loop" warning.
7. **Recap** — the mental model in three lines: *Render for the screen, `useEffect`
   for everything else.*

## Render

```bash
./render.sh                    # whole film, 480p (fast)
./render.sh example --quick    # the star scene, holds collapsed — quick sanity check
./render.sh full -q h          # final 1080p60 render
./render.sh --stitch -q m      # render each scene and stitch (720p)
```

`render.sh` bootstraps a local `.venv` on first run, or reuses the
HarnessEngineering / Fourier / CNN venv if one already exists.

Scenes render individually too: `intro · hooks · state · effects · anatomy ·
example · cycle · recap · outro`.

## Knobs

- **`RX_QUICK=1`** (or `--quick`) — collapse every reading hold and the end-of-scene
  holds, for fast iteration.
- **`RX_DELAY=1.2`** — the reading-hold multiplier (seconds per "beat"). Raise it to
  give more reading time, lower it to tighten the pace. Pacing lives in the single
  `DELAY` constant at the top of `react_hooks.py`.
