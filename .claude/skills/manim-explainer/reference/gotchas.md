# Manim gotchas (manim 0.21, Cairo renderer)

Each of these cost a round of user feedback at least once. `manimx` already
handles the ones marked (lib).

## Text
- **Small `Text` is mangled** below ~20 pt (spacing, fallback font for sub/superscripts).
  (lib) `manimx.Text` renders at 60 pt and scales down. Never `set_width` / scale a
  small `Text` *up*; never bind the raw class (`BaseText`) for visible text.
- **Serif fallback**: without a default font Pango picks a serif. (lib) `manimx` sets
  Helvetica Neue; `MX_FONT` overrides. Do not call `Text.set_default` yourself.
- **`t2c` overlap raises** even with equal colours (`setUser` inside `setUserId`).
  (lib) `safe_t2c(s, table)`.
- **Pango trims leading/trailing spaces**: separate inline pieces with `buff`.
- **Coloured word mid-sentence**: one `Text(..., t2c=...)`; a `VGroup` of words
  misaligns baselines (descenders).
- **Soft wrap**: a single `Text` longer than ~100 characters wraps by itself. Split it.
- **Never `Transform` a number `Text` into another number**: it crossfades into mush.
  Use `live_number` (redraw) or `FadeOut`/`FadeIn` with a small shift.
- **`DecimalNumber`/`Integer` need LaTeX** and render digits in a LaTeX font; they also
  reject `weight=`. Use `live_number(tracker, fmt)`.
- **`get_part_by_text` is not real** (`hasattr` lies via `__getattr__`): lay tokens out
  yourself if you need per-token control.
- Pass `font=` / `slant=` only when set: `font=None` can choke Pango. (lib) `txt()`.

## Mobjects and groups
- **`Circle`/`Ellipse`/`Arc` default to `color=RED`**, and `.set_opacity(x)` turns on the
  *fill*: a "dimmed ring" becomes a red disc. Pass `color=`/`stroke_color=` and dim with
  `set_stroke(opacity=...)`. Same for `interpolate_color`: it needs `ManimColor`s.
- **Never `set_opacity` a `CurvedArrow`**: it fills the arc into a crescent.
- **`ImageMobject` is not a `VMobject`**: it cannot go in a `VGroup`. Use `Group`, also
  in the scene-clearing `FadeOut`.
- **A submobject faded out but still inside its `VGroup` reappears** when the group is
  later faded or transformed. `group.remove(sub)` after the fade.
- **Cached centres go stale**: values computed from `get_center()` before `to_edge` /
  `arrange` describe the old position. Recompute after layout.
- **Plain `VMobject` has no `add_tip`**: build the head as a `Polygon`, or use `Arrow`.
- **A 2-tuple centre** passed to a helper that does `move_to`: coerce to 3-D first.
- **Scene classes named like Manim mobjects** (`Vector`, `Matrix`, `Line`) shadow them
  in the module after the class statement. Name scenes `VectorScene`, ...

## Animation
- **`always_redraw`**: never `Create`/`FadeIn` the live mobject (strict-zip crash).
  Animate a static copy, then `add` the live one and remove the copy.
- **Clear updaters before fading** a scene out. (lib) `wipe()` does it.
- **`LaggedStartMap` unpacks each submobject as `*args`**: use
  `LaggedStart(*[FadeIn(m) for m in group])`.
- **Do not stretch `Wait`**: reading holds are owned by `beat`/`read`/`settle`.
  (lib) `play()` never scales a bare `Wait`; `play_unstretched()` bypasses
  `pace.anim_slow` when a fade must keep its exact length.

## Arrows
- **`Arrow(mobject, mobject)` comes out diagonal**: Manim takes the farthest bezier point,
  not the mid-edge. (lib) `arr()` only accepts points: `arr(a.get_right(), b.get_left())`.
- **Loop-back / cycle edges**: route an orthogonal elbow in a free lane
  (`VGroup(Line(a, s1), Line(s1, s2), arr(s2, target))`); lay agent loops as a vertical
  spine so the return runs up one free side. A `CurvedArrow`'s bow flips with the sign
  of `angle`: verify it in a frame. A compact "repeat xN" glyph (see `repeat_glyph` in
  `animations/Diffusion`) is often clearer than any return edge.

## Code panels
- (lib) `code_panel` centres the title bar on the panel before `align_to(UP)`
  (indent-shifted code re-centres the panel, not the bar).
- Highlight with one moving bar: `self.focus(panel, lines, [i, j])`.

## Environment
- **OneDrive breaks venvs**: symlinks become 10-byte text files that "run", exit 0 and
  render nothing. (lib) the shared venv lives in `~/.cache/manimx/venv`.
- **OneDrive stalls long media writes**: HD renders of long films go to a local
  `MEDIA_DEFAULT` (e.g. `/private/tmp/<film>-media`) or `MX_MEDIA_DIR`.
- **Pillow 13 rejects the `mode=` manim 0.21 passes** for `ImageMobject`: pinned `<13`
  in `tools/requirements-render.txt`.
- **`.gitignore` blocks `*.png`**: bake photos as `.jpg`, or `git add -f` on purpose.
- Unseeded randomness makes every render different: seed (`np.random.default_rng(7)`).
