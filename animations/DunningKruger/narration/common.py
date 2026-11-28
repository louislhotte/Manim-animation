"""common.py: what the steps of the voice-over share (numpy only).

A take is one line of the film, said in one go, with the model's timing of each
word. Two things are read from it here, by the step that tells the film how the
voice runs (speak.py) and by the step that lays the voice under the film (place.py),
so that both see the same voice: where the take is silent enough to be cut, and
how long its pauses are once the shortest ones are given a narrator's length.
"""

from __future__ import annotations

import wave

import numpy as np

RATE = 24000  # the voice's sample rate
QUIET = 0.004  # of full scale: below this, nobody is speaking
MIN_QUIET = 0.06  # a take is only cut inside at least this much silence
LEAD_IN = 0.25  # a line starts this long after its caption begins to appear
# The voice's own full stop lasts 0.3 to 0.65 s, and "What a move! You are" has none.
MIN_PAUSE = {".": 0.6, "!": 0.6, "?": 0.6, ":": 0.5}


def load(path, rate=RATE):
    with wave.open(str(path)) as f:
        assert f.getframerate() == rate and f.getnchannels() == 1 and f.getsampwidth() == 2
        return np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float32) / 32768


def save(path, pcm, rate=RATE):
    with wave.open(str(path), "wb") as f:
        f.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        f.writeframes(np.round(np.clip(pcm, -1, 1) * 32767).astype("<i2").tobytes())


def quiet_cut(pcm, rate, word, mark, until):
    """The silence a punctuation mark makes: its middle and its length, or ``None``
    when the voice never really stops there.

    The model gives the mark a time span of its own (``mark``), but the silence
    begins earlier, inside the time it gives the word before (a last syllable dies
    away long before its slot is over). So the whole stretch from that word to the
    next (``word`` to ``until``) is searched, and only a silence that reaches the
    mark's own span counts: the closure of a "t" inside the word is not a pause."""
    hop = rate // 200  # 5 ms
    lo = int(max(word, mark[0] - 0.6) * rate)
    hi = min(len(pcm), int(until * rate))
    env = np.array([np.abs(pcm[i : i + hop]).max() for i in range(lo, hi - hop, hop)])
    best, start = (0.0, 0.0), None
    for i, silent in enumerate([*(env < QUIET), False]):
        if silent and start is None:
            start = i
        elif not silent and start is not None:
            a, b = (lo + start * hop) / rate, (lo + i * hop) / rate
            if min(b, mark[1]) - max(a, mark[0]) > 0.02:
                best = max(best, (b - a, a))
            start = None
    if best[0] < MIN_QUIET:
        return None
    return best[1] + best[0] / 2, best[0]


def cuts_of(words, pcm, rate=RATE):
    """Where a take may be cut: ``(time in the take, index of the first word after,
    the punctuation mark, how long the silence is)`` for each pause that is one."""
    out = []
    for k, w in enumerate(words[:-1]):
        if w["pause"]:
            found = quiet_cut(pcm, rate, w["start"], w["pause"], words[k + 1]["start"] + 0.05)
            if found:
                out.append((found[0], k + 1, w["text"][-1], found[1]))
    return out


def floors(cuts):
    """What each pause must grow by to be as long as a narrator's (``MIN_PAUSE``)."""
    return [max(0.0, MIN_PAUSE.get(mark, 0.0) - silence) for _, _, mark, silence in cuts]


def flow(take, pcm, rate=RATE):
    """The take as it runs when nothing holds it back: when each word starts, counted
    from the first one, and when the last sound has died away."""
    words = take["words"]
    cuts, grown = cuts_of(words, pcm, rate), 0.0
    later = np.zeros(len(words))
    for (_, first, _, _), more in zip(cuts, floors(cuts), strict=True):
        later[first:] += more
        grown += more
    t0 = words[0]["start"]
    starts = [round(float(w["start"] - t0 + later[k]), 3) for k, w in enumerate(words)]
    return starts, round(float(take["speech"][1] - t0 + grown), 3)
