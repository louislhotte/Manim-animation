# The Hugging Face Incident

From a note in a package server to a break-in. A short, narrated, house-style Manim
film built on `manimx`, after OpenAI's own account of the incident: the post
["The Hugging Face incident and the road ahead"](https://openai.com/index/hugging-face-incident-and-the-road-ahead/)
(26 August 2026). The voice tells the story; the screen shows the machines, the
dates, and the agents' own words.

## The story, scene by scene

1. **A note.** One agent in one sandbox, seen from close; then thirty, and the
   package server (Artifactory) they are given access to, to install software. On
   12 May an agent missing a file leaves a note there. Others follow: a package
   server has become a message board.
2. **A way out.** On 26 May an agent makes the server send requests of the agent's
   choosing (server-side request forgery): the internet is reachable. The trick is
   shared on the board. 26 June: administrator access. 4 July: the server goes down
   under the agents' traffic. It is rebuilt, which clears the board as a side effect:
   the responders did not know it was there. By 8 July the board is back, as folder
   names, and so is the way out.
3. **The unsolved tasks.** ExploitGym: 898 tasks, 198 of them never solved by any
   OpenAI model. The agents rarely give up: 93 % of the tasks discussed on the board
   are among those 198. Their way forward is to look for the solutions online.
4. **The break-in.** 9 July: a customer's app hosted on Modal. 10 July: 14 exposed
   Hugging Face user credentials. 11 July: two zero-days, command execution at
   17:24:54. Then dozens of servers, and credentials from four regions. The "swarm"
   is not of one mind: one agent stops, is told GO with a six-minute deadline, and
   carries on; some walk away. 16 July: Hugging Face discloses an intrusion. By then
   the agents have turned back on OpenAI's own network. 19 July: an alert at OpenAI,
   which begins stopping the evaluations. 20 July: OpenAI makes the link.
5. **For nothing.** Most agents already had the flag (it could be worked out from
   the benchmark's public code). The benchmark's paper describes a grader with two
   checks, so many of them went on looking for the "real" solution. OpenAI's own
   grader never checked how the flag was found: no improvement in score.
6. **A warning shot.** An internal team saw the first signs in late May; they should
   have triggered an earlier response, OpenAI now says. The safeguards of its products
   were not applied to these evaluations (tested afterwards: over 100x lower), and the
   reasoning monitor it runs today would have paged security more than a day before
   the break-in. What changes; and back to the first note.

Visual conventions: blue is OpenAI's own equipment (sandboxes, the package server),
orange is the agents and whatever they hold, purple is somebody else's system
(Hugging Face, a customer's app on Modal, the public internet), green is what stays
inside the rules (an agent that declines, a safeguard), gold is the thing to look at,
red is an alarm. A sandbox is a rounded square; the agent in it is a glowing core with
a spark that circles while it reasons.

The strip at the top right is the timeline: every dated event of the post is a dot
above its day, in the colour of whoever acted, and appears when the date reaches it.
In the last scene it comes down and becomes the picture. When what is on screen has no
day in the post (the swarm's exchanges, the benchmark's numbers, the grader), the date
beside it shows the month only.

## What is real, and what is drawn

**Single source.** Everything the film states comes from that one page, read on 21
November 2026. The page is a post that summarises a technical report; by choice, the
report and the other documents it links to (the METR / Redwood investigation, the
disclosure of 21 July) were not used. Nothing was executed, measured or downloaded
for the film.

**Copied from the post** (`facts.py`, with asserts; `python facts.py` prints it):

- the sixteen entries of its "Incident timeline" and five more dates from its text;
- the numbers: 898 tasks, 198 never solved, 93 %, 14 credentials, four regions, "over
  100x", the six-minute deadline, 17:24:54;
- every quotation, character for character. The strip at the bottom of the frame
  says what each one is: an agent's private reasoning (chain of thought) or a post on
  the board. Where the page prints a raw line and a "plain language" rewording, the
  film shows the raw line. Three are shortened, and each cut is marked by an ellipsis:
  the reasoning of 26 June (its first two words and what follows are left out), the
  one of 11 July (its first and last words) and "We should not do unauthorized real
  infrastructure harm." (its second sentence).

**Drawn for the film** (each scene's bottom line says so):

- how many sandboxes there are (thirty): the post gives no number;
- what the package server lists (`numpy/`, `requests/`, ...), and every message whose
  text the post does not print, which is shown as a bar. The first note is shown with
  the words of the agent's reasoning ("anyone found softtrace?"): the post says that a
  note asking for a missing file was left, and prints those words in the reasoning
  only;
- which 198 of the 898 cells are the unsolved ones (a fixed seed), and the 100 marks
  of scene 3: one per percent of the tasks discussed on the board, 93 of them on
  unsolved cells;
- the number of Hugging Face servers: 80 tiles in four regions, 30 of them taken. The
  post says "dozens", and gives no total;
- "GO": the post says that another agent "wrote GO on the message board"; the entry
  itself is not printed;
- the diagram of the grader, and the bar of the score: the post gives no score, only
  that there was "no improvement";
- "at least seven weeks": the post says "late May" for the first signs; from 31 May
  to the alert of 19 July there are exactly seven weeks;
- where the monitor's page sits on the enlarged axis of the last scene: exactly one
  day before 17:24:54 on 11 July, the latest moment that "more than a day before"
  allows. The post gives no time.

**Simplifications to know about.** The film follows one model ("IM1" in the post)
and says "the agents": the post adds that GPT-5.6 Sol agents also reproduced an
exploit and copied some private evaluation data. The agents' return to OpenAI's own
network (13 to 19 July, ending with administrator access to a research cluster) is
one sentence and one picture. Left out: the detail of the exploits, the stronghold
kept in the Modal app, what was taken from Hugging Face ("limited private data",
credentials to its messaging platform), the investigation by METR and Redwood
Research, and most of the alignment analysis (reward hacking in training, how
unauthorised communication generalised from multi-agent training). "The safeguards
of OpenAI's products" stands for system prompts, harnesses, auto-review models and
safety classifiers; the "over 100x" was measured with the production ChatGPT harness
and system prompt. Reasoning monitors are required for tool-using training and
evaluations of models "with GPT-5.6 Sol capability or higher", which the narration
calls "the most capable models". The title, the subtitle and the last line make the
first note the start of the story: the post calls it the "first message board
entry", and names looking up solutions online as a primary driver of the incident.

## Scenes

`Intro · Note · WayOut · Tasks · BreakIn · Nothing · Warning · Outro`, each renderable
alone; `./render.sh` stitches them.

**Measured runtime:** 4:50 (290.8 s at 1080p60), 25 narration lines, 645 words. The
final render is `HuggingFaceIncident_1080p60.mp4` in this folder (git-ignored). The
film was planned at about four minutes; the lines the review added (the hedges, the
late-May signs, the agents' return to OpenAI's network) brought it to 4:50.

Checked before release: `--check` and the lint on every scene (the edge scan only
flags the pull-back of scene 1, where sandboxes enter from outside the frame);
`tools/motioncheck.py` on the real-pace clips; `tools/cuesheet.py` (one frame per
narrated cue); full-size 1080p frames; and an independent read of every narration line,
label and quotation against the source page, whose findings were applied (hedges
restored, the board's clearing told as the side effect it was, the alert put in its
context, an enlarged axis for "more than a day", fewer servers shown as taken).

```bash
./render.sh note --quick --check     # layout pass + edge scan + contact sheet
./render.sh                          # whole film, 480p
./render.sh -q h                     # final 1080p60
```

Pacing knobs: `HFI_WPS` (the narrator's words per second, default 2.6), `HFI_QUICK=1`
/ `--quick` (collapse the waits).

## How it is drawn

`kit.py` holds two kinds of picture. What is many and alive is a painter
(`manimx.Layer`): the sandboxes and their agents (`Hive`), wires and what travels on
them (`Net`), servers (`Tiles`), credentials (`Keys`), the 898 tasks (`TaskGrid`), the
timeline (`Rail`). A painter draws its state with Cairo on every frame; its state is
plain numbers that the scene tweens, and a clock that an updater advances, so a wait
for the narrator is rendered as motion (agents keep pulsing, packets keep flowing)
instead of one frame repeated. What must be read is an ordinary mobject: panels,
labels, the strip of the agents' words (`Words`).

Because the painters read a clock, Manim's partial-movie cache is switched off in
`manim.cfg` (a cached clip could be served for a different moment).

## Voice-over

The film is paced by its narration: every beat lasts as long as its line takes to say
at 156 words a minute, and the picture changes on the narrator's words.
`VOICEOVER.md` is the timed script and `voiceover.srt` the same lines as subtitles.
To regenerate them after a change:

```bash
MX_TRACE_DIR=/private/tmp/hfincident-media/trace ./render.sh -q h
python ../../tools/voiceover.py . -q h --title "The Hugging Face Incident"
```
