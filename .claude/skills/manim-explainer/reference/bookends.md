# Intro / outro / rules cards

Every film (the Manim explainers and the matplotlib `Simulations/<Name>/` series)
opens on a title card and closes on a thank-you card, in the house palette
(`BG #0E1117`, `INK #F5F3EF` title, `MUTED #8A93A6` subtitle, `GOLD #FFD166` rule).

## Manim (`manimx`)
Set class attributes on the film's base scene; `play_intro()` / `play_outro()` do
the rest:

| Attribute | Card |
|---|---|
| `TITLE` | bold title, `INK`, with a rule running 1 unit past both ends |
| `SUBTITLE` | the title morphs into this one-line promise (`MUTED`) |
| `TAGLINE` | small line under the byline (optional) |
| `RECAP` | one-line recap on the outro, in `GOLD` (optional) |
| `RULE_COLOR`, `BYLINE_COLOR` | default `GOLD`, `SKY` |
| `intro_emblem()` | optional small mobject at the right end of the rule |

Byline: **"Created by Ptolémé"**. Outro title: **"Thank you for watching!"**.
Thin scene classes expose them: `class Intro(_Base): construct -> self.play_intro()`.
Older films keep bespoke `play_intro` overrides; new films should not need one.

## Rules / setup card (encouraged for simulations and games)
Before the action, state the rules and the agents' stats in two colour-coded panels,
then the one-sentence law and a punchy takeaway (*"This is math, not magic."*). A
persistent bottom key can keep the rules visible throughout.

## matplotlib (`Simulations/PredatorPrey/`)
Render each card to a 1920x1080 PNG (`cards.py`), the simulation to mp4 (`viz.py`),
and stitch `intro -> rules -> sim -> outro` in **one** ffmpeg `concat` pass with a
0.4 s fade to/from black (`film.py`). Force every input to
`scale=1920:1080,fps=30,format=yuv420p,setsar=1` so concat joins cleanly. Draw the
past-both-ends underline by measuring the title with `text.get_window_extent()` after
`fig.canvas.draw()`. Render to local `/tmp` and `mv` into the OneDrive repo (writing
the mp4 straight into the synced folder stalls for minutes).
