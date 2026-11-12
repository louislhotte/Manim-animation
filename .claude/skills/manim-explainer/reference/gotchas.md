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
- **Per-character control**: `Text(s, disable_ligatures=True)` has exactly one submobject
  per character, spaces included, so `t[7]` / `t[10:13]` index the string. Without it,
  ligatures and dropped spaces shift every index. For text that is typed, inserted
  into or deleted from, set the string once between sentinels (`"H" + s + "H"`) and cut
  one advance cell per character at the ink midpoints: `prose_cells` / `LiveLine` in
  `animations/Yjs/kit.py`.

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
- **Attribute names that collide with the `Mobject` API**: a custom `self.fade = 0.0`
  or `def target(self)` on a `VGroup` subclass breaks `FadeOut` / `MoveToTarget` far
  from the cause (`'float' object is not callable`). `target`, `fade`, `scale`, `shift`,
  `color`, `points` are taken: name yours `alpha`, `aim`, ...
- **`FadeOut` of a nested part splits its parent**: fading `chip.digit` makes Manim
  restructure `scene.mobjects` (the parent is replaced by its remaining pieces), and
  the leftovers no longer follow the parent. Animate the part's opacity
  (`part.animate.set_opacity(0)`) and swap in a new mobject, or fade the whole parent.
  Worse when the parent lays itself out in an updater: the scene only updates its
  top-level mobjects, so **the parent's updater stops for good, without any error**.
  After `FadeOut(panel.title)` a `TextPanel` kept its last layout: a block "opened"
  in one jump at the next explicit refresh, rows shown later never appeared, and a
  new arc stayed a default-size triangle at the origin (Terraform, scene 8).
- **Animating a new `VGroup` of mobjects that are already on stage** re-adds them as
  that group: they jump to the top of the draw order, and parents that held them are
  split the same way. Build such groups before anything is added, or fade the pieces.
  `Succession(...)` / `AnimationGroup(...)` around an animation of a *nested* mobject
  do this silently (their own group is added to the scene), so a big parent such as a
  window ends up as loose parts in `scene.mobjects`. A later `FadeOut(parent)` then
  re-adds the parent *on top* of everything added since, hiding what should survive
  it. Before adding the survivors, put the parent back: `self.add(parent)`.
- **A child taken out of its parent (`parent.remove(child)`) is not drawn at all** until
  it is added to the scene again: do both in the same breath, not a play apart.
- **`set_z_index` only reaches the family a group has *now*.** Content added later to
  a raised group (a line appended to a HUD panel whose window is at z-index 10) keeps
  z-index 0 and is drawn *under* the panel's own background: the text "does not
  appear". Give new children the parent's z-index when adding them (`TextPanel._adopt`
  in `animations/Terraform/kit.py`).
- **A film helper named like a `manimx` helper silently replaces it.** With
  `from manimx import *` followed by `from stage import *`, a 3D `plate(origin, ...)`
  shadowed the house `plate(mob)`, and the failure surfaced far away as an unexpected
  keyword argument. Give film-local helpers their own names (`ground_plate`).
- **`family_members_with_points()` skips mobjects that have no points yet.** A part
  that builds its faces in `refresh()` must walk `get_family()`, or the faces never get
  their first points and nothing is drawn.
- **Identity colours that sit side by side** (three writers, three series): run the
  `dataviz` skill's `validate_palette.js` on the film surface (`--mode dark --surface
  "#0E1117" --pairs all`). The house `SKY` / `LILAC` pair fails colour-vision
  separation; `#508FF9` / `#E26E1A` / `#C170BB` passes (Yjs film).

## Animation
- **`always_redraw`**: never `Create`/`FadeIn` the live mobject (strict-zip crash).
  Animate a static copy, then `add` the live one and remove the copy.
- **Clear updaters before fading** a scene out. (lib) `wipe()` does it.
- **`LaggedStartMap` unpacks each submobject as `*args`**: use
  `LaggedStart(*[FadeIn(m) for m in group])`.
- **Do not stretch `Wait`**: reading holds are owned by `beat`/`read`/`settle`.
  (lib) `play()` never scales a bare `Wait`; `play_unstretched()` bypasses
  `pace.anim_slow` when a fade must keep its exact length.
- **`self.play(..., run_time=X)` overrides every animation's own `run_time`**, including
  `m.animate(run_time=...)` and the parts of a `Succession`. When durations differ,
  set them per animation and leave the play-level kwarg out.
- **`Succession` / `AnimationGroup` put the mobjects of non-introducer animations on
  stage when the play starts**, not when their turn comes (only introducers such as
  `FadeIn` / `Create` are added late). A custom mover scheduled after a `Wait` shows
  early: hide it in `__init__` and reveal it in `interpolate_mobject` (`Travel` in
  `manimx/motion.py`).
- **A mobject removed from its parent during a play is still drawn until that play
  ends**: the renderer freezes its list of moving family members when the play starts.
  A label swapped by an updater (`group.remove(old); group.add(new)`) therefore shows
  old and new on top of each other (`×6` under `×11` reads `×611`). Hide before
  removing: `old.set_opacity(0)`. It only shows in frames sampled *mid-animation*:
  zoom on a counter or a typed label while it runs, not just at the end of a beat.
- **An animation that ends before its play does is re-applied at alpha = 1 on every
  later frame** (a top-level animation, or the last-ending child of a top-level
  `AnimationGroup`). So `play(FadeIn(m), ..., Succession(Wait(5), FadeOut(m)))` fades `m`
  out and then pops it back until the play ends: two captions sat on top of each other
  for 1.5 s. Put the early animation in a `Succession(...)` (it stops interpolating
  after its last child), or use two plays.
- **Recolouring a nested part re-stacks it.** The same split as above: animating
  `field.box.animate.set_stroke(AMBER)` inside a group re-adds the box *after* its
  siblings, and an opaque box then covers the caret that was drawn on it. Fade a
  stroke-only copy in over the part instead of recolouring the part.
- **Two animations on one mobject in the same play** (`FadeIn(m)` plus
  `m.animate.shift(...)`): the second captures the first's start state (transparent).
  Play them one after the other, or fold both into one animation.
- **Tweening plain attributes while updaters keep running**: an `Animation` suspends
  the updaters of its mobject. Run attribute tweens on a throwaway `Mobject()` host
  with `suspend_mobject_updating=False` (`Tween`, `Breathe` in `manimx/motion.py`),
  so self-laying-out rows and lines keep following.

## Pacing and motion
- **Reading time as a guarantee**: a fixed `read()` after each caption either rushes
  long captions or freezes short ones. `cap()` / `hold()` (in `manimx`, born in the Yjs film)
  swap the caption *as an animation* (it plays under the motion) and then wait only
  for what is left of `chars / 16 + 0.9 s`. `MX_TRACE=1` (or the film's own
  `TRACE_ENV`, e.g. `YJ_TRACE=1`) prints the time each caption really stayed up and
  flags the short ones.
- **A narrated film is paced by its narration**: `tell(caption, vo)` gives the beat
  the time the line takes to say (`words / WPS + VO_PAD`), `cue("phrase")` waits
  until the narrator reaches a word, so the picture changes on it. Cues are computed
  from word counts: when a cue falls *before* the previous animation has finished it
  simply does not wait, so keep the animations between two cues shorter than the
  words between them. `MX_TRACE_DIR` + `tools/voiceover.py` give the timed script.
- **Holds that move**: `hold(ambient=lambda t: [...])` fills the remaining reading
  time with motion that means something (the item under discussion breathes, packets
  keep flowing) instead of a freeze.
- **Find the dead stretches without watching**: `python tools/motioncheck.py
  <video.mp4>...` prints the share of the film that moves and every still stretch
  of 2 s or more with its timestamp. Aim for no still stretch over about 3 s.
- **Swaps in one place: leave, then arrive.** `play(FadeOut(a), FadeIn(b))` with `a`
  and `b` in the same spot stacks two pictures (two captions, two code panels, a chart
  and the table that replaces it) for half the fade, and a frozen frame of it reads
  as a bug. Fade the old one out first: `FadeOut(a, run_time=0.25)` plus
  `Succession(Wait(0.25), FadeIn(b, run_time=0.4))` in the same play (no play-level
  `run_time`). `then()` and `cap()` in `manimx` do this.

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
  `hash("a string")` is random too (it changes with every Python process): never
  derive a phase or a colour from it, use an index.
- **Manim's partial-movie cache can serve a stale clip after a fix.** A play is keyed
  on the scene state when it starts and on the animations' own attributes, not on
  the code they call. A fix inside an updater, a `refresh()` or an
  `interpolate_mobject` leaves the key unchanged, so the old clip is reused and the
  bug "is still there". Render with `./render.sh <scene> --no-cache` after such a fix,
  and for the final HD render.
