"""cue_times.py: what the film says, and when each of its pictures lands.

The film waits for its narrator: ``cue("phrase")`` holds a picture back until a
word, ``span("phrase")`` stretches a motion until one. This script plays every
scene without writing a video (tiny frames at the film's own 60 frames a second, so
the clock is the film's) and writes down, for each narrated line, its words, when
it starts, and when each of its cues really lands (a cue can be late: the motion
before it may not be over). Two steps need that:

  * ``speak.py`` says the lines it finds here;
  * ``place.py`` puts every word a third of a second after its picture.

It does not touch the film: it wraps four methods of the scene class while it runs.

    ~/.cache/manimx/venv/bin/python narration/cue_times.py           # -> narration/cues.json
    ~/.cache/manimx/venv/bin/python narration/cue_times.py Expert    # one scene again

About a minute per scene. Run it again whenever the film's timing changes, which
includes after ``speak.py``: the film is cut to the voice (``voice.json``).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILM = HERE.parent
sys.path[:0] = [str(FILM), str(FILM.parents[1])]

from manim import tempconfig  # noqa: E402

import dunning_kruger as dk  # noqa: E402

SCENES = ("Intro", "Move", "Light", "Climb", "Expert", "Everyone", "Outro")
FPS = 60

lines: list[dict] = []  # of the scene being played


def _line(scene, vo, at=0.0):
    lines.append({"t0": round(scene.renderer.time + at, 4), "text": vo, "anchors": []})


def _anchor(scene, kind, phrase, lead, t):
    vo = scene._vo
    lines[-1]["anchors"].append(
        {
            "kind": kind,  # cue: the picture starts to change; span: a motion ends
            "phrase": phrase,
            "word": len(vo[: vo.index(phrase)].split()),  # index of its first word
            "t": round(t, 4),
            "lead": lead,  # the picture is meant to come this long before the word
        }
    )


_tell, _cue, _span, _over = dk._Common.tell, dk._Common.cue, dk._Common.span, dk._Common.over_card


def tell(self, caption, vo, **kw):
    _line(self, vo, kw.get("at", 0.0))
    return _tell(self, caption, vo, **kw)


def over_card(self, vo):
    self._vo = vo
    _line(self, vo)
    return _over(self, vo)


def cue(self, phrase, lead=0.3, ambient=None):
    _cue(self, phrase, lead=lead, ambient=ambient)
    _anchor(self, "cue", phrase, lead, self.renderer.time)


def span(self, phrase=None, floor=0.5, lead=0.3, cap=None):
    rt = _span(self, phrase, floor=floor, lead=lead, cap=cap)
    if phrase:
        _anchor(self, "span", phrase, lead, self.renderer.time + rt)
    return rt


def main():
    assert not dk._Common.pace.quick, "run at the real pace (unset DK_QUICK / MX_QUICK)"
    dk._Common.tell, dk._Common.cue, dk._Common.span, dk._Common.over_card = tell, cue, span, over_card
    todo = sys.argv[1:] or SCENES
    assert set(todo) <= set(SCENES), f"scenes are {SCENES}"
    path = HERE / "cues.json"
    old = {s["scene"]: s for s in json.loads(path.read_text())["scenes"]} if path.exists() else {}
    out = {"fps": FPS, "wps": dk._Common.WPS, "scenes": []}
    with tempfile.TemporaryDirectory() as tmp:
        for name in SCENES:
            if name not in todo:
                out["scenes"].append(old[name])
                continue
            lines.clear()
            with tempconfig(
                {
                    "pixel_width": 256,
                    "pixel_height": 144,
                    "frame_rate": FPS,
                    "dry_run": True,
                    "disable_caching": True,
                    "media_dir": tmp,
                    "verbosity": "ERROR",
                    "progress_bar": "none",
                }
            ):
                scene = getattr(dk, name)()
                scene.render()
                length = scene.renderer.time
            out["scenes"].append({"scene": name, "length": round(length, 4), "lines": [dict(ln) for ln in lines]})
            print(f"{name:9s} {length:7.2f} s  {len(lines)} lines, {sum(len(ln['anchors']) for ln in lines)} cues", flush=True)
    path.write_text(json.dumps(out, indent=1) + "\n")
    total = sum(s["length"] for s in out["scenes"])
    print(f"film {total:.2f} s -> {path}")


if __name__ == "__main__":
    main()
