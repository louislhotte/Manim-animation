# JavaScript's `this` — a short explainer

A ~3-minute, no-voiceover Manim film on the single most-confused keyword in
JavaScript, built around one idea:

> **`this` is decided by *how* a function is called (its call-site), not by
> where the function is written** — and arrow functions are the deliberate
> exception, capturing `this` lexically.

Concrete over metaphor: every beat is real JS you can paste into a console.

## What it teaches

1. **The puzzle** — one `function whoAmI() { return this }` body, four
   call-sites, four different values of `this`. Only the call-site changed.
2. **The dot rule** — `user.greet()` sets `this = user`. Look immediately left
   of the dot at the call. `this.name` reads `"Ada"`.
3. **The lost `this`** — rip the method off the object
   (`const greet = user.greet; greet()`) or hand it to a callback
   (`setTimeout(user.greet, 1000)`) and the dot is gone: `this` falls back to
   `undefined` in strict mode → `TypeError`.
4. **Who sets `this`?** — the four bindings, in precedence order:
   `new Fn()` › `fn.call/apply/bind(obj)` › `obj.fn()` › `fn()`.
5. **Pinning it down** — `bind()` locks `this` once; arrow functions have no
   `this` of their own and borrow the enclosing one (the `setInterval` classic).
6. **Takeaway** — call-site, not definition — unless it's an arrow.

## Scenes

`Intro` · `Hook` (the puzzle) · `DotRule` · `Lost` · `Rules` · `Fix` ·
`Takeaway` · `Outro`, plus the full film `ThisKeyword`.

## Render

```bash
./render.sh dot --quick        # fast layout check of one scene (480p15)
./render.sh                    # whole film, 480p
./render.sh full -q h          # final 1080p60
./render.sh --stitch -q m      # render each scene and concat (720p30)
```

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering /
Fourier / CNN) if present, otherwise bootstraps a local `.venv`. Env knobs:
`THIS_QUICK=1` collapses the reading holds, `THIS_DELAY` / `THIS_READ` tune the
cadence.

Measured runtime: **2 m 39 s** (130 animations, real cadence).
