# Yjs & CRDTs

How people and AI agents edit one document at the same time. A no-voiceover,
house-style Manim film built on `manimx`: **5:26** (325.7 s, measured on the
1080p60 deliverable, `media/videos/yjs/1080p60/YjsFilm.mp4`).

It introduces CRDTs through Yjs (15.7 million npm downloads a week, against 0.2
million for Loro and 0.1 million for Automerge): why index-based edits diverge,
how ids and origins fix it, how two writers at the same position are
ordered, what happens when someone goes offline, why delivery order cannot break a
document, how Yjs compares with other libraries, and where Tiptap and Hocuspocus
fit. Three writers travel through every scene: **Ada** and **Bob** (people) and an
**Agent** (an AI peer), one colour each.

## Scenes (`render.sh` name, class)

| # | name | class | what it shows |
|---|------|-------|---------------|
| 0 | `intro` | `Intro` | house title card |
| 1 | `together` | `Together` | a Tiptap-style editor with three live carets (keys vs streamed tokens); then the same paragraph as three private copies, each a little ahead of the others |
| 2 | `positions` | `Positions` | `insert(2,"D")` and `insert(3,"s")` cross and land: `CRDsT` vs `CRDTs`; an OT server rewrites the 3 into a 4 |
| 3 | `items` | `Items` | every character gets an id `client:clock`; the real `Item` struct (id, origin, rightOrigin, content); the run splits, both copies converge; the real 10-byte update; the cells C, R, D, T, s spell out Conflict-free Replicated Data Types |
| 4 | `samespot` | `SameSpot` | Ada and the agent type at the same position; each run is one item; the tie is broken by client id on both copies |
| 5 | `offline` | `Offline` | Bob loses his connection, both sides keep editing; state vectors, the diff, only the missing items travel; a tombstone anchors Bob's text |
| 6 | `anyorder` | `AnyOrder` | the story's 8 updates delivered to three copies in three orders, then a 40,320-pixel map of every possible order, recoloured by result: one colour, one sentence |
| 7 | `numbers` | `Numbers` | the length of a real paper over its 259,778 keystrokes; Yjs replays it in real time (the sweep lasts the measured 0.93 s); the same trace on Loro and Automerge; weekly downloads; v13 from 2020 to today |
| 8 | `stack` | `Stack` | the real `client.js`, `server.js`, `agent.js` beside the live pipeline Tiptap, Y.Doc, provider, Hocuspocus, database; back in the editor, the three writers type the film's sentence |
| 9 | `outro` | `Outro` | house thank-you card |

`YjsFilm` is the whole film. The sentence built item by item across scenes 3 to 6,
*CRDTs merge all edits, even offline*, is what every delivery order ends on in
scene 6 and comes back as the last line typed in the editor.

**On "stable".** The film does not claim that Yjs wins every benchmark: on this
trace Loro replays faster and Automerge saves smaller, and Yjs comes second on all
three measures. What it shows instead is why a Yjs document is hard to break (any
delivery order, duplicates and long offline periods end on the same bytes, with no
central server deciding), and why it is the safe pick (the same major version since
January 2020, 15.7 million downloads a week).

## Real data, not mockups

Nothing on screen is typed in by hand. `generate_assets.py` copies `demo/` to a
temp dir (never into this OneDrive-synced repo), runs `npm install` with pinned
versions, and actually runs:

- **`demo/story.mjs`, `assets/story.json`.** The film's story on real Yjs 13.6.33:
  three `Y.Doc`s (client ids pinned to 1, 2, 3 so the film can print them; they are
  random 32-bit numbers in real life). Every row of items, id, origin, tombstone,
  state vector and byte count shown in scenes 3 to 6 is read from that run, and the
  scenes `assert` that what they draw equals it. The story's 8 updates are then
  delivered to a fresh document in **all 8! = 40,320 orders**: one text, one
  byte-identical encoded state; 40,264 of those orders needed Yjs's pending queue.
  Each update delivered three times in random order (20,000 trials): same result.
- **`demo/stack.mjs`, `assets/stack.json`.** Two real Tiptap 3.33 editors (in
  jsdom) and a headless agent (a plain `Y.Doc` plus `HocuspocusProvider`) on a real
  Hocuspocus 4.8 server with the `Database` extension. The code panels of scene 8
  are the code this script runs. It checks that the three copies converge, that
  the agent's caret label really appears in Ada's editor DOM, that an offline
  writer catches up on reconnect, and that the document survives a server restart.
  The editor text of scenes 1 and 8 is what those editors produced.
- **`demo/bench.mjs`, `assets/bench.json`.** A real-world editing trace (the
  keystroke history of a published paper: 182,315 insertions, 77,463 deletions)
  replayed on Yjs 13.6.33, Loro 1.17.1 and Automerge 3.5.0, every edit as its own
  transaction, median of several runs. Timings are from one laptop and say so on
  screen. The Yjs size is the V2 encoding (`encodeStateAsUpdateV2`).
- **`assets/npm.json`.** Release dates and last week's downloads from the npm
  registry.

Re-bake with `./render.sh --assets` (needs node 22+, npm and network; about two
minutes). Renders never touch the network.

## Sources

- Yjs: <https://github.com/yjs/yjs>. Its algorithm, YATA: Nicolaescu, Jahns,
  Derntl, Klamma, *Near Real-Time Peer-to-Peer Shared Editing on Extensible Data
  Types*, GROUP 2016.
- Editing trace: Martin Kleppmann and Alastair Beresford,
  <https://github.com/automerge/automerge-perf> (CC BY 4.0). It is the writing of
  *A Conflict-Free Replicated JSON Datatype* (IEEE TPDS 2017).
- Tiptap: <https://tiptap.dev>. Hocuspocus: <https://github.com/ueberdosis/hocuspocus>.
- Loro: <https://loro.dev>. Automerge: <https://automerge.org>.
- npm registry download counts, week of 3 to 9 November 2026.

## Colour

The three writer colours carry identity everywhere and any two can be neighbours,
so they were chosen with the `dataviz` skill's validator rather than by eye:
`#508FF9`, `#E26E1A`, `#C170BB` pass every check on the film's surface, all pairs
(worst pair dE 9.8 under colour-vision-deficiency simulation, 17.9 in normal
vision). The house `SKY` / `LILAC` pair does not (5.7 and 15.0). The order map of
scene 6 uses a validated one-hue ramp.

## Render

```bash
./render.sh items --quick --check     # one scene: layout pass, edge scan, contact sheet
./render.sh                           # whole film, 480p
./render.sh --stitch -q h --no-cache  # final 1080p60, scene by scene, then stitched
YJ_TRACE=1 ./render.sh offline        # print how long every caption stays on screen
python ../../tools/motioncheck.py /private/tmp/yjs-media/videos/yjs/480p15/*.mp4
```

Media goes to `/private/tmp/yjs-media` (override with `YJ_MEDIA_DIR`); the final
film is copied to `media/` here (git-ignored). Pacing: every caption is held for
its reading time (`chars / 16 + 0.9 s`, see `hold` in `manimx/scene.py`), and the holds carry
motion; `--quick` collapses them. `motioncheck.py` prints the share of each scene
that moves and any still stretch of 2 s or more: on the final render the eight
content scenes move 69 to 82 % of the time, with no still stretch over 2 s (the
house intro and outro cards hold for about 4 s). Use `--no-cache` after changing
`kit.py`: Manim's partial-movie cache does not see changes inside updaters or
animations.

## Files

- `yjs.py`: storyboard, data loading with assertions, the eight scenes.
- `kit.py`: the film's building blocks (`LiveLine`, `ItemRow` / `Block`, `Caret`,
  the editor window, packets, the Item card, state-vector bars).
- `generate_assets.py`, `demo/`: the Node scripts that produce `assets/`, and the
  Python driver that runs them and asserts their results.
