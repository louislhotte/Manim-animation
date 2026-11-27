"""model.py: the two things this film computes instead of drawing by hand.

1. **A light in a dark field** (a toy, not data). Everything there is to know about
   a subject is a disc of dots. You stand in the middle; what you know is the disc
   your light reaches, of radius ``r`` (0 = nothing, 1 = everything).

   * What you *really* know is the lit share of the field: ``real(r) = r**2``.
   * You cannot count what you cannot see. Around your light you make out a little
     more of the field, as far as ``horizon(r)``; that is the whole field as far as
     you can tell. What you *feel* you know is the lit share of that:
     ``felt(r) = (r / horizon(r))**2``.
   * ``horizon`` has three regimes: before the first lesson you imagine the subject
     small (``B0``); then every thing you learn lets you make out more that you have
     not learned, and the edge runs away from you (``r * (1 + C * r**Q)``); at last
     it reaches the true edge and stops (1).

   Nothing here is fitted to a study: the three numbers below were chosen so that
   the picture reads well, and the film says so on screen. Two things were kept
   in line with what Kruger and Dunning (1999) report, and are asserted below: the
   beginner's feeling is far above the facts, and yet the beginner never feels
   surer than the expert does. What the model is good for is consistency: the dots
   on the map, the gauges, the bars and the chart are all read from these
   functions. The pictures count dots (400 of them), the chart draws the formulas:
   from the first peak on they agree to within a few points (below it, where a
   handful of dots is lit, the count is coarser).

2. **A real chess game**: the four-move checkmate known as the scholar's mate.
   ``python model.py`` replays it with python-chess when that is installed.
"""

from __future__ import annotations

import numpy as np

# ---- the light and the field -------------------------------------------------------- #
B0 = 0.23  # before lesson one: how big you imagine the subject (share of its radius)
C, Q = 7.5, 3  # how fast what you can make out outruns what you know
N_DOTS = 400  # things there are to know
EXPERT = 0.93  # nobody lights the whole field
GOLDEN = np.pi * (3 - np.sqrt(5))


def horizon(r):
    """How far you can tell the field goes (share of its true radius)."""
    r = np.asarray(r, dtype=float)
    sight = r * (1 + C * r**Q)
    raw = (B0**8 + sight**8) ** (1 / 8)  # never smaller than what you imagined at first
    return (raw**-10.0 + 1.0) ** (-1 / 10)  # never beyond the true edge


def real(r):
    """The share of the field you really know."""
    return np.asarray(r, dtype=float) ** 2


def felt(r):
    """The share of the field you feel you know."""
    r = np.asarray(r, dtype=float)
    return (r / horizon(r)) ** 2


def scatter(n=N_DOTS, seed=7):
    """``n`` dots spread evenly over the unit disc (a sunflower with shaken angles), so
    that the number of dots within radius ``r`` is ``n * r**2`` to within a few
    dots. Returns ``(radius, angle)``; the very centre is left free for the one who
    holds the light, and no dot sits beyond 0.992."""
    rng = np.random.default_rng(seed)
    i = np.arange(n)
    rad = np.sqrt((i + 2.5) / (n + 2.5)) + rng.normal(0, 0.003, n)
    ang = i * GOLDEN + rng.normal(0, 0.22, n) + rng.uniform(0, 2 * np.pi)
    return np.clip(rad, 0.06, 0.992), ang


_r = np.linspace(0.001, 1.0, 4000)
_f = felt(_r)
_ip = int(np.argmax(_f[:1600]))
_iv = _ip + int(np.argmin(_f[_ip:]))
R_PEAK, R_VALLEY = float(_r[_ip]), float(_r[_iv])
FIRST = R_PEAK  # the light after a few lessons (scene 2): the first peak of the feeling
# Where the film stops at the bottom: the first light from which every dot of the
# field is in sight (no dot sits beyond 0.992). The feeling has just stopped falling.
R_SEEN = float(_r[int(np.argmax(horizon(_r) > 0.9925))])

# The shape the film talks about, asserted.
# A first peak very early: you feel you know most of it, and know a twentieth.
assert 0.2 < R_PEAK < 0.3 and 0.7 < felt(R_PEAK) < 0.82 and real(R_PEAK) < 0.08
# ... and yet the beginner never feels surer than the expert (as in the 1999 data).
assert felt(R_PEAK) < felt(EXPERT) - 0.05
# A deep valley in the middle, where the feeling meets the facts ...
assert 0.45 < R_VALLEY < 0.60 and felt(R_VALLEY) < 0.32
assert abs(felt(R_VALLEY) - real(R_VALLEY)) < 0.05
assert R_VALLEY < R_SEEN < 0.6 and felt(R_SEEN) - felt(R_VALLEY) < 0.04
assert abs(felt(R_SEEN) - real(R_SEEN)) < 0.01
assert np.all(scatter()[0] < horizon(R_SEEN))  # ... and the whole field is in sight
# ... and from there they climb together.
assert np.all(_f[_r > 0.7] - real(_r[_r > 0.7]) < 0.01)
assert np.all(np.diff(_f[_r > R_SEEN]) > 0)
assert np.all(_f >= real(_r) - 1e-9)  # in this toy you never feel you know less than you do

# ---- the chess game ------------------------------------------------------------------- #
FILES = "abcdefgh"
START = {
    **{f"{f}2": "wP" for f in FILES},
    **{f"{f}7": "bP" for f in FILES},
    **{f"{f}1": "w" + p for f, p in zip(FILES, "RNBQKBNR", strict=True)},
    **{f"{f}8": "b" + p for f, p in zip(FILES, "RNBQKBNR", strict=True)},
}
# (from, to, how it is written down)
OPENING = [
    ("e2", "e4", "e4"),
    ("e7", "e5", "e5"),
    ("d1", "h5", "Qh5"),
    ("b8", "c6", "Nc6"),
    ("f1", "c4", "Bc4"),
]
BLUNDER = ("g8", "f6", "Nf6")  # "it attacks the queen!"
MATE = ("h5", "f7", "Qxf7#")  # the queen takes, guarded by the bishop on c4


def replay():
    """The position after each move, as ``{square: piece}``; checks the bookkeeping."""
    pos = dict(START)
    for a, b, _ in [*OPENING, BLUNDER, MATE]:
        assert a in pos, a
        pos[b] = pos.pop(a)
    return pos


_end = replay()
assert _end["f7"] == "wQ" and _end["f6"] == "bN" and _end["c4"] == "wB" and _end["e8"] == "bK"


if __name__ == "__main__":
    for name, r in (("first peak", R_PEAK), ("valley", R_VALLEY), ("field in sight", R_SEEN), ("expert", EXPERT)):
        print(f"{name:15s}: light {r:.3f}  feels {felt(r):.0%}  really {real(r):.1%}")
    rad, _ = scatter()
    for r in (FIRST, R_SEEN, EXPERT):
        lit, seen = int((rad < r).sum()), int((rad < horizon(r)).sum())
        print(f"light {r:.3f}: {lit} lit, {seen} in sight, {N_DOTS} in all  ({lit / seen:.0%} of what is in sight)")
    try:
        import chess
    except ImportError:
        print("python-chess is not installed: the game was not replayed (pip install chess)")
    else:
        board = chess.Board()
        for _, _, san in [*OPENING, BLUNDER]:
            board.push_san(san)
        assert chess.H5 in board.attacks(chess.F6)  # the knight does attack the queen
        board.push_san(MATE[2])
        assert board.is_checkmate()
        print("scholar's mate replayed with python-chess: checkmate on move 4")
