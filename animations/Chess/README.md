# The Immortal Game — a cinematic chess replay

A self-explanatory (no voice-over) Manim film that replays the most famous game
in chess history, move by move:

> **Adolf Anderssen vs. Lionel Kieseritzky** — London, 1851 · King's Gambit

Anderssen sacrifices a bishop, **both rooks and finally his queen**, then mates
with three minor pieces:

```
1.e4 e5 2.f4 exf4 3.Bc4 Qh4+ 4.Kf1 b5 5.Bxb5 Nf6 6.Nf3 Qh6 7.d3 Nh5
8.Nh4 Qg5 9.Nf5 c6 10.g4 Nf6 11.Rg1 cxb5 12.h4 Qg6 13.h5 Qg5 14.Qf3 Ng8
15.Bxf4 Qf6 16.Nc3 Bc5 17.Nd5 Qxb2 18.Bd6‼ Bxg1 19.e5 Qxa1+ 20.Ke2 Na6
21.Nxg7+ Kd8 22.Qf6+‼ Nxf6 23.Be7#
```

## What's on screen

- A persistent board built from a walnut frame, ivory/teal squares and
  coordinates; the opening army is placed with a soft cascade.
- **Smooth piece glides** — knights hop along an arc — with a red flash on every
  capture and a captured piece flying into a **material tray**. By the end the
  tray shows White's losses (♟ ♝ ♟ ♜ ♜ ♛) against Black's three pawns: the whole
  point of the game, made visible.
- **Last-move highlighting** and a **red pulse** whenever a king is in check.
- A running **move badge** (number + notation) and a **story caption** that
  lingers long enough to read.
- **Extra emphasis** — a glowing arrow and a long pause — on the three
  brilliancies (18.Bd6‼, 22.Qf6+‼, 23.Be7#).
- A closing **"why it's mate" breakdown** — every flight square (c7, e7, e8)
  crossed out and explained — then a title card.

## Render

```bash
./render.sh                     # the whole film (Immortal), 480p, fast
./render.sh full -q m           # final 720p render
./render.sh game --quick        # just the game, holds collapsed (fast check)
./render.sh game --quick --plies 12   # only the first 12 half-moves (dev aid)
./render.sh --stitch -q m       # render intro + game + outro and stitch
./render.sh intro               # a single part (intro | game | outro)
```

The first run bootstraps a local `.venv` (or reuses another series' Manim venv
in this repo). Quality flags: `l`=480p15 (default), `m`=720p30, `h`=1080p60,
`k`=2160p60. Add `-p` to preview when done.

### Scenes / classes

| scene | class      | what it is                              |
|-------|------------|-----------------------------------------|
| full  | `Immortal` | intro card → the game → outro card      |
| intro | `Intro`    | title card (players · venue · year)     |
| game  | `Game`     | the board and all 45 half-moves + mate  |
| outro | `Outro`    | the "Thank you for watching!" card      |

### Pacing knobs (env vars)

| var           | default | effect                                            |
|---------------|---------|---------------------------------------------------|
| `CHESS_QUICK` | `0`     | `1` collapses every reading hold for a fast render |
| `CHESS_PLIES` | `999`   | stop the game after *N* half-moves (dev aid)      |

At the default pace the game runs ~3½ minutes (plus the intro/outro cards) —
enough time to follow every move and read the commentary. `--quick` renders the
game in ~90 s for iteration.

## Notes / implementation

- **No LaTeX.** Everything is `Text` (Pango). Chess pieces are Unicode glyphs
  from the *filled* set (♚♛♜♝♞♟) recoloured — ivory for White, charcoal for
  Black — so both armies read cleanly on either square colour. They're drawn
  with a symbol font that actually carries the glyphs (`Arial Unicode MS`, with
  `Apple Symbols` as a fallback); if neither is present, Pango falls back.
- The whole game is data-driven: each half-move is a small record
  (`from`, `to`, notation, caption, capture/check/mate flags) in `GAME`, and one
  `play_move` engine animates it. There is no chess logic — the moves are the
  historical game, so no castling/en-passant/promotion handling is needed.
- Text is rendered at a large base size and scaled down (Manim mangles glyph
  spacing at small font sizes).
