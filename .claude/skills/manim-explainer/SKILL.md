---
name: manim-explainer
description: >-
  How to build, edit, review and render the Manim explainer films in this repo
  (animations/<Name>/, silent or made to be narrated, built on the shared `manimx`
  library and rendered by each folder's render.sh): the quality bar that separates a film from a
  slideshow, the storyboard-first workflow, the library API, the hard house rules
  (crisp text, layout, pacing, arrows, no em-dashes, real data) and the mandatory
  visual verification loop. Also the intro/outro card spec shared with the
  matplotlib Simulations/ series. Triggers: "manim", "explainer", "new film",
  "new scene", "render.sh", "manimx", "make it less basic / amateurish",
  "overlapping text", "cut off / off-screen", "spacing looks wrong",
  "how long should the film be", "intro / outro card", "Created by Ptolémé",
  "voice-over", "narration script", "Simulations/".
---

# Manim explainers

Every film lives in `animations/<Name>/`, imports **`manimx`** (repo root) and is
rendered by a 10-line `render.sh` that sources **`tools/render_lib.sh`**. Never
copy boilerplate between films: if two films need it, it belongs in `manimx`.
A clean render is not the bar. A film is done when it clears §1 and the frames
have been *looked at* (§5).

## 1. The bar: a film, not a slideshow

Contact sheets of all 60 films (Nov 2026) split cleanly. The user loves
**Transformer, KV Cache, Mixtral, Neural Network, LangGraph, Tensors**, and calls
films like RBAC, ElastiCache, ALB, CDN, SemanticLayer "basic / amateurish".

What the good ones do, every scene:

1. **The data structure is the picture.** An embedding is a column of cells, attention
   is a heatmap, a prediction is a row of probability bars, an agent is its real
   `StateGraph` with the message list filling up. Not a box labelled "embedding".
2. **One hero visual fills the frame** (roughly 60% of it), captions sit under it.
3. **A motif travels through the film**: the token row "Not all those who wander"
   is in every Transformer scene; the same image, graph or table keeps coming back.
4. **Real numbers, computed and asserted in code**: softmax outputs, a trained
   network's loss curve, a real benchmark, a real dataset (see `reference/real-data.md`).
5. **Motion carries meaning**: the object itself transforms (the cache grows a
   column, the shape tuple grows an axis, a counter ticks, a highlight moves with
   the sentence). FadeIn is the glue, never the explanation.
6. **Code and picture in lockstep** for software topics: the real API in a
   `code_panel`, the highlighted line driving the node that lights up.

What reads as amateur (find these in a contact sheet and remove them):

1. **Slide frames**: a centred sentence on black, checkmark bullet lists,
   "X, in one card / in one breath", pros-vs-cons boxes. Allowed once per film at
   most (the final takeaway). Recap by **reprising the hero visuals** in miniature,
   not by listing sentences.
2. **Small things floating in an empty frame**; labels under 16 pt.
3. **Boxes and thin arrows** where nothing transforms.
4. **Toy or "illustrative" numbers** where real ones exist.
5. **Typography drift**: serif fallback (now impossible via `manimx`), LaTeX digits
   from `DecimalNumber` (use `live_number`), em-dashes, terse jargon captions.
6. **No through-line**: each scene restarts from a blank screen with new objects.
7. **Metaphors replacing the thing**: for a topic the viewer knows, glass boxes and
   floating packets lose to the real artifact (LangGraph v1 failed on this).

## 2. Workflow

1. **Storyboard before code**, in the film's docstring. Per scene, one line:
   *question it answers | hero visual | what moves | takeaway caption*; then the
   motif and the data source. If a scene's hero visual is "text", redesign it.
   Keep it tight: 4 to 7 scenes, 2.5 to 4 minutes; cut scenes rather than pad.
   For a film that will be narrated, write the voice-over line of every beat too
   (§4, Narrated films): the narration sets the length of each beat.
2. **Scaffold**: `python3 tools/new_film.py Name "Title" "Subtitle" --prefix XX`
   (folder, film module on `manimx`, render.sh, README).
3. **Build one scene at a time**, and after every change:
   `./render.sh <scene> --quick --check`, then **Read the contact sheet image** it
   prints, fix, repeat. `python3 tools/lint_film.py <film>.py` catches the
   mechanical rules (§4).
4. **Self-review** the whole film's sheet against §1 before showing the user.
5. **Final**: `./render.sh full -q h` in the background, then put the *measured*
   runtime and the sources in the README.

## 3. manimx cheat-sheet

```python
from manimx import *        # = from manim import *  + crisp Text, house font, palette, below

class _Base(ExplainerScene):              # Explainer3DScene for 3D; ExplainerMixin for mixins
    pace = Pace.from_env("XX", read=3.0)  # XX_QUICK / XX_DELAY / XX_READ env overrides
    TITLE, SUBTITLE = "The KV Cache", "Why the 1000th token is almost as cheap as the first"
    TAGLINE, RECAP = "the optimization behind fast LLM inference", "Compute the past once."
    SCENES = ("waste", "reuse")           # play_all(): intro, scene_waste(), scene_reuse(), outro

    def scene_waste(self):
        h = self.section_header("1 · The waste", AMBER)     # top-left; keep content below y~2.6
        grid = heatmap(values, MINT)                        # data as a picture
        self.caption("Every step recomputes the same Keys and Values.")  # swaps + read() hold
        self.add(self.cite("Vaswani et al., 2017"))         # sources on screen
        self.settle(); self.wipe()                           # every scene ends like this
```

| Need | Use |
|---|---|
| Timing | `beat(t)` rhythm, `read(k)` reading hold (~3 s), `settle()`, `wipe()`, `card_wait()` |
| Captions | `caption(text)` (swap + hold), `say(text)` (mobject only), `clear_cap()`, `cite(src)`, `takeaway(l1, l2)` |
| Timed captions | `cap(text)` (the swap as an animation, played under the motion), `hold(ambient=)` / `settle(ambient=)` (wait only for what is left of the reading time), `lead(text)`, `then(anim, after)` (leave, then arrive) |
| Narrated film | `tell(caption, vo)` (a beat lasts as long as its line takes to say), `cue("phrase", ambient=)` (wait for the narrator to reach a word), `narrate(vo)` (over a card); `tools/voiceover.py` writes the timed script |
| Motion | `Tween(obj, attr=...)`, `Breathe`, `Throb`, `Travel` / `stream` (packets), `ripple`, `Do`, `Pop`, `glow_dot`, `polyline`, `mix` |
| Text | `Text` (crisp), `txt(s, fs, color)`, `mono(s)`, `mtext([...])` formulas, `safe_t2c`, `clamp_width` |
| Glyphs | `chip`, `pill`, `stamp`, `plate`, `arr(p, q)` (points only), `wire`, `make_tick`, `make_cross`, `dot_label` |
| Data | `heatmap`, `vcells`, `prob_bars`, `live_number(tracker)` (LaTeX-free counter) |
| Code | `code_panel(spec, t2c_table, title)` -> `(panel, lines)`, then `self.focus(panel, lines, [i])` |
| Layout | `keep_inside(m)`, `fit_in_frame(m)`, `SAFE`, `CAPTION_Y`, `HEADER_CLEAR_Y` |
| Cards | `play_intro()` / `play_outro()` from `TITLE SUBTITLE TAGLINE RECAP`; `intro_emblem()` hook |
| Palette | `BG PANEL INK MUTED FAINT GOLD GOOD BAD` + hues `SKY MINT LILAC AMBER` (alias them: `Q_C = SKY`) |

Override any method in the film's base class when a film genuinely needs its own.
If you change `manimx` itself, prove no film changed (§5.4).

## 4. House rules (hard)

**Text.** `Text` only, never `Tex`/`MathTex`/`DecimalNumber` (LaTeX-free repo;
`mtext` for formulas, `live_number` for counters). Never `.set_width()` or scale
small text *up*. No em-dash in rendered text (use `.` `:` `,`). Captions are
complete plain sentences in reading order; one caption at a time; under ~90
characters (Pango soft-wraps past ~100). A coloured word inside a sentence is one
`Text(..., t2c={"word": C})`, never a `VGroup` of pieces (baselines jump). Separate
inline pieces with `buff`, not padding spaces (Pango trims them). Code in Menlo via
`code_panel`.

**Layout.** Content stays `SAFE` (0.35 u) inside every edge: clamp anything whose
length depends on text (`keep_inside(clamp_width(m, w))`). Boxes are sized to their
content, never content scaled into a fixed box. Side-by-side groups are
`arrange(RIGHT, buff=...)`d and `fit_in_frame`d, never pinned at fixed x (a wider
string then collides). Repeated glyphs are spaced by at least their own width.

**Pacing.** Err slow: prose ~2 s on screen, formulas / code / dense diagrams 3-4 s
*after* they finish drawing. `read()` after every caption; never pad empty holds to
reach a target length. Measured runtime goes in the README. Slow is not still: a
reading hold should carry motion that means something (the item under discussion
pulses, packets keep flowing, a counter runs), never a frozen frame for 4 s. Pattern
and measuring tool: `reference/gotchas.md`, "Pacing and motion".

**Narrated films.** When the user will voice the film over, the picture and the
voice carry it and text steps back: one short caption per beat (under ~65
characters, larger: `fs` 27), on screen for the whole beat (8 to 12 s), never
typed, scrolled or swapped faster than that; no paragraph the viewer must read
while something moves. Write the narration in the storyboard first, start each
beat with `tell(caption, vo)` and place the visual changes with `cue("phrase")`,
so they land on the narrator's word. Render with `MX_TRACE_DIR=<dir>` and run
`python tools/voiceover.py animations/<Name>` for `VOICEOVER.md` (timecodes,
room, words per line; `TIGHT` marks a line that does not fit) and `voiceover.srt`.
Worked example: `animations/Terraform`.

**Arrows and motion.** `arr(a.get_right(), b.get_left())`: endpoints are points
(`arr` raises on a mobject). Loop-backs are orthogonal elbows in a free lane, not
`CurvedArrow`s. No arrow may cross content or land on an image. Camera moves only in
real 3D scenes (`reference/3d.md`); 2D motion comes from the mobjects.

**Content.** Real data when it exists (`reference/real-data.md`); a paper's table or
figure is shown as a cropped screenshot, never rebuilt. Concrete artifact over
metaphor. Every number on screen is computed or cited, and the source is on screen
(`cite`) and in the README.

**Bookends.** Every film opens with `play_intro()` and closes with `play_outro()`
("Created by Ptolémé"); spec and the matplotlib variant in `reference/bookends.md`.

## 5. Verification (mandatory before "done")

1. `./render.sh <scene> --quick --check` per changed scene: renders 480p, runs the
   edge-bleed scan (`tools/edgecheck.py`) and writes a 12-frame contact sheet.
   **Read the sheet image.** Layout is identical in quick mode; only holds change.
2. In the sheet and in individual frames (`ffmpeg -ss T -i v.mp4 -frames:v 1 f.png`,
   sampled at the *end* of a beat, never mid-fade), check: overlaps, text touching
   edges or escaping boxes, header collisions, dead space, slide frames, every
   arrow traced end to end (right endpoints, head attached, crossing nothing).
   Zoom a frame with subscripts and confirm they match the body font.
3. `python3 tools/lint_film.py <film>.py`: zero errors (LaTeX, em-dashes, bare-mobject
   arrows); read the warnings (tiny fonts, long lines, slide smells, missing cite).
4. Changing shared code (`manimx`, a helper used by several scenes):
   `python tools/scene_fingerprint.py <film>.py` before and after (run with the Manim
   venv python). Identical digests prove identical frames; `--ignore-code` compares
   on-screen state only (for moved helpers). Any other difference must be explained.
5. Final HD render only after 1-4 are clean; report the measured duration.

For a film that has to feel dynamic, also run `python tools/motioncheck.py` on the
full-pace 480p scene videos (not `--quick`): it prints the share of time that moves
and every still stretch of 2 s or more, so freezes are found without watching.

Rendering: `./render.sh [scene|full] [-q l|m|h|k] [--quick] [--check] [--stitch]
[--list] [-p] [-- manim args]`. The shared venv lives outside OneDrive at
`~/.cache/manimx/venv` (OneDrive breaks venv symlinks and stalls media writes);
`MX_PYTHON`, `MX_MEDIA_DIR` override. Details: `tools/render_lib.sh` header.

## Definition of done

- [ ] Storyboard in the docstring; every scene has a hero visual that is not text.
- [ ] Clears §1: motif, real numbers, meaningful motion, at most one slide frame.
- [ ] Every scene renders alone and the full film renders (exit 0, file written).
- [ ] `--check` clean on every scene; sheets read; arrows traced; lint has no errors.
- [ ] README: what it teaches, scenes, sources, **measured** runtime.

## References (read when relevant)

- `reference/gotchas.md`: Manim pitfalls (updaters, colours, groups, t2c, images, OneDrive).
- `reference/real-data.md`: fetching and baking real data; paper tables as screenshots.
- `reference/3d.md`: `Explainer3DScene`, unlit Cairo shading, fixed HUD, camera rules.
- `reference/bookends.md`: intro / outro / rules cards, incl. the matplotlib Simulations.
