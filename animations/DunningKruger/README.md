# The Dunning-Kruger Effect

Why a little knowledge feels like a lot. A short, house-style Manim film built on
`manimx`. It is a story, not a study: no percentiles, no error bars. One real game
of chess, then one picture that carries the rest of the film: everything there is
to know about a subject is a dark field, and what you know is the part your light
reaches.

Made to be narrated, and readable without the voice: every beat has one short
caption. The timed script is in `VOICEOVER.md` (and `voiceover.srt`).

## The story, scene by scene

1. **A great move.** One of your first games of chess. Three moves in, you spot a
   move that attacks the queen, and you are sure of it. One move later it is
   checkmate. The board is drawn the way a beginner sees it: dark, except where
   they look. The threat was on the board all along, in the dark part.
   *The less you know, the harder it is to see how little you know.*
2. **A small light.** The same idea as a picture. A dark field, a light, 22 things
   known, 7 more in sight, and a fence where the field seems to end. "How much do I
   know?" can only be answered against what is in sight: 22 of 29, most of it. Then
   the picture pulls back and the fog lifts: 22 of 400.
   *To see what is missing, you would need what is missing.*
3. **The climb.** The light grows, and the same run is drawn as a chart: gold is
   how much of the field you feel you know, blue how much you really know. The
   feeling races ahead, then falls as the fence runs away from the light, and
   stops falling when the fence reaches the true edge.
   *The bottom is where you start being right about yourself.*
4. **The other end.** Someone who has lit almost the whole field pictures everybody
   else with a light as big as their own, and places themselves above the middle,
   well short of the top. Lined up by what they really know, they stand at the top.
   *Beginners misjudge themselves. Experts misjudge everyone else.*
5. **Everyone.** One person, five fields: a big light for the day job, small ones
   for almost everything else, and from the inside a small one can feel almost
   complete. What moves the fence is learning more, and people who know more can
   teach you what you are missing. The film ends on the first field, pulling back
   one more time.
   *Feeling sure is about your light, not about the size of the dark.*

Visual conventions, the same in every scene: **gold is what somebody believes** (the
plan on the board, the fence, "you feel you know"), **blue is what is true** (what
the light really reaches), red is the danger nobody saw. A filled blue dot is a
thing you know, a hollow gold one a thing you know you have not learned, a faint
grey one a thing you do not know exists.

## What is real, and what is drawn

**Real.**

- The chess game is the scholar's mate: 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#.
  `python model.py` replays it with python-chess when that is installed
  (`pip install chess`) and checks that the knight on f6 does attack the queen and
  that the last move is checkmate.
- The name and the date: Justin Kruger and David Dunning, "Unskilled and Unaware of
  It: How Difficulties in Recognizing One's Own Incompetence Lead to Inflated
  Self-Assessments", *Journal of Personality and Social Psychology* 77(6),
  1121-1134, 1999.
- What the film says in words about people comes from that paper:
  - the weakest performers overrate themselves, and the skill they lack is the one
    they would need to notice it (scenes 1 and 2);
  - the best performers underrate where they stand among others, because they take
    others to be about as good as they are; and this mistake is the smaller of the
    two (scene 4);
  - what made the weakest more accurate in the study was training them (its Study
    4; they still overrated their rank, but far less). Being shown the better
    answers of others did not (its Study 3). Hence scene 5: the fence moves when
    the light grows, and the helper is there to teach.

**Drawn for the film** (each scene says so in its bottom line).

- The field, the light and every share on screen come from a toy model,
  `model.py`: what you really know is the lit share of the field; what you feel you
  know is the lit share of what is in sight; what is in sight grows faster than
  what you know, until it reaches the true edge. Its three parameters were chosen
  so that the picture reads well. Nothing is fitted to data. The numbers of scene 2
  (22, 29, 400; 76 % and 6 %) and the bars of scene 5 are counted from the dots on
  screen; the chart of scene 3 draws the model's formulas, which the dot counts
  follow to within a few points from the first peak on.
- **The chart of scene 3 is that model, not the study.** The peak-and-valley curve
  is the popular picture of the effect. The 1999 paper has no such curve: its
  figures plot perceived against actual performance by quartile, and in them the
  weakest rate themselves well above their results but still below the best. The
  film uses the curve as a story about one learner over time, labels it as a toy,
  and keeps the toy on the right side of that fact: its first peak (77 %) stays
  under the level the expert ends on (86 %).
- The people of scene 4 and the five fields of scene 5 (which subjects, how big
  each light is) are made up.

**Not in the film.** Whether the effect is what its authors say it is has been
argued ever since: part of the pattern is what any noisy self-rating produces
(regression to the mean, plus most people rating themselves above average), and the
paper itself says so before arguing that this is not the whole story. The film
tells the authors' account, as a story.

## Scenes

`Intro · Move · Light · Climb · Expert · Everyone · Outro`, each renderable alone;
`./render.sh` stitches them.

## Render

```bash
./render.sh move --quick --check   # layout pass + edge scan + contact sheet
./render.sh                        # whole film, 480p
./render.sh full -q h              # final 1080p60 (slow: run in background)

# the timed narration script
MX_TRACE_DIR=$PWD/media/trace ./render.sh --stitch -q h
python ../../tools/voiceover.py . -q h
```

Pacing knobs: `DK_WPS` (the narrator's words per second, default 2.6), `DK_QUICK=1`
/ `--quick` (collapse holds). `manim.cfg` switches Manim's cache off: the painters
read a clock that never stops, which the cache does not see.

**Measured runtime:** 4 min 28 s (268.7 s at 1080p60): intro 14.0, Move 45.1, Light 55.1,
Climb 56.9, Expert 44.2, Everyone 41.7, outro 11.7. 25 narrated lines, 575 words at 156
words a minute; no line is tight. Each scene moves 91 to 100 % of the time
(`tools/motioncheck.py`), with no still stretch of 2 s or more.

## Files

- `dunning_kruger.py`: the storyboard (docstring) and the five scenes.
- `kit.py`: the pictures. Painters for what is many and alive (`FogMap`, the field
  and the light; `Spot`, the dark over the chess board), ordinary mobjects for what
  has a face or must be read (`Buddy`, a face drawn from ten numbers so that a mood
  is a tween; `Board`; `Gauge`; `ClimbChart`).
- `model.py`: the toy model with its asserts, and the chess game.
