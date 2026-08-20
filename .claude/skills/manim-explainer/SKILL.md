---
name: manim-explainer
description: >-
  House style, standards and the mandatory verification workflow for building the
  no-voiceover Manim explainer animations in this repo (animations/<Name>/ with a
  render.sh). Use when creating, editing, reviewing or rendering any of these
  explainers. Covers the crisp-text spacing fix, layout / no-overlapping-text
  rules, pacing & "how long to wait", the required visual self-check (frame
  extraction + edge-bleed detector), and the recurring Manim gotchas. Triggers:
  "manim animation", "explainer", "render.sh", "new scene", "overlapping text",
  "off-screen / cut off", "spacing looks wrong", "how long should the film be".
---

# Manim explainer — house style & standards

Hard-won standards from the validated animations (HarnessEngineering, Transformer,
CrossValidation, BiasVariance, Gravity, EmbeddingRetrieval, ReactHooks,
Kubernetes, …). Follow these when building or editing any `animations/<Name>/`
explainer. **A render finishing is not the bar — it must be verified to look
right (see §6, which is mandatory).**

## 1. Project shape

Each explainer is a self-contained folder `animations/<Name>/`:

- `<name>.py` — all scenes in one file.
- `render.sh` — bootstraps/reuses a venv and renders a scene or the whole film.
- `requirements.txt` — just `manim` + `numpy` (no LaTeX).
- `README.md` — what it teaches, the scene list, how to render.

Copy `render.sh` from a recent sibling (e.g. `animations/Kubernetes/render.sh`)
and change only: the header comment, `FILE=`, the `scene_class()` name→class map,
the `STITCH` order, and the `*_QUICK` env var. `render.sh` reuses an existing
Manim venv (`HarnessEngineering`, `Fourier` or `CNN`) if present, else bootstraps
a local `.venv` — so you never re-install manim.

Scene wiring in `<name>.py`:

- One base class `_XxxBase(Scene)` with the helpers below.
- One thin class per scene (`class Intro(_XxxBase): def construct(self): self.play_intro()`)
  **and** one full-film class (`class TheName(_XxxBase)` running `play_all()`), so any
  scene renders alone or the whole thing renders end-to-end.
- Bookend every film with the house intro card and the "Thanks for watching!" /
  "Created by Ptolémé" outro.

## 2. Text & spacing — the #1 rule

Manim's `Text` (Pango) **mangles letter/word spacing below ~20 pt** ("card iac ar
rest"). Never render small text directly and never `.set_width()` / scale small
text *up*. Instead shadow `Text` once, at the top of the module, so every call
renders at a large base and scales *down*:

```python
_BaseText = Text
_TEXT_BASE = 60

def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)
```

- Use `Text`, never `Tex`/`MathTex` (keeps the repo LaTeX-free).
- For "formulas" (r², xₜ, 10⁻¹¹) build inline from `Text` pieces with raised
  super/subscripts — see `mtext()` in `animations/Gravity/gravity.py`.
- Code (Dockerfiles, YAML, JS) is set in **Menlo** via a `code_panel()` helper
  (see `animations/ReactHooks` / `animations/Kubernetes`).

## 3. Layout — nothing off-screen, nothing overlapping

Frame is `x ∈ [-7.11, 7.11]`, `y ∈ [-4, 4]` (use `config.frame_x_radius`, not a
hard-coded 7.11). At 480p15 that's ~60 px per unit. Rules:

- **Keep content ≥ ~0.35 u from every edge.** For any text that could be long
  (side captions, notes), clamp it: build it, then
  `if grp.width > avail: grp.scale(avail / grp.width, about_point=grp.get_left())`
  where `avail = config.frame_x_radius - 0.35 - grp.get_left()[0]`. The running
  bottom caption helper (`say`) should `scale_to_fit_width(~12.6)` itself.
- **Things must fit their boxes.** When a box wraps a label grid, size the *box to
  the content* (`width = inner.width + pad`), don't `scale_to_fit_width` the grid
  into a fixed box — scaling a grid to a width also scales its **height** and it
  spills out. (This bit the Control-Plane box.)
- **Space siblings apart.** Repeated glyphs need center spacing ≥ their own width:
  e.g. pods of radius r are `2r` wide, so node "slots" must be `> 2r` apart or the
  pods overlap inside the node. Side-by-side schemas (a diagram next to a code
  panel / a pipeline) must not collide — leave a real gap.
- **Header clearance.** The section header sits top-left (`to_corner(UL, buff=0.5)`);
  keep top-center content low enough to clear it (roughly `y ≤ 2.6`).
- **code_panel title bar:** make the title bar full-width with
  `bar.move_to(bg).align_to(bg, UP)` — `align_to(UP)` alone leaves it x-offset,
  because the indent-shifted code re-centres the panel but not the bar (worst with
  deep indentation). Left-align the filename after the traffic-light dots.
- **Prefer full-screen "takeaway" cards** over cramming a recap box under a busy
  diagram — fade the diagram, then land the one-line recap centered.

## 4. Pacing & "how long to wait"

Reading holds and animation speed are separate knobs. Standard base class:

```python
QUICK = os.environ.get("XX_QUICK") == "1"
DELAY     = float(os.environ.get("XX_DELAY", "0.28" if QUICK else "2.0"))  # reading rhythm
ANIM_SLOW = 1.0 if QUICK else 1.2   # stretch every played animation's run_time
END_HOLD  = 0.2 if QUICK else 2.2   # hold at the end of each scene before the wipe
```

- `self.beat(t)` == `self.wait(t * DELAY)` — every reading pause. Give the eye time:
  a fresh caption wants `beat(1.5–2.0)`; a quick reveal `beat(0.5)`.
- Slow motion by overriding `play()` to multiply `run_time` by `ANIM_SLOW`, but
  **guard `Wait`** (don't scale `self.wait`, which routes through `play(Wait(...))`).
- End every scene with `self.settle()` (`wait(END_HOLD)`) **then** `self.wipe()`
  (clear updaters → `FadeOut` everything). Optionally hold a `SCENE_GAP` first.
- `XX_QUICK=1` collapses all holds for fast iteration; the real cadence is the
  non-QUICK values. Expose an `XX_DELAY` override.
- Reality check on length: **fixed animation time ~= 90–110 s** for a 6-scene film;
  reading holds add the rest. You can reach ~3–4 min comfortably; **don't claim
  "5–6 min" and pad empty holds to get there** — add real content instead, and
  state the *measured* runtime (`ffprobe … format=duration`) in the README.

## 5. Recurring Manim gotchas

- **`always_redraw`:** never `Create`/`FadeIn` an `always_redraw` mobject (strict-zip
  crash) — animate a *static copy*, then `add()` the live one and swap. Always
  `clear_updaters()` before wiping (the base `wipe()` does this).
- **`Circle`/`Ellipse`/`Arc` default to `color=RED`**, and `.set_opacity(x)` turns on
  the *fill* (not just the stroke). So a "stroke-only" ring you dim with
  `.set_opacity(x)` renders as a **red disc**. Only ever dim a stroked shape with
  `stroke_opacity=`/`.set_stroke(opacity=…)` and keep `fill_opacity=0`, or pass an
  explicit `color=`/`fill_color=`. (This is what made the CDN globe bands, the
  map-pin halos and the atmosphere ring bleed red.)
- **`ImageMobject` is not a `VMobject`** — it can't go inside a `VGroup` (raises).
  Use `Group(...)` to mix a baked image (e.g. a textured planet) with vector
  mobjects, and use `Group(...)`—not `VGroup(...)`—in the scene-clearing `FadeOut`.
- **`t2c` overlaps:** `Text(t2c=…)` raises if two colored substrings overlap — even
  when the color is equal (`setUser` ⊂ `setUserId`). Prune per line with a
  `_safe_t2c()` that drops any key that is a substring of another present key.
- **`DecimalNumber` rejects `weight=`** — style it after construction.
- **`LaggedStartMap` unpacks each submobject as *args** → use
  `LaggedStart(*[Anim(m) for m in group])`.
- **Plain `VMobject` has no `add_tip`** — hand-build arrowheads (Polygon) for custom
  paths; use `Arrow`/`GrowArrow` for straight arrows.
- **`node_box`-style helpers:** a center passed as a 2-tuple throws — coerce to 3-D.
- **`get_part_by_text` isn't real** (`__getattr__` lies via `hasattr`) — lay out
  tokens explicitly if you need per-token control.
- Pass optional `font=`/`slant=` only when set (a `font=None` can choke Pango) — use
  a small `txt()` wrapper that drops `None` kwargs.

## 6. Visual verification — MANDATORY before "done"

A clean exit code ships overlaps, off-screen text and misaligned boxes. After
rendering, **look at the frames** — do not rely on the user to catch bugs.

1. Render the changed scene(s): `./render.sh <scene> --quick -q l` (layout is
   identical to the full quality; QUICK only changes hold length).
2. **Automated cutoff scan** — run the bundled detector on each scene video; it
   flags any content within ~9 px of a frame edge (i.e. text running off-screen):
   ```bash
   <venv>/bin/python .claude/skills/manim-explainer/edgecheck.py <scene>.mp4 48
   ```
   It cannot see *overlaps* — only cutoffs — so still do step 3.
3. **Eyeball key frames.** Extract with ffmpeg and read them as images. Sample at
   the **end of each beat**, never mid-transition (a frozen fade always looks
   "weird"):
   ```bash
   D=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 s.mp4)
   ffmpeg -y -ss "$(awk "BEGIN{print $D*0.6}")" -i s.mp4 -frames:v 1 out.png
   ```
   Use explicit output filenames (bash assoc-arrays + globs have mangled these).
   To inspect a tight spot (a title bar, a box edge), crop + upscale:
   `-vf "crop=W:H:X:Y,scale=iw*3:ih*3:flags=neighbor"`.
4. Check specifically for: text touching/exceeding edges; glyphs overlapping each
   other or their box; arrows that look detached/weird; a title bar not spanning
   its panel; captions colliding with a panel or the header.
5. Only after both the scan is clean **and** the frames look right, do the final
   full render and report the *measured* duration.

## 7. Rendering cheatsheet

```bash
./render.sh <scene> --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                   # whole film, 480p (default)
./render.sh full -q h              # final HD (1080p60) — slow; run in background
./render.sh --stitch -q m          # render each scene and ffmpeg-concat to one file
```

Quality: `-q l|m|h|k` = 480p15 / 720p30 / 1080p60 / 2160p60. Iterate at `l --quick`;
only render `-q h` for the final deliverable.

## Definition of done

- [ ] Each scene renders alone and the full film renders end-to-end (exit 0).
- [ ] `edgecheck.py` is clean on every scene (no edge bleed).
- [ ] Key frames eyeballed: no overlaps, nothing cut off, boxes fit, arrows clean.
- [ ] Reading cadence is comfortable; every scene ends on a settle before the wipe.
- [ ] README states what it teaches, the scene list, and the **measured** runtime.
