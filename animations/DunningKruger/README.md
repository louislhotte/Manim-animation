# The Dunning-Kruger Effect

Why a little knowledge feels like a lot. A short, house-style Manim film built on
`manimx`. It is a story, not a study: no percentiles, no error bars. One real game
of chess, then one picture that carries the rest of the film: everything there is
to know about a subject is a dark field, and what you know is the part your light
reaches.

The film has a voice: a text-to-speech model that runs on this machine reads the
narration, and the film is cut to it (see [The voice](#the-voice)). It still reads
without sound: every beat has one short caption.

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
./render.sh full -q h              # final 1080p60, without sound

# the timed script (VOICEOVER.md, voiceover.srt: each line and when its caption appears)
MX_TRACE_DIR=$PWD/media/trace ./render.sh --stitch -q h
python ../../tools/voiceover.py . -q h
```

Pacing knobs: `DK_VOICE=0` (ignore the recorded voice and pace the film for a
reader), `DK_WPS` (that reader's words per second, default 2.6), `DK_QUICK=1` /
`--quick` (collapse holds). `manim.cfg` switches Manim's cache off: the painters
read a clock that never stops, which the cache does not see.

**Measured runtime:** 3 min 51 s (231.0 s at 1080p60): intro 14.0, Move 37.9, Light
45.4, Climb 49.4, Expert 38.1, Everyone 34.6, outro 11.7. 25 narrated lines, 575
words. Every caption stays up for its whole line (5.3 to 14.3 s), never less than
its reading time. Each scene moves 91 to 100 % of the time
(`tools/motioncheck.py`), with no still stretch of 2 s or more. Paced for a reader
instead (`DK_VOICE=0`, 156 words a minute) the film lasts 4 min 28 s.

## The voice

`media/DunningKruger_1080p60-narrated.mp4` is the film with its narration, and
`DunningKruger_1080p60-narrated.srt` what is said and when, sentence by sentence
(a copy sits next to the video, where players pick it up as subtitles).

The voice is Kokoro (82M parameters, voice `af_heart`, speed 0.9), run locally by
[mlx-audio](https://github.com/Blaizzy/mlx-audio): nothing is sent to a service.
The sound is not kept in git (`media/` is ignored); the scripts in `narration/`
rebuild it.

**The film is cut to the voice, not the voice to the film.** A word count is a
poor clock: "So beginners misjudge themselves." is four words and two seconds.
So `narration/voice.json` holds the rhythm of the voice as it was really said (how
long each line takes, when each word starts), and `dunning_kruger.py` follows it:
a beat lasts as long as its line, and `cue("phrase")` waits for the phrase itself.
Nothing is stretched or squeezed. Sentence pauses are brought to a narrator's
0.6 s (the model's own run from almost nothing to 0.65 s), and where a picture is
not ready for its word, the pause before it grows a little: the longest pause
inside a line is 0.76 s. Between two lines the voice rests for about a second.

```bash
VOICE_PY=...    # a Python with mlx-audio, on Apple silicon; Kokoro-82M-bf16 and
                # whisper-large-v3-turbo-asr-fp16 (mlx-community) in the Hugging Face cache
MANIM_PY=~/.cache/manimx/venv/bin/python

$MANIM_PY narration/cue_times.py   # the lines of the film (a few minutes, no video written)
$VOICE_PY narration/speak.py       # says them: takes in media/narration/, and voice.json
$MANIM_PY narration/cue_times.py   # the film follows voice.json now: when each picture lands
MX_TRACE_DIR=$PWD/media/trace ./render.sh --stitch -q h
$MANIM_PY narration/place.py       # the voice under the pictures: the narrated .mp4 and .srt
$VOICE_PY narration/listen.py      # a speech recogniser listens to the result
```

After a change to the pictures only, the first two steps can be skipped.

**What was checked, and how** (`narration/placement.json`, `narration/heard.json`):

- Each of the 46 cues gets its word 0.06 to 0.53 s after its picture starts to
  change (0.30 s in the middle), by the voice's own timing of its words.
- A speech recogniser that does not know the script (Whisper large-v3-turbo, local)
  was played the finished file. It wrote down every word of the script, in order
  (580 of them once "22" is "twenty two" and "Dunning-Kruger" two words), and nothing else while the
  voice speaks. Over the silent end card it added "Thank you": the track is
  silent there, and filling a long silence with a film's usual last words is a
  known habit of that recogniser. It hears each word 0.01 s from where it was
  placed (median; 95 % within 0.10 s, all within 0.35 s), and each cue's word
  0.29 s after its picture (from 0.04 s before to 0.40 s after).
- The video stream of the narrated file is the silent film's, bit for bit; the
  voice sits at -16 LUFS, true peak -2 dB.

A recogniser checks words and timing. Whether the voice sounds right takes ears.

## Files

- `dunning_kruger.py`: the storyboard (docstring) and the five scenes.
- `narration/`: the voice. `speak.py` (the takes, and `voice.json`: the rhythm the
  film follows), `cue_times.py` (`cues.json`: the lines, and when each picture
  lands), `place.py` (the narrated film, its subtitles, `placement.json`),
  `listen.py` (`heard.json`: what a recogniser hears in the result), `common.py`.
- `VOICEOVER.md`, `voiceover.srt`: every line with the time its caption appears.
- `kit.py`: the pictures. Painters for what is many and alive (`FogMap`, the field
  and the light; `Spot`, the dark over the chess board), ordinary mobjects for what
  has a face or must be read (`Buddy`, a face drawn from ten numbers so that a mood
  is a tween; `Board`; `Gauge`; `ClimbChart`).
- `model.py`: the toy model with its asserts, and the chess game.
