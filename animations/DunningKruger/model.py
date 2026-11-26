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
   the picture reads well, and the film says so on screen. What the model is good
   for is consistency: the dots on the map, the gauges and the chart are all read
   from these functions, so they agree.

2. **A real chess game**: the four-move checkmate known as the scholar's mate.
   ``python model.py`` replays it with python-chess when that is installed.
"""

from __future__ import annotations

import numpy as np

# ---- the light and the field -------------------------------------------------------- #
B0 = 0.15  # before lesson one: how big you imagine the subject (share of its radius)
C, Q = 7.5, 3  # how fast what you can make out outruns what you know
N_DOTS = 400  # things there are to know
FIRST = 0.20  # the light after a few lessons (scene 2)
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
    """``n`` dots spread evenly over the unit disc (a sunflower, shaken a little), so
    that the number of dots within radius ``r`` is close to ``n * r**2``. Returns
    ``(radius, angle)``; the very centre is left free for the one who holds the light."""
    rng = np.random.default_rng(seed)
    i = np.arange(n)
    rad = np.sqrt((i + 2.5) / (n + 2.5)) + rng.normal(0, 0.012, n)
    ang = i * GOLDEN + rng.normal(0, 0.22, n) + rng.uniform(0, 2 * np.pi)
    return np.clip(rad, 0.06, 0.992), ang


_r = np.linspace(0.001, 1.0, 2000)
_f = felt(_r)
_ip = int(np.argmax(_f[:800]))
_iv = _ip + int(np.argmin(_f[_ip:]))
R_PEAK, R_VALLEY = float(_r[_ip]), float(_r[_iv])

# The shape the film talks about, asserted: a high peak very early, a deep valley
# in the middle, and from there the feeling and the facts climb together.
assert 0.15 < R_PEAK < 0.22 and felt(R_PEAK) > 0.85 and real(R_PEAK) < 0.05
assert 0.45 < R_VALLEY < 0.60 and felt(R_VALLEY) < 0.32
assert abs(felt(R_VALLEY) - real(R_VALLEY)) < 0.05
assert np.all(_f[_r > 0.7] - real(_r[_r > 0.7]) < 0.01)
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
    print(f"peak   : light {R_PEAK:.3f}  feels {felt(R_PEAK):.0%}  really {real(R_PEAK):.1%}")
    print(f"valley : light {R_VALLEY:.3f}  feels {felt(R_VALLEY):.0%}  really {real(R_VALLEY):.0%}")
    rad, _ = scatter()
    for r in (FIRST, R_VALLEY, EXPERT):
        lit, seen = int((rad < r).sum()), int((rad < horizon(r)).sum())
        print(f"light {r:.2f}: {lit} lit, {seen} in sight, {N_DOTS} in all")
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
